from __future__ import annotations
from fastapi import APIRouter, Request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity
from app.settings import get_settings
from app.bot.teams_activity_handler import VIPEXTeamsBot

router = APIRouter()
settings = get_settings()
bot = VIPEXTeamsBot()
adapter = BotFrameworkAdapter(BotFrameworkAdapterSettings(settings.bot_app_id or "", settings.bot_app_password or ""))

@router.post("/api/messages")
async def messages(req: Request):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    async def call_bot(turn_context: TurnContext):
        await bot.on_turn(turn_context)
    await adapter.process_activity(activity, auth_header, call_bot)
    return Response(status_code=201)
