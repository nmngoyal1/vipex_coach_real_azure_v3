from __future__ import annotations

def processing_card(job_id: str, idea_count: int) -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": "VIPEX Coach is processing your workshop file", "weight": "Bolder", "size": "Medium"},
            {"type": "TextBlock", "text": f"Job {job_id} accepted. {idea_count} raw ideas queued.", "wrap": True},
            {"type": "TextBlock", "text": "Expected processing: minutes for 200–500 ideas. You can continue working; the result will return in this thread.", "wrap": True}
        ],
        "actions": [{"type": "Action.OpenUrl", "title": "Check status", "url": f"/jobs/{job_id}"}]
    }

def progress_card(job_id: str, status: str, queue_stats: dict | None = None) -> dict:
    stats = queue_stats or {}
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": f"VIPEX job status: {status}", "weight": "Bolder"},
            {"type": "FactSet", "facts": [
                {"title": "Job", "value": job_id},
                {"title": "Active queue", "value": str(stats.get("active", "n/a"))},
                {"title": "DLQ", "value": str(stats.get("dead_letter", "n/a"))}
            ]}
        ]
    }

def result_card(result: dict | None) -> dict | None:
    if not result:
        return None
    facts = [
        {"title": "Ideas processed", "value": str(result.get("ideas_processed"))},
        {"title": "Duplicates removed", "value": str(result.get("duplicates_removed"))},
        {"title": "Latency", "value": f"{result.get('telemetry', {}).get('latency_ms')} ms"},
        {"title": "Estimated cost", "value": f"{result.get('telemetry', {}).get('estimated_cost_dkk')} DKK"},
    ]
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": "VIPEX Coach results are ready", "weight": "Bolder", "size": "Medium"},
            {"type": "FactSet", "facts": facts},
            {"type": "TextBlock", "text": "Review each idea below and give fast feedback to improve future scoring.", "wrap": True}
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Accept shortlist", "data": {"action": "feedback", "signal": "accept"}},
            {"type": "Action.Submit", "title": "Needs SME review", "data": {"action": "feedback", "signal": "needs_sme_review"}}
        ]
    }

def feedback_card(idea_id: str, title: str) -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": title, "weight": "Bolder", "wrap": True},
            {"type": "TextBlock", "text": "Quick feedback helps calibrate feasibility and avoid repeated bad ideas.", "wrap": True},
            {"type": "Input.Text", "id": "reason", "placeholder": "Optional: reason or correction"}
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Accept", "data": {"idea_id": idea_id, "signal": "accept"}},
            {"type": "Action.Submit", "title": "Reject", "data": {"idea_id": idea_id, "signal": "reject"}},
            {"type": "Action.Submit", "title": "Edit", "data": {"idea_id": idea_id, "signal": "edit"}}
        ]
    }
