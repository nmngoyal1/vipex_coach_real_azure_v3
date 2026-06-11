from __future__ import annotations
from fastapi import FastAPI
from app.api.routes import router
from app.bot.routes import router as bot_router
from app.storage.bootstrap import bootstrap
from app.observability import configure_observability

configure_observability()
bootstrap()
app = FastAPI(title="VIPEX Coach Azure-Ready", version="1.0.0")
app.include_router(router)
app.include_router(bot_router)

@app.get("/health")
def health():
    return {"status":"ok", "service":"vipex-coach", "mode":"azure-ready"}
