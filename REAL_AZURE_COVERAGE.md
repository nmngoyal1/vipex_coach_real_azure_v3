# Real Azure Coverage Added

| Document component | Real Azure implementation in this package |
|---|---|
| Microsoft Teams | `app/bot/routes.py`, `app/bot/teams_activity_handler.py`, `infra/teams/manifest.json` |
| Bot Service | Bot Framework endpoint `/api/messages`; `create_bot_and_teams_app.sh` |
| Service Bus | `app/azure/servicebus_adapter.py`; Bicep namespace + queue + DLQ config |
| ACA Worker | `scripts/run_worker.py`; Bicep worker Container App scaling 1–10 replicas |
| AI Foundry / GPT runtime | `app/azure/foundry_adapter.py` Azure OpenAI/Foundry-compatible adapter |
| AI Search | `app/azure/ai_search_adapter.py`; `scripts/index_kb.py`; Bicep search service |
| Cosmos DB | `app/azure/cosmos_adapter.py`; Bicep database + jobs/sessions/rules/feedback containers |
| Redis | Still documented as production extension; not mandatory for basic Azure run |
| OneLake / Fabric | Env placeholders; adapter seam retained; tenant permissions required |
| Key Vault | Bicep Key Vault resource; secrets should be moved there for production hardening |
| ACR | Bicep ACR + `az acr build` deployment script |
| App Insights / Monitor | Bicep App Insights + Log Analytics connection string passed to apps |
| VNet/private endpoints | Not implemented in Bicep because it is tenant/network-specific; described in docs as hardening step |


## Final recheck

Read `docs/RECHECK_AGAINST_CASE_STUDY.md` for the latest gap-fix list and document coverage matrix.
