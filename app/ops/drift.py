from __future__ import annotations
from app.storage.db import feedback_stats, telemetry_summary
from app.tools.retrieval import rule_review_due

def drift_signals(market: str | None = None) -> dict:
    fb = feedback_stats(market=market, days=30)
    tel = telemetry_summary(days=30)
    due_rules = rule_review_due(market, 60) if market else []
    signals = []
    acc = fb.get("acceptance_rate")
    signals.append({
        "signal": "operator_acceptance_rate",
        "value": acc,
        "threshold": "alert if < 0.70 over rolling 30 days with >=20 feedback events",
        "alert": bool(acc is not None and fb.get("total", 0) >= 20 and acc < 0.70)
    })
    p95 = tel.get("p95_latency_ms")
    signals.append({
        "signal": "p95_workshop_latency_ms",
        "value": p95,
        "threshold": "alert if > 120000 ms",
        "alert": bool(p95 is not None and p95 > 120000)
    })
    signals.append({
        "signal": "market_rules_due_for_review",
        "value": len(due_rules),
        "threshold": "alert if any active rule expires within 60 days",
        "alert": len(due_rules) > 0,
        "rule_ids": [r.get("rule_id") for r in due_rules]
    })
    return {"market": market or "all", "signals": signals, "feedback": fb, "telemetry": tel}
