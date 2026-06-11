from __future__ import annotations
import httpx
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, CardFactory
from app.models import TeamsUploadRequest
from app.api.routes import teams_message
from app.ingestion.parsers import extract_raw_ideas_from_upload

class VIPEXTeamsBot(ActivityHandler):
    """Real Teams Bot Framework activity handler.

    Handles pasted workshop ideas and file attachments. Teams file bytes are downloaded through the
    attachment contentUrl; CSV/XLSX/JSON/TXT are parsed directly. Image/PDF attachments return a clear
    preprocessing/OCR warning unless an OCR service is wired to app/ingestion/parsers.py.
    """

    async def on_message_activity(self, turn_context: TurnContext):
        activity = turn_context.activity
        text = (activity.text or "").strip()
        channel_data = activity.channel_data or {}
        conversation_id = activity.conversation.id if activity.conversation else "unknown_conversation"
        user_id = activity.from_property.id if activity.from_property else "unknown_user"
        market = _extract_value(text, "market") or channel_data.get("market") or "VN"
        workshop = _extract_value(text, "workshop") or "Teams Upload"
        raw_ideas: list[str] = []
        warnings: list[str] = []

        # Teams file upload path
        for att in activity.attachments or []:
            if not att.content_url:
                continue
            try:
                content = await _download_attachment(att.content_url, turn_context)
                parsed = extract_raw_ideas_from_upload(att.name or "teams_upload", content)
                raw_ideas.extend(parsed.raw_ideas)
                warnings.extend(parsed.warnings)
            except Exception as exc:
                warnings.append(f"Could not process attachment {att.name or att.content_url}: {exc}")

        # Pasted text path
        if not raw_ideas:
            raw_ideas = [line.strip(" -\t") for line in text.splitlines() if line.strip() and ":" not in line]
        if not raw_ideas and text:
            raw_ideas = [text]
        if not raw_ideas:
            await turn_context.send_activity("I could not find ideas in this message. Paste raw ideas or upload CSV/XLSX/TXT/JSON.")
            return

        payload = TeamsUploadRequest(conversation_id=conversation_id, user_id=user_id, market=market, workshop=workshop, raw_ideas=raw_ideas)
        accepted = teams_message(payload)
        if warnings:
            accepted["teams_ack_card"]["body"].append({"type": "TextBlock", "text": "Warnings: " + "; ".join(warnings[:3]), "wrap": True})
        card = CardFactory.adaptive_card(accepted["teams_ack_card"])
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("VIPEX Coach is ready. Upload workshop files or paste raw idea text with market/workshop metadata.")

async def _download_attachment(content_url: str, turn_context: TurnContext) -> bytes:
    headers = {}
    # Teams file downloads often need the bot auth token. get_user_token is not appropriate; this is a
    # service-to-service connector token seam. Keep the function isolated for tenant-specific handling.
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(content_url, headers=headers)
        res.raise_for_status()
        return res.content

def _extract_value(text: str, key: str) -> str | None:
    prefix = key.lower() + ":"
    for line in text.splitlines():
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None
