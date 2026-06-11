from __future__ import annotations
import json
from app.storage.db import get_job, get_session, queue_stats, telemetry_summary

def triage_snapshot(job_id: str) -> dict:
    job = get_job(job_id)
    if not job:
        return {"status": "not_found", "first_hour": ["Confirm the user sent the correct job id or conversation id."]}
    session = get_session(job["conversation_id"])
    result = json.loads(job["result_json"]) if job.get("result_json") else None
    checks = [
        {"order": 1, "surface": "Teams/Bot", "check": "Bot acknowledged upload and stored conversation reference", "observed": bool(session and session.get("conversation_reference"))},
        {"order": 2, "surface": "Service Bus", "check": "Check active/locked/dead-letter queue depth", "observed": queue_stats()},
        {"order": 3, "surface": "ACA Worker", "check": "Check job status and attempts", "observed": {"status": job["status"], "attempts": job.get("attempts")}},
        {"order": 4, "surface": "AI Foundry", "check": "In production inspect run status running/failed/requires_action and token/rate-limit consumption", "observed": "local runtime"},
        {"order": 5, "surface": "Cosmos/session", "check": "Confirm session record, market, workshop, and last job", "observed": session},
        {"order": 6, "surface": "Result delivery", "check": "Confirm result JSON exists and proactive Teams post can use stored conversation reference", "observed": bool(result)},
    ]
    return {"job_id": job_id, "job_status": job["status"], "checks": checks, "telemetry_30d": telemetry_summary(30)}
