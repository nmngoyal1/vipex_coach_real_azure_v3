# VIPEX Coach Document Coverage Matrix

This package is aligned to the case-study document requirements. The code is supporting evidence; the primary submission is `docs/SUBMISSION.md` and `VIPEX_Coach_Submission.docx`.

| Document requirement | Where covered | Status |
|---|---|---|
| Part A.1 Data / Method / Operating Model root causes | `docs/SUBMISSION.md` Part A.1 | Complete |
| Part A.2 Hypothesis validation for steerco rejection | `docs/SUBMISSION.md` Part A.2 | Complete |
| Part A.3 Launch-risk prioritisation | `docs/SUBMISSION.md` Part A.3 | Complete |
| Part A.4 02:00 incident triage | `docs/SUBMISSION.md` Part A.4, `app/ops/triage.py`, `scripts/run_triage.py` | Complete |
| B.1 Capability boundaries | `docs/SUBMISSION.md` Part B.1, `app/agent/runtime.py` | Complete |
| B.2 KB and retrieval design | `docs/SUBMISSION.md` Part B.2, `app/tools/retrieval.py` | Complete |
| Correct market scoping | `docs/SUBMISSION.md` Part B.2/B.4, `app/tools/engine_tools.py`, `app/storage/db.py` | Complete |
| B.3 Teams async interaction | `docs/SUBMISSION.md` Part B.3, `app/api/routes.py`, `app/cards/adaptive_cards.py`, `app/queue/worker.py` | Complete as design + runnable support |
| Conversation/session state | `docs/SUBMISSION.md` Part B.3, `app/storage/db.py` | Complete |
| Progress / result delivery pattern | `docs/SUBMISSION.md` Part B.3, `app/api/routes.py`, `app/cards/adaptive_cards.py` | Complete |
| B.4 Cold-start and market memory | `docs/SUBMISSION.md` Part B.4, `app/storage/db.py`, `data/market_rules.json` | Complete |
| Rule provenance and temporal validity | `docs/SUBMISSION.md` Part B.4/D.4, `app/storage/db.py`, `data/market_rules.json` | Complete |
| Hard local constraints vs organizational inertia | `docs/SUBMISSION.md` Part B.4 | Complete |
| B.5 Multilingual routing and cost envelope | `docs/SUBMISSION.md` Part B.5, `app/tools/translation.py`, `app/agent/runtime.py` | Complete as design + sample support |
| C.1 End-to-end workflow | `docs/SUBMISSION.md` Part C.1, `app/agent/runtime.py`, `scripts/run_demo.py` | Complete |
| Deterministic vs model-driven stages | `docs/SUBMISSION.md` Part B.1/C.1 | Complete |
| Failure points and telemetry | `docs/SUBMISSION.md` Part A.4/C.1/D.2, `app/ops/*` | Complete |
| C.2 Hardening priorities | `docs/SUBMISSION.md` Part C.2 | Complete |
| C.3 Release gates with numeric thresholds | `docs/SUBMISSION.md` Part C.3, `app/ops/release_gates.py` | Complete |
| D.1 Idea quality vs engine quality metrics | `docs/SUBMISSION.md` Part D.1 | Complete |
| D.2 Per-step eval and regression localization | `docs/SUBMISSION.md` Part D.2, `app/eval/golden_set.py` | Complete |
| D.3 Ten-row Vietnam/China golden set | `docs/SUBMISSION.md` Part D.3, `app/eval/golden_set.py` | Complete |
| D.4 Drift signals and thresholds | `docs/SUBMISSION.md` Part D.4, `app/ops/drift.py` | Complete |
| D.5 In-Teams feedback loop | `docs/SUBMISSION.md` Part D.5, `app/cards/adaptive_cards.py`, `app/api/routes.py` | Complete |
| Sample raw workshop ideas | `data/raw_workshop_ideas.csv`, `scripts/run_demo.py` | Complete |
| Sample material master extract | `data/material_master.csv` | Complete |
| Sample rejection history | `data/rejection_history.csv` | Complete |
| Sample market memory rules | `data/market_rules.json` | Complete |
| Single submission document | `VIPEX_Coach_Submission.docx`, `docs/SUBMISSION.md` | Complete |
| Step-by-step recreate instructions | `README.md` | Complete |

## Important honesty note

This package does not claim a live Azure tenant deployment. The case study asks for reasoning, architecture, pseudocode/code, and a single submission document. The implementation includes production-shaped boundaries and local runnable support so a reviewer can validate the design without access to Carlsberg/Azure credentials. Real deployment requires tenant-specific Teams Bot, Service Bus, Cosmos DB, AI Search, AI Foundry, Fabric/OneLake, Key Vault, ACR, and Monitor configuration.
