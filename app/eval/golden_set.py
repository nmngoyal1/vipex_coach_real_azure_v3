from __future__ import annotations
from app.agent.runtime import VIPEXAgentRuntime
from app.models import JobEnvelope
from app.storage.bootstrap import bootstrap

GOLDEN_ROWS = [
    {"raw":"Giảm độ dày lon 330ml xuống 0.235mm","cleaned":"Reduce 330ml can gauge to 0.235mm","market":"VN","score_min":65,"score_max":85,"rule_hits":[]},
    {"raw":"giam can gauge 330ml","cleaned":"Reduce 330ml can gauge","market":"VN","score_min":65,"score_max":85,"rule_hits":[]},
    {"raw":"Bỏ in nhãn màu vàng trên thùng carton 24 lon","cleaned":"Remove yellow label printing on 24-can carton","market":"VN","score_min":60,"score_max":85,"rule_hits":[]},
    {"raw":"Switch shrink film from PE to bio-PE on 500ml HDPE","cleaned":"Switch shrink film from PE to bio-PE on 500ml HDPE","market":"VN","score_min":55,"score_max":75,"rule_hits":[]},
    {"raw":"Đổi nắp khoén 26mm sang 24mm","cleaned":"Change 26mm pull-tab cap to 24mm","market":"VN","score_min":45,"score_max":65,"rule_hits":[]},
    {"raw":"330 毫升铝罐颈部规格统一为 202 直径","cleaned":"Standardise 330ml aluminium can neck finish to 202 diameter","market":"CN","score_min":55,"score_max":85,"rule_hits":[]},
    {"raw":"330ml 罐 颈口标准化 202","cleaned":"Standardise 330ml can neck finish to 202 diameter","market":"CN","score_min":55,"score_max":85,"rule_hits":[]},
    {"raw":"取消彩盒，改为简装托盘","cleaned":"Remove colour carton and switch to simple tray","market":"CN","score_min":25,"score_max":60,"rule_hits":["R_002"]},
    {"raw":"啤酒瓶颈玻璃克重从 145g 降到 138g","cleaned":"Reduce beer bottle neck glass weight from 145g to 138g","market":"CN","score_min":55,"score_max":85,"rule_hits":[]},
    {"raw":"夏季出货取消热缩膜","cleaned":"Remove shrink film for summer shipments","market":"CN","score_min":55,"score_max":85,"rule_hits":[]},
]

def evaluate() -> dict:
    bootstrap()
    passed = 0
    checks = []
    for i, row in enumerate(GOLDEN_ROWS, start=1):
        job = JobEnvelope(job_id=f"golden_{i}", conversation_id=f"golden_thread_{i}", user_id="eval", market=row["market"], workshop="golden", raw_ideas=[row["raw"]])
        res = VIPEXAgentRuntime().process(job)
        idea = res.results[0]
        clean_ok = idea.clean.cleaned_en == row["cleaned"]
        score_ok = row["score_min"] <= idea.feasibility.score <= row["score_max"]
        hit_ok = set(row["rule_hits"]).issubset(set(idea.feasibility.market_rule_hits))
        ok = clean_ok and score_ok and hit_ok
        passed += int(ok)
        checks.append({"row": i, "ok": ok, "clean_ok": clean_ok, "score": idea.feasibility.score, "score_ok": score_ok, "rule_hits": idea.feasibility.market_rule_hits, "hit_ok": hit_ok})
    return {"passed": passed, "total": len(GOLDEN_ROWS), "accuracy": passed/len(GOLDEN_ROWS), "checks": checks}

if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
