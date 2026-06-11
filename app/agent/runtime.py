from __future__ import annotations
import time, uuid
from app.models import AgentResult, CleanIdea, ProcessedIdea, OnePager, JobEnvelope, RetrievalTrace
from app.tools.translation import translate_to_english, detect_language
from app.tools.retrieval import extract_context, find_similar_ideas, retrieve_material
from app.tools.engine_tools import compute_savings_band, score_feasibility, generate_alternatives, deterministic_duplicate_key
from app.storage.db import log_metric

class VIPEXAgentRuntime:
    """Local stand-in for Azure AI Foundry agent runtime.

    Production boundary:
    - deterministic code: schema validation, market scoping, dedupe keys, savings math, persistence, release gates
    - model judgment: messy language cleanup, tacit rule extraction, one-pager narrative, ambiguous feasibility explanation
    """

    def process(self, job: JobEnvelope) -> AgentResult:
        start = time.time()
        seen = set()
        results: list[ProcessedIdea] = []
        duplicates = 0
        stage_ms: dict[str, int] = {}

        for idx, raw in enumerate(job.raw_ideas):
            t0 = time.time()
            detected = detect_language(raw) if job.language == "auto" else job.language
            cleaned = translate_to_english(raw, job.language)
            ctx = extract_context(cleaned, job.market, job.brand)
            dup_key = deterministic_duplicate_key(cleaned)
            if dup_key in seen:
                duplicates += 1
                continue
            seen.add(dup_key)
            clean = CleanIdea(source_index=idx, raw_text=raw, cleaned_en=cleaned, duplicate_group_id=dup_key, language_detected=detected, **ctx)
            stage_ms["cleaning_dedupe"] = stage_ms.get("cleaning_dedupe", 0) + int((time.time()-t0)*1000)

            t1 = time.time()
            similar = find_similar_ideas(cleaned, job.market, k=5)
            material = retrieve_material(clean.component, job.market)
            savings = compute_savings_band(clean.model_dump(), job.market)
            feasibility = score_feasibility(clean.model_dump(), job.market)
            alternatives = generate_alternatives(clean.model_dump(), 3)
            trace = RetrievalTrace(
                structured_filters={"market": job.market, "brand": job.brand, "component": clean.component, "sku_range": clean.sku_range},
                market_rule_hits=feasibility.market_rule_hits,
                similar_idea_refs=[str(s.get("idea_id")) for s in similar],
                material_rows=len(material),
                fallback_used=(savings.method.startswith("fallback"))
            )
            stage_ms["retrieval_scoring"] = stage_ms.get("retrieval_scoring", 0) + int((time.time()-t1)*1000)

            t2 = time.time()
            one_pager = OnePager(
                title=f"VIPEX proposal: {clean.cleaned_en}",
                summary=(f"Proposal for {job.market} / {job.brand or 'all brands'}: {clean.cleaned_en}. "
                         f"Savings are expressed as a band and feasibility is {feasibility.score}/100."),
                implementation_steps=[
                    "Validate affected SKU list against market material master and BOM.",
                    "Run supplier and line-trial feasibility check.",
                    "Review commercial constraints and market-rule hits with SME.",
                    "Prepare steerco decision with low/mid/high savings band."
                ],
                risks=feasibility.reason_codes + (["cross_market_prior_ideas_used"] if any(s.get("scope") == "cross_market" for s in similar) else []),
                savings_band=savings,
                feasibility=feasibility
            )
            stage_ms["one_pager"] = stage_ms.get("one_pager", 0) + int((time.time()-t2)*1000)
            results.append(ProcessedIdea(idea_id=f"idea_{uuid.uuid4().hex[:10]}", clean=clean, retrieval_trace=trace, savings_band=savings, feasibility=feasibility, alternatives=alternatives, one_pager=one_pager))

        latency_ms = int((time.time()-start)*1000)
        estimated_cost_dkk = round(0.05 + len(job.raw_ideas)*0.03 + len(results)*0.01, 2)
        for stage, ms in stage_ms.items():
            log_metric(job.job_id, job.conversation_id, job.market, stage, "stage_latency_ms", ms)
        log_metric(job.job_id, job.conversation_id, job.market, "end_to_end", "latency_ms", latency_ms)
        log_metric(job.job_id, job.conversation_id, job.market, "end_to_end", "estimated_cost_dkk", estimated_cost_dkk)

        return AgentResult(
            job_id=job.job_id,
            conversation_id=job.conversation_id,
            market=job.market,
            ideas_processed=len(results),
            duplicates_removed=duplicates,
            results=results,
            telemetry={
                "latency_ms": latency_ms,
                "stage_ms": stage_ms,
                "estimated_cost_dkk": estimated_cost_dkk,
                "model_deployment": "local-simulated-gpt-5.2",
                "target_p95_ms": 120000,
                "market_scoping": "market rules and material data filtered to request market; prior ideas may be cross-market with explicit scope flag"
            }
        )
