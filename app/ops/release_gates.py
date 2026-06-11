from __future__ import annotations
from app.models import ReleaseGateResult
from app.storage.db import feedback_stats, telemetry_summary, queue_stats

def evaluate_release_gates(market: str = "VN") -> dict:
    fb = feedback_stats(market=market, days=30)
    tel = telemetry_summary(days=30)
    qs = queue_stats()
    gates = [
        ReleaseGateResult(gate="pilot_acceptance_rate", value=fb.get("acceptance_rate") if fb.get("acceptance_rate") is not None else "insufficient_feedback", threshold=">= 0.70 with >=20 feedback events", passed=bool(fb.get("total", 0) >= 20 and (fb.get("acceptance_rate") or 0) >= 0.70), evidence="Teams feedback table"),
        ReleaseGateResult(gate="p95_processing_latency_ms", value=tel.get("p95_latency_ms") or "no_completed_jobs", threshold="<= 120000", passed=bool(tel.get("p95_latency_ms") is not None and tel["p95_latency_ms"] <= 120000), evidence="Job telemetry"),
        ReleaseGateResult(gate="p99_cost_per_workshop_dkk", value=tel.get("p99_cost_dkk") or "no_completed_jobs", threshold="<= 14 DKK local target derived from 50k DKK / 10 users / year budget", passed=bool(tel.get("p99_cost_dkk") is not None and tel["p99_cost_dkk"] <= 14), evidence="Cost telemetry"),
        ReleaseGateResult(gate="dead_letter_depth", value=qs.get("dead_letter", 0), threshold="0 before launch cutover", passed=qs.get("dead_letter", 0) == 0, evidence="Queue stats"),
        ReleaseGateResult(gate="completed_job_volume", value=tel.get("completed", 0), threshold=">= 5 pilot dry-run files", passed=tel.get("completed", 0) >= 5, evidence="Job table"),
    ]
    return {"market": market, "gates": [g.model_dump() for g in gates], "ready": all(g.passed for g in gates)}
