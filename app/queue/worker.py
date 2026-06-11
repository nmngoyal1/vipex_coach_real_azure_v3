from __future__ import annotations
import json
from pathlib import Path
from app.models import JobEnvelope
from app.agent.runtime import VIPEXAgentRuntime
from app.queue.local_queue import LocalServiceBusQueue
from app.settings import get_settings
from app.azure.servicebus_adapter import AzureServiceBusQueue
from app.storage.db import update_job, increment_job_attempt
from app.bot.proactive import send_proactive_update
from app.cards.adaptive_cards import progress_card, result_card

ARTIFACT_DIR = Path("outputs")
ARTIFACT_DIR.mkdir(exist_ok=True)

class VIPEXWorker:
    """ACA Worker simulator. In Azure this would run as a Container Apps worker/job."""
    def __init__(self) -> None:
        self.settings = get_settings()
        self.queue = AzureServiceBusQueue() if self.settings.is_azure else LocalServiceBusQueue()
        self.runtime = VIPEXAgentRuntime()

    def process_one(self) -> dict:
        msg = self.queue.receive_one()
        if not msg:
            return {"status": "empty"}
        message_id = msg["message_id"]
        payload = msg["payload"]
        try:
            job = JobEnvelope(**payload)
            update_job(job.job_id, "running")
            increment_job_attempt(job.job_id)
            send_proactive_update(job.conversation_reference, f"VIPEX Coach is processing job {job.job_id}.", progress_card(job.job_id, "running", {}))
            result = self.runtime.process(job).model_dump()
            out = ARTIFACT_DIR / f"{job.job_id}_result.json"
            out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            update_job(job.job_id, "completed", result=result)
            send_proactive_update(job.conversation_reference, f"VIPEX Coach completed job {job.job_id} with {result.get('ideas_processed')} processed ideas.", result_card(result))
            if self.settings.is_azure:
                self.queue.complete_received(msg)
            else:
                self.queue.complete(message_id)
            return {"status": "completed", "job_id": job.job_id, "output": str(out)}
        except Exception as exc:
            if self.settings.is_azure:
                self.queue.dead_letter_received(msg, str(exc))
            else:
                self.queue.fail(message_id, str(exc))
            if "job" in locals():
                update_job(job.job_id, "failed", error=str(exc))
                send_proactive_update(job.conversation_reference, f"VIPEX Coach failed job {job.job_id}: {str(exc)[:250]}", progress_card(job.job_id, "failed", {"error": str(exc)[:250]}))
                return {"status": "failed", "job_id": job.job_id, "error": str(exc)}
            return {"status": "failed", "error": str(exc)}

    def drain(self, max_messages: int = 100) -> list[dict]:
        out = []
        for _ in range(max_messages):
            res = self.process_one()
            out.append(res)
            if res["status"] == "empty":
                break
        return out
