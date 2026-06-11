# Review First — VIPEX Coach Final Package

Start here.

## 1. Local verification

```bash
python -m app.storage.bootstrap
python scripts/run_demo.py
python -m pytest -q
python -m app.eval.golden_set
python scripts/run_release_gates.py
```

## 2. Case-study coverage files

Review these in order:

1. `docs/FINAL_GAP_CHECK.md`
2. `docs/RECHECK_AGAINST_CASE_STUDY.md`
3. `docs/DOCUMENT_COVERAGE_MATRIX.md`
4. `docs/SUBMISSION.md`
5. `VIPEX_Coach_Submission.docx`

## 3. Real Azure files

1. `README_AZURE_REAL.md`
2. `infra/bicep/main.bicep`
3. `infra/scripts/deploy_azure.sh`
4. `infra/teams/manifest.json`
5. `.env.azure.example`

## 4. Key implementation areas

- Teams Bot + file upload: `app/bot/*`, `app/api/routes.py`, `app/ingestion/parsers.py`
- Async queue + worker: `app/queue/*`, `app/azure/servicebus_adapter.py`
- Agent runtime/tools: `app/agent/runtime.py`, `app/tools/*`
- State/memory: `app/storage/db.py`, `app/azure/cosmos_adapter.py`
- Retrieval: `app/tools/retrieval.py`, `app/azure/ai_search_adapter.py`
- Fabric/OneLake: `app/azure/fabric_onelake_adapter.py`
- Redis: `app/azure/redis_adapter.py`
- OCR: `app/azure/document_intelligence_adapter.py`
- Ops/eval: `app/eval/golden_set.py`, `app/ops/*`

## 5. Honest production note

The package is now document-complete and Azure-ready, but a real deployment still requires tenant-specific values: subscription, Teams bot registration, model deployment, OneLake paths, Key Vault secret policy, and M365 app approval.
