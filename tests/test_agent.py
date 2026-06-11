from app.models import JobEnvelope
from app.agent.runtime import VIPEXAgentRuntime
from app.storage.bootstrap import bootstrap


def test_vn_duplicate_removed():
    bootstrap()
    job = JobEnvelope(
        job_id="test_job",
        conversation_id="test_thread",
        user_id="tester",
        market="VN",
        workshop="Walk-the-Floor 2026-W22",
        raw_ideas=["Giảm độ dày lon 330ml xuống 0.235mm", "giam can gauge 330ml"],
    )
    res = VIPEXAgentRuntime().process(job)
    assert res.duplicates_removed == 1
    assert res.ideas_processed == 1


def test_cn_market_rule_hit():
    bootstrap()
    job = JobEnvelope(
        job_id="test_cn_rule",
        conversation_id="test_thread_cn",
        user_id="tester",
        market="CN",
        workshop="Gemba Kaizen 2026-W23",
        raw_ideas=["取消彩盒，改为简装托盘"],
    )
    res = VIPEXAgentRuntime().process(job)
    assert "R_002" in res.results[0].feasibility.market_rule_hits
