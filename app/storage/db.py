from __future__ import annotations
import json, sqlite3, time, uuid
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("data/vipex.db")

def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS sessions(
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT,
            market TEXT,
            brand TEXT,
            workshop TEXT,
            last_job_id TEXT,
            status TEXT,
            conversation_reference TEXT,
            created_at REAL,
            updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS jobs(
            job_id TEXT PRIMARY KEY,
            conversation_id TEXT,
            status TEXT,
            request_json TEXT,
            result_json TEXT,
            error TEXT,
            attempts INTEGER DEFAULT 0,
            created_at REAL,
            updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS queue_messages(
            message_id TEXT PRIMARY KEY,
            job_id TEXT,
            queue_name TEXT,
            status TEXT,
            payload_json TEXT,
            attempts INTEGER DEFAULT 0,
            visible_at REAL,
            created_at REAL,
            updated_at REAL,
            last_error TEXT
        );
        CREATE TABLE IF NOT EXISTS market_rules(
            rule_id TEXT PRIMARY KEY,
            market TEXT,
            category TEXT,
            constraint_text TEXT,
            rationale TEXT,
            captured_by TEXT,
            captured_at TEXT,
            valid_from TEXT,
            valid_to TEXT,
            source_conversation_id TEXT,
            hardness TEXT,
            status TEXT,
            rule_json TEXT
        );
        CREATE TABLE IF NOT EXISTS feedback(
            feedback_id TEXT PRIMARY KEY,
            idea_id TEXT,
            conversation_id TEXT,
            market TEXT,
            signal TEXT,
            reason TEXT,
            corrected_text TEXT,
            corrected_feasibility INTEGER,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS telemetry_events(
            event_id TEXT PRIMARY KEY,
            job_id TEXT,
            conversation_id TEXT,
            market TEXT,
            stage TEXT,
            metric_name TEXT,
            metric_value REAL,
            dimensions_json TEXT,
            created_at REAL
        );
        ''')

def upsert_session(conversation_id: str, user_id: str, market: str, brand: Optional[str], workshop: str, job_id: str, conversation_reference: Optional[dict[str, Any]] = None) -> None:
    now = time.time()
    ref = conversation_reference or {"conversation_id": conversation_id, "channel": "local-teams-simulator"}
    with connect() as conn:
        conn.execute('''INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(conversation_id) DO UPDATE SET last_job_id=excluded.last_job_id,status=excluded.status,updated_at=excluded.updated_at,conversation_reference=excluded.conversation_reference''',
        (conversation_id,user_id,market,brand,workshop,job_id,"queued",json.dumps(ref),now,now))

def get_session(conversation_id: str) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE conversation_id=?", (conversation_id,)).fetchone()
    return dict(row) if row else None

def create_job(job_id: str, conversation_id: str, request: dict[str, Any]) -> None:
    now = time.time()
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO jobs(job_id,conversation_id,status,request_json,result_json,error,attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (job_id, conversation_id, "queued", json.dumps(request), None, None, 0, now, now))

def update_job(job_id: str, status: str, result: Optional[dict[str, Any]] = None, error: Optional[str] = None) -> None:
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=?, result_json=COALESCE(?, result_json), error=?, updated_at=? WHERE job_id=?", (status, json.dumps(result) if result else None, error, time.time(), job_id))

def increment_job_attempt(job_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE jobs SET attempts=COALESCE(attempts,0)+1, updated_at=? WHERE job_id=?", (time.time(), job_id))

def get_job(job_id: str) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    return dict(row) if row else None

def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

def enqueue_message(job_id: str, payload: dict[str, Any], queue_name: str = "vipex-jobs") -> str:
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    now = time.time()
    with connect() as conn:
        conn.execute("INSERT INTO queue_messages VALUES(?,?,?,?,?,?,?,?,?,?)", (msg_id, job_id, queue_name, "active", json.dumps(payload), 0, now, now, now, None))
    return msg_id

def dequeue_message(queue_name: str = "vipex-jobs") -> Optional[dict[str, Any]]:
    now = time.time()
    with connect() as conn:
        row = conn.execute("SELECT * FROM queue_messages WHERE queue_name=? AND status='active' AND visible_at<=? ORDER BY created_at LIMIT 1", (queue_name, now)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE queue_messages SET status='locked', attempts=attempts+1, updated_at=? WHERE message_id=?", (now, row["message_id"]))
    msg = dict(row)
    msg["payload"] = json.loads(msg["payload_json"])
    return msg

def complete_message(message_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE queue_messages SET status='completed', updated_at=? WHERE message_id=?", (time.time(), message_id))

def abandon_or_deadletter(message_id: str, error: str, max_attempts: int = 3) -> None:
    now = time.time()
    with connect() as conn:
        row = conn.execute("SELECT attempts FROM queue_messages WHERE message_id=?", (message_id,)).fetchone()
        status = "dead_letter" if row and row["attempts"] >= max_attempts else "active"
        visible_at = now + 5
        conn.execute("UPDATE queue_messages SET status=?, visible_at=?, updated_at=?, last_error=? WHERE message_id=?", (status, visible_at, now, error, message_id))

def queue_stats() -> dict[str, int]:
    with connect() as conn:
        rows = conn.execute("SELECT status, COUNT(*) c FROM queue_messages GROUP BY status").fetchall()
    out = {r["status"]: r["c"] for r in rows}
    return {"active": out.get("active", 0), "locked": out.get("locked", 0), "completed": out.get("completed", 0), "dead_letter": out.get("dead_letter", 0)}

def insert_rule(rule: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute('''INSERT OR REPLACE INTO market_rules VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            rule["rule_id"], rule["market"], rule["category"], rule["constraint"], rule.get("rationale",""),
            rule.get("captured_by","unknown"), rule.get("captured_at"), rule.get("valid_from"), rule.get("valid_to"),
            rule.get("source_conversation_id"), rule.get("hardness", "unknown"), rule.get("status","active"), json.dumps(rule)
        ))

def list_rules(market: str, include_expired: bool = False) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT rule_json FROM market_rules WHERE market=? AND status='active'", (market,)).fetchall()
    rules = [json.loads(r["rule_json"]) for r in rows]
    if include_expired:
        return rules
    today = time.strftime("%Y-%m-%d")
    return [r for r in rules if not r.get("valid_to") or r["valid_to"] >= today]

def insert_feedback(feedback: dict[str, Any]) -> str:
    fid = feedback.get("feedback_id") or f"fb_{uuid.uuid4().hex[:12]}"
    with connect() as conn:
        conn.execute("INSERT INTO feedback VALUES(?,?,?,?,?,?,?,?,?)", (
            fid, feedback["idea_id"], feedback["conversation_id"], feedback["market"], feedback["signal"],
            feedback.get("reason"), feedback.get("corrected_text"), feedback.get("corrected_feasibility"), time.time()
        ))
    return fid

def feedback_stats(market: Optional[str] = None, days: int = 30) -> dict[str, Any]:
    since = time.time() - days*86400
    where = "created_at>=?"
    params: list[Any] = [since]
    if market:
        where += " AND market=?"; params.append(market)
    with connect() as conn:
        rows = conn.execute(f"SELECT signal, COUNT(*) c FROM feedback WHERE {where} GROUP BY signal", params).fetchall()
    counts = {r["signal"]: r["c"] for r in rows}
    total = sum(counts.values())
    return {"total": total, "counts": counts, "acceptance_rate": round(counts.get("accept", 0)/total, 4) if total else None}

def log_metric(job_id: str, conversation_id: str, market: str, stage: str, metric_name: str, metric_value: float, dimensions: Optional[dict[str, Any]] = None) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO telemetry_events VALUES(?,?,?,?,?,?,?,?,?)", (f"evt_{uuid.uuid4().hex[:12]}", job_id, conversation_id, market, stage, metric_name, metric_value, json.dumps(dimensions or {}), time.time()))

def telemetry_summary(days: int = 30) -> dict[str, Any]:
    since = time.time() - days*86400
    with connect() as conn:
        jobs = conn.execute("SELECT status, result_json, created_at FROM jobs WHERE created_at>=?", (since,)).fetchall()
    latencies = []
    costs = []
    completed = 0
    failed = 0
    for j in jobs:
        if j["status"] == "completed" and j["result_json"]:
            completed += 1
            try:
                res = json.loads(j["result_json"])
                latencies.append(float(res.get("telemetry", {}).get("latency_ms", 0)))
                costs.append(float(res.get("telemetry", {}).get("estimated_cost_dkk", 0)))
            except Exception:
                pass
        elif j["status"] == "failed":
            failed += 1
    def pct(vals, p):
        if not vals: return None
        vals = sorted(vals); idx = min(len(vals)-1, int(round((p/100)*(len(vals)-1))))
        return vals[idx]
    return {"jobs": len(jobs), "completed": completed, "failed": failed, "p50_latency_ms": pct(latencies, 50), "p95_latency_ms": pct(latencies, 95), "p99_cost_dkk": pct(costs, 99)}
