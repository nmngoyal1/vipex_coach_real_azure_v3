from __future__ import annotations
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
import json
from app.storage.bootstrap import bootstrap
from app.ops.release_gates import evaluate_release_gates
bootstrap()
print(json.dumps(evaluate_release_gates("VN"), indent=2, ensure_ascii=False))
