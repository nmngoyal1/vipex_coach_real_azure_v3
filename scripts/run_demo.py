from __future__ import annotations
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
import json
from app.models import TeamsUploadRequest
from app.storage.bootstrap import bootstrap
from app.api.routes import teams_message
from app.queue.worker import VIPEXWorker

bootstrap()
payload = TeamsUploadRequest(
    conversation_id="thread_demo",
    user_id="SME_VN_03",
    market="VN",
    workshop="Walk-the-Floor 2026-W22",
    raw_ideas=[
        "Giảm độ dày lon 330ml xuống 0.235mm",
        "giam can gauge 330ml",
        "Bỏ in nhãn màu vàng trên thùng carton 24 lon",
        "Đổi nắp khoén 26mm sang 24mm",
    ],
)
accepted = teams_message(payload)
print("ACK:")
print(json.dumps(accepted, indent=2, ensure_ascii=False))
print("\nWORKER:")
print(json.dumps(VIPEXWorker().process_one(), indent=2, ensure_ascii=False))
