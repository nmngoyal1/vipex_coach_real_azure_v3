# VIPEX Coach — AI Engineer Case Study Submission

## Assumption

I treat the Asia MVP as an inherited production system, not a greenfield design. The main goal is to make the agent operationally safe: market-scoped, auditable, async-by-design, measurable, and easy to debug during GCC handover.

---

# Part A — Problem Diagnosis & Ops

## A.1 Root Cause Structuring

| Category | Root cause | Symptoms explained |
|---|---|---|
| Data | Uneven material-master/BOM/PPI coverage by market and packaging component. Vietnam has mapped SKUs but may lack carton/cap/line-trial details; China has more SKUs but supplier PPI gaps. | Zero or low-confidence savings bands, fallback estimates, steerco distrust, inconsistent estimates across markets. |
| Method | Savings are expressed as low/mid/high bands, but the business still asks for a commit number. Feasibility also mixes hard constraints and soft commercial resistance. | Agent-accepted ideas later rejected by steerco, disagreement on which number enters the business case, weak calibration between feasibility score and actual approval. |
| Operating Model | Market rules can be captured by SMEs but have no owner, review cadence, expiry workflow, or quality bar. | Rules age silently, wrong rules keep blocking good ideas, Western Europe logic leaks into Asia, SMEs lose trust in the memory base. |

## A.2 Hypothesis Validation

Complaint: ideas are accepted by the agent but rejected by commercial steerco. Hypothesis: savings-band methodology, not material-spend source data, is the problem.

I would request a four-week Vietnam pilot sample with every idea that reached steerco, including: material spend inputs, low/mid/high predicted band, the number shown in the one-pager, steerco decision, rejection reason, and any revised finance estimate.

Metric comparison:

- Data agreement: compare agent material-spend base against finance/ERP base. Confirm data is not the issue if absolute variance is below 5–8% for at least 90% of reviewed ideas.
- Method agreement: compare steerco commit value against predicted band. Confirm methodology issue if more than 25% of rejected/returned ideas have valid source spend but the commit value is outside the agent band or finance cannot defend which point in the band to use.
- Calibration: bucket feasibility scores into 0–40, 41–60, 61–80, 81–100 and compare actual acceptance rate. Confirm method issue if high-score buckets still reject frequently for savings credibility reasons.

Confirmed would look like: material base matches finance, but steerco rejects because the savings band is not decision-ready or because mid-point assumptions are not transparent.

## A.3 Prioritisation

I would reduce weak savings credibility first.

Why: VIPEX Coach exists to produce defensible savings into commercial steerco. If savings are not credible, even perfect translation, dedupe, or one-pager quality will not convert into validated savings. The target is not just idea volume; it is accepted proposals and validated DKK impact.

Mitigation:

- expose spend base and assumptions per idea,
- return low/mid/high plus recommended commit number,
- attach data-quality label,
- flag missing material/PPI explicitly,
- require SME/finance review for low-confidence estimates.

Risk accepted by not choosing others: duplicate handling and translation may still create noise; market-memory gaps may still produce bad feasibility judgments. I accept that because those errors are easier to spot in review, while savings credibility failure can kill trust in the whole product.

## A.4 Operational Incident — First Hour Triage

Scenario: at 02:00 Vietnam time, a 300-idea upload has been processing for 90 minutes after acknowledgement.

First hour:

1. Confirm the user thread and job id from the Teams acknowledgement. This proves whether the Bot Service received the activity and stored the conversation reference.
2. Check Service Bus active, locked, and DLQ message count. If active is high, workers are not draining. If locked is high, workers may be hung. If DLQ > 0, inspect poison-message reason.
3. Check ACA Worker replica status and logs. I want to know whether replicas scaled, whether one message is stuck under lock, and whether the worker crashed after pulling the job.
4. Check the job record in Cosmos: status, attempts, market, workshop, input size, last updated timestamp.
5. Check AI Foundry run status: running, failed, requires-action, or rate-limited. For a 300-idea file, token consumption and tool-call fanout can easily be the bottleneck.
6. Check AI Search / OneLake tool-call errors. If material retrieval is timing out, the agent may be waiting on tools rather than model output.
7. Check result delivery path: if the job completed but Teams did not receive the result, validate stored conversation reference and proactive send permissions.
8. Communicate to user: acknowledge the incident, give current state, and avoid saying the file is lost unless confirmed. If the job is stuck but input is safe, requeue with idempotency key.

---

# Part B — Agent Design & Teams Integration

## B.1 Capability Boundaries

### Hard job 1: Cleaning and deduplicating messy ideas

Bucket: mixed, but controlled by deterministic services after model/language cleanup.

Why: translation and messy phrase normalization need model judgment, but duplicate grouping must be repeatable and auditable. A duplicate decision changes idea count and savings pipeline, so the final grouping should be deterministic or at least traceable.

Failure if placed incorrectly: if the model alone dedupes, the same file may produce different shortlisted ideas on different runs. If deterministic only, near-duplicates across Vietnamese, Chinese, and English will be missed.

Mitigation: language detection, packaging glossary, canonical English phrase, embedding/fuzzy similarity, deterministic duplicate key, and human override.

### Hard job 2: Estimating savings bands

Bucket: primarily deterministic service logic.

Why: savings must be tied to material spend, BOM, supplier PPI, and assumptions. The model can explain assumptions but should not invent numbers.

Failure if placed incorrectly: hallucinated savings, weak steerco credibility, inability to audit finance assumptions.

Mitigation: structured material retrieval, transparent low/mid/high formula, data-quality label, finance override workflow, and no-material fallback.

### Hard job 3: Capturing and applying market rules

Bucket: mixed. Capture can use model judgment; storage and application must be deterministic and governed.

Why: tacit rules often arrive in conversation, so extraction needs language understanding. But applying rules to feasibility must be market-scoped, versioned, and explainable.

Failure if placed incorrectly: Western Europe assumptions leak into Vietnam/China, expired rules keep blocking ideas, or soft resistance becomes hard law.

Mitigation: rule schema with market/category/constraint/rationale/provenance/validity/hardness; SME review; temporal expiry alerts; hard vs soft constraint separation.

### Boundaries to harden first

1. Savings-band computation.
2. Market-rule application and market scoping.
3. Duplicate grouping traceability.

### Areas to keep flexible

1. One-pager tone and wording.
2. Alternative idea generation.
3. Tacit rule suggestion before SME approval.

### Decisions to defer until production evidence

1. Whether feasibility scoring should become a trained model or remain rules + calibrated heuristics.
2. How much cross-market transfer is acceptable between WE, CN, VN.
3. Whether every one-pager needs human approval before steerco.

## B.2 Knowledge and Retrieval

For raw idea: “reduce can gauge on 330ml standard SKUs”.

Structured context extracted first:

- market: VN/CN from session,
- brand if provided,
- component: can_330ml,
- action: reduce gauge,
- target: 0.235mm if present,
- SKU range: standard 330ml SKUs,
- language and source workshop.

Retrieval approach:

1. Structured pre-filter first: market = VN for material data and market rules.
2. Hybrid retrieval second: vector + keyword over prior ideas, SOPs, and packaging specs.
3. Semantic ranking third: rerank by component, action, market, brand, validity, and rejection history relevance.

Ranking/filtering:

- Material data: always market-scoped unless explicitly doing benchmark.
- Market rules: always market-scoped and validity-filtered.
- Prior ideas: same-market first, cross-market allowed only with explicit scope flag.
- Rejection history: same-market hard constraints outrank cross-market soft resistance.

Fallback when no useful hits:

- create low-confidence one-pager,
- mark savings data quality low,
- request SME/material-owner input,
- do not invent savings,
- optionally use cross-market benchmark as “benchmark only, not decision basis”.

## B.3 Teams Integration

Design:

1. User uploads 200–500 idea file in Teams.
2. Bot validates file and replies immediately with text + adaptive card: job accepted, idea count, expected processing time.
3. Bot stores conversation reference and session metadata in Cosmos.
4. Bot puts job envelope onto Service Bus.
5. ACA Worker consumes one job per replica, invokes Foundry runtime, persists intermediate state.
6. Progress is shown as milestone updates, not streaming every token. Example: queued → cleaning → scoring → drafting → done.
7. Final result is delivered to the same Teams thread as adaptive card + downloadable JSON/Excel/one-pager bundle.
8. User can resume next morning because session state is in Cosmos keyed by conversation_id/workshop/market.

Cosmos session sketch:

```json
{
  "conversation_id": "thread_VN_001",
  "user_id": "SME_VN_03",
  "market": "VN",
  "workshop": "Walk-the-Floor 2026-W22",
  "last_job_id": "job_abc",
  "status": "completed",
  "conversation_reference": {},
  "last_artifact_url": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

Higher-cost generation should run outside the synchronous turn. The user should never wait on Teams for the full agent run.

## B.4 Cold-Start and Market Memory

Rule schema:

```json
{
  "rule_id": "R_002",
  "market": "CN",
  "category": "packaging",
  "constraint": "330ml carton on Brand_C SKUs cannot be substituted with shrink-tray packaging",
  "rationale": "Carton is also an in-store display",
  "captured_by": "SME_CN_05",
  "captured_at": "2026-02-04",
  "valid_from": "2026-02-04",
  "valid_to": "2026-12-31",
  "source_conversation_id": "thread_CN_0298",
  "hardness": "hard_constraint",
  "status": "active"
}
```

Application logic:

```python
rules = load_rules(market=request.market, status="active", valid_on=today)
for rule in rules:
    if rule_matches(rule, idea):
        feasibility -= severity(rule.hardness)
        trace.add(rule.rule_id)
```

Avoiding WE leakage:

- WE rules are not applied to VN/CN unless selected as cross-market benchmark.
- Any transferred rule gets label `benchmark_only` and requires SME approval before it can affect score.
- Market rules and material data use market filters before vector search.

Hard local constraints vs inertia:

- Hard constraint: legal, regulatory, line-tooling, capex impossibility, brand mandate.
- Soft resistance: historical preference, one-off campaign, old commercial objection.
- Soft resistance lowers confidence but should trigger alternatives, not automatic rejection.

## B.5 Multilingual Routing & Cost Envelope

Language flow:

1. Query understanding: detect language, normalize packaging terms, translate to canonical English for internal reasoning.
2. Retrieval: translate-then-query plus original-language query against mixed-language index. Use market filters first.
3. Generation: produce working one-pager in English; final response language depends on audience.
4. Rendering: local-language summary for market SMEs; English one-pager for EVP/steerco.

Latency/cost envelope for 300 ideas:

- Target: under 2 minutes P95.
- Batch cleaning/dedupe, do not call LLM once per idea if avoidable.
- Deterministic material and savings tools run in batch.
- Generate full one-pagers only for shortlisted ideas, not every raw duplicate.
- Use caching for repeated material/SKU lookups.
- Budget: 50,000 DKK / 10 active users / year; the system should track P99 cost per workshop and throttle expensive generation.

---

# Part C — Production Boundaries & Release Gates

## C.1 Sample End-to-End Workflow

Representative path: workshop upload → cleaning/dedupe → savings sizing → feasibility → one-pager.

```text
Teams upload
  -> Bot validates and stores conversation reference
  -> Service Bus job
  -> ACA Worker
  -> Clean/translate ideas                         [model + glossary]
  -> Extract structured context                    [deterministic]
  -> Deduplicate                                  [deterministic + similarity]
  -> Retrieve material/BOM/PPI from OneLake        [deterministic]
  -> Retrieve rules/prior ideas from AI Search     [hybrid retrieval]
  -> Compute savings band                          [deterministic]
  -> Score feasibility                             [rules + calibrated judgment]
  -> Generate alternatives                         [model judgment]
  -> Render one-pager                              [model judgment with structured facts]
  -> Persist result and telemetry                  [deterministic]
  -> Post result to Teams                          [Bot proactive reply]
```

Failure points:

1. Material retrieval returns zero rows, causing low-confidence savings.
2. Rule retrieval applies the wrong market rule or expired rule.

Telemetry/eval:

- stage latency,
- tool-call success rate,
- material row count,
- rule hit IDs,
- fallback rate,
- score distribution,
- feedback acceptance rate,
- golden-set stage-level accuracy.

## C.2 Hardening Priorities

Priority 1: savings-band service.

Reason: it is the commercial trust anchor. It must be auditable, deterministic, and tied to material spend.

Priority 2: market-memory/rule service.

Reason: market rules are where tacit knowledge enters the system. If they drift or leak across markets, feasibility scores become dangerous.

Strongest counter-argument: translation/dedupe errors happen earlier and can poison downstream stages. I would still prioritize savings and rules because those create higher business risk and steerco trust risk.

## C.3 Release Gates

1. Pilot acceptance rate >= 70% over at least 20 SME-reviewed ideas.
2. P95 end-to-end workshop processing <= 120 seconds for 200–500 ideas.
3. Tool-call success rate >= 99% for material/rule/search calls.
4. Golden-set critical accuracy >= 90%, with zero market-scope leakage failures.
5. Service Bus DLQ depth = 0 at cutover and no unresolved P1/P2 incidents in final dry run.

---

# Part D — Evaluation Framework

## D.1 Idea Quality vs Engine Quality

Idea quality metrics:

1. Savings-band realism: realised savings six months later should land inside predicted band.
2. Feasibility calibration: predicted feasibility bucket vs actual accept/reject rate.
3. Translation fidelity: human spot-check preservation of packaging meaning.
4. Dedupe precision/recall: compare against held-out duplicate-labeled workshop set.
5. Market-rule correctness: SME confirms rule hits are relevant.

Engine quality metrics:

1. P50/P95/P99 latency end-to-end.
2. P99 cost per workshop file.
3. Tool-call success rate.
4. Conversation completion rate.
5. DLQ rate and retry rate.
6. Fallback/no-material-data rate.

## D.2 Per-Step Eval

I would instrument eval per stage, not only end-to-end:

- translation/cleaning accuracy,
- dedupe grouping quality,
- retrieval hit relevance,
- material lookup coverage,
- savings-band formula checks,
- feasibility score calibration,
- one-pager factual grounding,
- Teams delivery and feedback capture.

If feasibility regresses tomorrow, inspect:

1. score distribution by market and component,
2. rule-hit rate by rule ID,
3. feedback rejection reasons,
4. golden-set rows involving feasibility,
5. recent rule changes or expiry events,
6. retrieval trace showing whether wrong market rules were applied.

This local project stores retrieval trace, rule hits, feedback, and telemetry to make this tractable.

## D.3 Golden Idea Set

The code implements a 10-row golden set in `app/eval/golden_set.py`, covering Vietnam and China examples from the appendix:

- VN can gauge duplicate,
- VN carton label simplification,
- VN bio-PE switch,
- VN cap change with tooling risk,
- CN neck standardisation duplicate,
- CN carton-to-tray market-rule hit,
- CN bottle lightweighting,
- CN shrink film removal.

## D.4 Drift Detection

Signals:

1. Operator acceptance rate below 70% over rolling 30 days with at least 20 feedback events.
2. P95 workshop latency above 120 seconds.
3. Any active market rule expiring within 60 days without review.
4. Savings fallback/no-material-data rate increases above 20% for a market/component.
5. Feasibility high-score rejection rate rises above 25%.

## D.5 In-Teams Feedback Loop

Adaptive card per idea:

- Accept
- Reject
- Edit
- Needs SME review
- Optional reason/correction

Signal flow:

1. Feasibility scoring: corrected score and rejection reason become calibration data.
2. Rejection-aware generation: repeated rejected pattern becomes negative retrieval context.
3. Golden set: SME corrections create candidates for new golden rows after review.

The key design principle is that feedback must take under two seconds. If feedback is slow, SMEs will not provide it and the market-memory base will rot.

---

# Time Spent

Approximate target allocation:

- Part A: 25 minutes
- Part B: 50 minutes
- Part C: 25 minutes
- Part D: 35 minutes
- Code/architecture mapping: additional implementation time outside the written case-study limit
