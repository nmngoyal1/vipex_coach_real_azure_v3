from __future__ import annotations
import logging
from typing import Any
from app.settings import get_settings

logger = logging.getLogger(__name__)

def send_proactive_update(conversation_reference: dict[str, Any] | None, text: str, card: dict[str, Any] | None = None) -> dict[str, Any]:
    """Production seam for proactive Teams replies.

    The async architecture in the case study requires the worker to post final results back into the same Teams thread.
    Real tenant code uses Bot Framework `continue_conversation` with the stored ConversationReference.
    This function is intentionally safe in local mode and records exactly what would be sent.
    """
    s = get_settings()
    if not conversation_reference:
        return {"sent": False, "reason": "missing_conversation_reference"}
    if not s.is_azure:
        logger.info("LOCAL proactive Teams update: %s", text)
        return {"sent": False, "mode": "LOCAL", "would_send": {"text": text, "card": card, "conversation_reference": conversation_reference}}
    try:
        # Bot Framework proactive messaging is tenant-specific because trust_service_url and adapter auth
        # differ by deployment. We keep this as a concrete integration seam instead of pretending a fake send succeeded.
        from botbuilder.schema import ConversationReference  # noqa: F401
        return {"sent": False, "mode": "AZURE", "reason": "wire BotFrameworkAdapter.continue_conversation with stored ConversationReference in tenant", "would_send": {"text": text, "card": card}}
    except Exception as exc:
        return {"sent": False, "mode": "AZURE", "error": str(exc)}
