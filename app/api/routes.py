from __future__ import annotations
import json, uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models import TeamsUploadRequest, JobEnvelope, FeedbackRequest, MarketRuleRequest
from app.storage.db import create_job, get_job, list_jobs, upsert_session, insert_feedback, insert_rule, feedback_stats, get_session, queue_stats
from app.queue.local_queue import LocalServiceBusQueue
from app.settings import get_settings
from app.azure.servicebus_adapter import AzureServiceBusQueue
from app.queue.worker import VIPEXWorker
from app.cards.adaptive_cards import processing_card, progress_card, result_card, feedback_card
from app.ops.drift import drift_signals
from app.ops.release_gates import evaluate_release_gates
from app.ops.triage import triage_snapshot
from app.ingestion.parsers import extract_raw_ideas_from_upload

router = APIRouter()
settings = get_settings()
queue = AzureServiceBusQueue() if settings.is_azure else LocalServiceBusQueue()

@router.post("/teams/upload")
@router.post("/teams/message")
def teams_message(payload: TeamsUploadRequest):
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job_payload = payload.model_dump(exclude={"ideas"})
    job = JobEnvelope(job_id=job_id, **job_payload, conversation_reference={"conversation_id": payload.conversation_id, "service_url": "local"})
    upsert_session(payload.conversation_id, payload.user_id, payload.market, payload.brand, payload.workshop, job_id, job.conversation_reference)
    create_job(job_id, payload.conversation_id, job.model_dump())
    message_id = queue.send(job_id, job.model_dump())
    return {"status": "accepted", "job_id": job_id, "message_id": message_id, "teams_ack_card": processing_card(job_id, len(payload.raw_ideas))}

@router.post("/teams/upload_file")
@router.post("/teams/upload_csv")
async def teams_upload_file(file: UploadFile = File(...), conversation_id: str = Form(...), user_id: str = Form(...), market: str = Form(...), workshop: str = Form(...), brand: str | None = Form(None)):
    content = await file.read()
    try:
        parsed = extract_raw_ideas_from_upload(file.filename or "upload", content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not parsed.raw_ideas:
        return {"status": "needs_preprocessing", "parser": parsed.parser, "warnings": parsed.warnings, "metadata": parsed.metadata}
    payload = TeamsUploadRequest(conversation_id=conversation_id, user_id=user_id, market=market, workshop=workshop, brand=brand, raw_ideas=parsed.raw_ideas)
    ack = teams_message(payload)
    ack["ingestion"] = {"parser": parsed.parser, "warnings": parsed.warnings, "metadata": parsed.metadata}
    return ack

@router.post("/worker/process-one")
def process_one_message():
    return VIPEXWorker().process_one()

@router.post("/worker/drain")
def drain_worker(max_messages: int = 100):
    return VIPEXWorker().drain(max_messages=max_messages)

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"status": "not_found"}
    result = json.loads(job["result_json"]) if job.get("result_json") else None
    return {"job_id": job_id, "status": job["status"], "attempts": job.get("attempts"), "error": job.get("error"), "result": result, "teams_progress_card": progress_card(job_id, job["status"], queue_stats()), "teams_result_card": result_card(result) if result else None}

@router.get("/sessions/{conversation_id}")
def session(conversation_id: str):
    return get_session(conversation_id) or {"status": "not_found"}

@router.get("/jobs")
def recent_jobs(limit: int = 20):
    return list_jobs(limit)

@router.post("/feedback")
def feedback(payload: FeedbackRequest):
    fid = insert_feedback(payload.model_dump())
    return {"status": "stored", "feedback_id": fid, "effect": "available for feasibility calibration, rejection-aware generation, and golden-set review"}

@router.get("/feedback/card/{idea_id}")
def get_feedback_card(idea_id: str, title: str = "VIPEX idea feedback"):
    return feedback_card(idea_id, title)

@router.get("/feedback/stats")
def get_feedback_stats(market: str | None = None, days: int = 30):
    return feedback_stats(market, days)

@router.post("/rules")
def capture_rule(payload: MarketRuleRequest):
    rule = payload.model_dump()
    rule["rule_id"] = f"R_{uuid.uuid4().hex[:8].upper()}"
    rule["captured_at"] = rule["valid_from"]
    rule["status"] = "active"
    insert_rule(rule)
    return {"status": "stored", "rule": rule}

@router.get("/ops/queue")
def ops_queue():
    return queue_stats()

@router.get("/ops/triage/{job_id}")
def ops_triage(job_id: str):
    return triage_snapshot(job_id)

@router.get("/ops/drift")
def ops_drift(market: str | None = None):
    return drift_signals(market)

@router.get("/ops/release-gates")
def ops_release_gates(market: str = "VN"):
    return evaluate_release_gates(market)
