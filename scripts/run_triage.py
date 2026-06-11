from __future__ import annotations
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
import sys, json
from app.storage.bootstrap import bootstrap
from app.ops.triage import triage_snapshot
bootstrap()
job_id = sys.argv[1] if len(sys.argv) > 1 else "demo_job"
print(json.dumps(triage_snapshot(job_id), indent=2, ensure_ascii=False))
