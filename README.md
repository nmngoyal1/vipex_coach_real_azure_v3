# VIPEX Coach — Production-Shaped Local Project

This project is a runnable local simulation of the VIPEX Coach case study architecture. It keeps the same product boundaries as the target Azure design:

Teams/Bot Service → Service Bus queue → ACA Worker → AI Foundry-style agent runtime → AI Search / OneLake / Cosmos / Redis-style state → Teams result + feedback loop.

The local implementation is intentionally dependency-light so it runs on a laptop, but the code has production seams for Azure Service Bus, Azure AI Foundry, Cosmos DB, and AI Search.

## Feature coverage

Implemented locally:

- Teams-style message and CSV upload endpoint
- Immediate acknowledgement adaptive card
- Async queue lifecycle using SQLite as a Service Bus simulator
- Worker process simulating Azure Container Apps Worker
- Agent runtime simulating Azure AI Foundry orchestration
- Cleaning and translation of VN/CN sample ideas
- Near-duplicate detection
- Market-scoped material lookup from CSV, simulating OneLake/Fabric
- Market-scoped rule memory, simulating Cosmos DB
- Retrieval trace with material rows, similar prior ideas, and market-rule hits
- Savings bands: low / mid / high DKK
- Feasibility score with reason codes and rule hits
- Rejection-aware alternatives
- Implementation-ready one-pager JSON
- Feedback API and feedback adaptive card
- Rule-capture API with provenance, validity, and hardness
- Drift checks: acceptance, latency, rule expiry
- Release gates for VN → CN launch/handover
- On-call triage endpoint/script
- 10-row golden-set eval
- Dockerfile and deploy skeleton
- Written case-study answer in `docs/SUBMISSION.md`

Production integration seams:

- `app/azure/servicebus_adapter.py`
- `app/azure/foundry_adapter.py`
- `app/azure/cosmos_adapter.py`
- `app/azure/ai_search_adapter.py`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.storage.bootstrap
python scripts/run_demo.py
```

Expected behavior:

1. The demo submits a Teams-style upload.
2. The API returns an acknowledgement card and a `job_id`.
3. The worker consumes one queued message.
4. Results are written to SQLite and `outputs/<job_id>_result.json`.

## Run API

```bash
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Test a Teams-style message

POST `/teams/message`:

```json
{
  "conversation_id": "thread_vn_test",
  "user_id": "SME_VN_03",
  "market": "VN",
  "workshop": "Walk-the-Floor 2026-W22",
  "ideas": [
    "Giảm độ dày lon 330ml xuống 0.235mm",
    "giam can gauge 330ml",
    "Bỏ in nhãn màu vàng trên thùng carton 24 lon",
    "Đổi nắp khoén 26mm sang 24mm"
  ]
}
```

Then process queued work:

```bash
curl -X POST http://127.0.0.1:8000/worker/process-one
```

Check job:

```bash
curl http://127.0.0.1:8000/jobs/<job_id>
```

## Run eval and ops

```bash
python -m app.eval.golden_set
python scripts/run_release_gates.py
python scripts/run_triage.py <job_id>
```

API ops endpoints:

- `GET /ops/queue`
- `GET /ops/triage/{job_id}`
- `GET /ops/drift?market=VN`
- `GET /ops/release-gates?market=VN`

## Feedback loop

POST `/feedback`:

```json
{
  "idea_id": "idea_123",
  "conversation_id": "thread_vn_test",
  "market": "VN",
  "signal": "reject",
  "reason": "Requires filling-line tooling not in 2026 capex plan",
  "corrected_feasibility": 40
}
```

This is stored for three downstream loops:

1. feasibility calibration,
2. rejection-aware generation,
3. golden-set review.

## Market memory rule capture

POST `/rules`:

```json
{
  "market": "CN",
  "category": "packaging",
  "constraint": "330ml carton on Brand_C SKUs cannot be substituted with shrink-tray packaging",
  "rationale": "Carton also acts as in-store promotional display.",
  "captured_by": "SME_CN_05",
  "source_conversation_id": "thread_CN_0298",
  "valid_from": "2026-02-04",
  "valid_to": "2026-12-31",
  "hardness": "hard_constraint"
}
```

## Local-to-Azure mapping

| Local component | Azure production equivalent |
|---|---|
| FastAPI `/teams/message` | Azure Bot Service Teams activity handler |
| SQLite queue table | Azure Service Bus Premium queue + DLQ |
| `VIPEXWorker` | Azure Container Apps Worker |
| `VIPEXAgentRuntime` | Azure AI Foundry agent runtime with gpt-5.2 deployment |
| Local CSV material master | Fabric / OneLake material, BOM, supplier PPI |
| Local retrieval | Azure AI Search hybrid vector + keyword + semantic ranker |
| SQLite tables | Cosmos DB SQL API containers |
| Feedback endpoints | Teams adaptive-card feedback actions |
| Ops endpoints | Azure Monitor / App Insights dashboards and KQL |

## Docker

```bash
docker build -t vipex-coach:local .
docker run -p 8000:8000 vipex-coach:local
```

## Suggested Azure deployment path

1. Create Azure Container Registry.
2. Build and push image.
3. Create Azure Service Bus Premium namespace and queue.
4. Create Cosmos DB SQL API account and containers.
5. Create AI Search service and indexes.
6. Create AI Foundry project/deployment and register deterministic tools.
7. Deploy API container as Bot backend.
8. Deploy worker container as ACA worker/job with Service Bus scale rule.
9. Add Application Insights and dashboards for latency, failures, DLQ, token/cost, feedback, and drift.

See `deploy/azure_resources.md` for a more detailed checklist.
