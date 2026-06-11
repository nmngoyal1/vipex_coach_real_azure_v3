# VIPEX Coach — Recheck Against Case Study

This file records the final recheck against the uploaded case-study document.

## Recheck result

I found and fixed these issues in the previous package:

1. **Pytest import failure** — added `pyproject.toml` and `tests/conftest.py` so tests run from a clean checkout.
2. **Upload endpoint naming** — added `POST /teams/upload` in addition to `/teams/message` so the API matches the Teams upload wording.
3. **File ingestion coverage** — added parsers for CSV, XLSX, JSON, and TXT workshop uploads; image/PDF now returns an explicit OCR-preprocessing warning instead of silently ignoring the file.
4. **Teams file attachments** — Bot Framework handler now attempts to process Teams file attachments, not only pasted text.
5. **Azure Service Bus receiver lifecycle** — fixed real adapter so messages can be completed/dead-lettered before the receiver is closed.
6. **Azure Bot Service resource** — Bicep now includes Azure Bot Service when `BOT_APP_ID` is supplied.
7. **Managed Identity role assignments** — Bicep now includes ACR Pull and Service Bus sender/receiver role assignments.
8. **OneLake / Fabric seam** — added a real read-only OneLake adapter for material master/BOM/PPI style extracts.
9. **Observability seam** — added Azure Monitor/OpenTelemetry configuration seam when App Insights connection string is provided.
10. **Private networking note** — added optional private networking Bicep skeleton for corporate VNet/private endpoint rollout.
11. **Redis coverage** — added Azure Cache for Redis adapter and Bicep resource for idempotency, rate limits, and hot session reads.
12. **OCR coverage** — added Azure AI Document Intelligence seam for screenshots, whiteboards, handwritten notes, and PDFs.
13. **Proactive Teams delivery seam** — worker now calls a Teams proactive update seam for running/completed/failed states.
14. **Queue-depth scaling** — worker Container App now includes a Service Bus queue-depth scale rule.

## Document coverage checklist

| Case-study requirement | Package coverage |
|---|---|
| Teams user interface, adaptive cards, file upload | `app/bot/*`, `app/cards/*`, `/teams/upload_file`, Teams manifest |
| Bot Service receives activity, validates, queues jobs | `app/bot/routes.py`, `app/bot/teams_activity_handler.py`, `app/api/routes.py` |
| Async queue with DLQ / poison handling | Local queue + `app/azure/servicebus_adapter.py` |
| ACA worker processes jobs | `app/queue/worker.py`, `scripts/run_worker.py`, Container Apps Bicep |
| AI Foundry / GPT agent runtime seam | `app/agent/runtime.py`, `app/azure/foundry_adapter.py` |
| AI Search hybrid/semantic retrieval seam | `app/tools/retrieval.py`, `app/azure/ai_search_adapter.py`, `scripts/index_kb.py` |
| Cosmos sessions, idea history, market rules | `app/storage/db.py`, `app/azure/cosmos_adapter.py`, Cosmos Bicep containers |
| Redis idempotency/rate limit design | `app/azure/redis_adapter.py`, Redis env settings, Redis Premium Bicep resource; local uses DB-backed simulation. |
| OneLake / Fabric material/BOM/PPI | CSV local + `app/azure/fabric_onelake_adapter.py` |
| Key Vault / ACR / App Insights | Bicep resources + env wiring |
| Market memory with provenance and validity | `/rules`, market_rules table, schema in `models.py`, docs/SUBMISSION.md |
| Savings bands, feasibility, alternatives, one-pager | `app/tools/engine_tools.py`, `app/agent/runtime.py` |
| Evaluation framework + golden set | `app/eval/golden_set.py`, `docs/SUBMISSION.md` |
| Drift detection | `app/ops/drift.py` |
| Release gates | `app/ops/release_gates.py` |
| First-hour incident triage | `app/ops/triage.py`, `/ops/triage/{job_id}` |
| Written Parts A-D response | `docs/SUBMISSION.md`, `VIPEX_Coach_Submission.docx` |

## Remaining items that require tenant decisions, not code guessing

These cannot be honestly hardcoded without your Azure tenant and enterprise policies:

- Exact private DNS zones/hub-spoke networking configuration.
- Teams app publishing/approval workflow in your Microsoft 365 tenant.
- Exact AI Foundry model deployment name and quota.
- Exact OneLake workspace/lakehouse paths and table permissions.
- Whether image/PDF OCR is handled by an existing M365 extraction pipeline or by adding Azure AI Document Intelligence.

The code now has seams for these, and the submission document explains the intended production design.
