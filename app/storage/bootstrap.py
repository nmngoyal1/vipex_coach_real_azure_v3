from __future__ import annotations
import json
from pathlib import Path
from app.storage.db import init_db, insert_rule

def bootstrap() -> None:
    init_db()
    rules_path = Path("data/market_rules.json")
    if rules_path.exists():
        for rule in json.loads(rules_path.read_text(encoding="utf-8")):
            insert_rule(rule)

if __name__ == "__main__":
    bootstrap()
    print("VIPEX local database initialised.")
