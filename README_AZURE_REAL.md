# VIPEX Coach — Real Azure Version

This package is not only local simulation. It includes a real Azure deployment path using:

- Microsoft Teams Bot Framework endpoint: `POST /api/messages`
- Azure Bot Service / Teams app manifest
- Azure Service Bus queue with dead-letter handling
- Azure Container Apps API + Worker containers
- Azure Cosmos DB SQL API containers for jobs, sessions, rules, feedback
- Azure AI Search index for market rules and rejection/prior idea retrieval
- Azure OpenAI / AI Foundry-compatible model adapter
- Azure Container Registry
- Azure Key Vault placeholder
- Azure Application Insights + Log Analytics

## 1. Local test first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.storage.bootstrap
python scripts/run_demo.py
uvicorn app.main:app --reload --port 8000
```

## 2. Real Azure prerequisites

You need these permissions in your Azure tenant:

- Ability to create a Resource Group
- Ability to create Container Apps, ACR, Service Bus, Cosmos DB, AI Search, Key Vault, App Insights
- Ability to create/register a Microsoft Entra app for the bot
- Ability to enable the Microsoft Teams channel for Azure Bot
- Access to an Azure OpenAI / AI Foundry model deployment

## 3. Create the Bot identity

First deploy infra once or use any public URL placeholder, then create bot registration:

```bash
export RESOURCE_GROUP=rg-vipex-dev
export BOT_NAME=vipex-coach-bot-dev
export MESSAGING_ENDPOINT=https://<container-app-url>/api/messages
./infra/scripts/create_bot_and_teams_app.sh
```

This prints:

```text
BOT_APP_ID=...
BOT_APP_PASSWORD=...
```

Keep these safe. Put them into your deployment environment or Key Vault.

## 4. Deploy Azure infrastructure and containers

```bash
az login
export AZURE_SUBSCRIPTION_ID=<subscription-id>
export RESOURCE_GROUP=rg-vipex-dev
export LOCATION=eastus
export ENVIRONMENT=dev
export BOT_APP_ID=<bot-app-id>
export BOT_APP_PASSWORD=<bot-secret>
export AZURE_OPENAI_ENDPOINT=https://<azure-openai>.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=gpt-5.2
./infra/scripts/deploy_azure.sh
```

The script:

1. creates the resource group,
2. deploys Bicep resources,
3. builds container image in ACR,
4. redeploys API + worker with the real image,
5. prints the API URL and Teams messaging endpoint.

## 5. Create the AI Search KB index

After deployment, fill `.env` using outputs or use managed identity in the container. For local indexing from your laptop:

```bash
cp .env.azure.example .env
# fill AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY or use az login + RBAC
python scripts/index_kb.py
```

## 6. Connect Teams

Edit:

```text
infra/teams/manifest.json
```

Replace:

```text
REPLACE_WITH_BOT_APP_ID
REPLACE_WITH_CONTAINER_APP_DOMAIN
```

Zip the Teams manifest package with icons, then upload it in Teams Admin Center or Developer Portal.

## 7. Production endpoint checks

```bash
curl https://<api-url>/health
curl https://<api-url>/ops/release-gates?market=VN
```

For Bot Framework, Teams sends activities to:

```text
https://<api-url>/api/messages
```

## 8. What is still tenant-specific

The code and deployment scaffolding are real Azure. The tenant-specific things you must provide are:

- Subscription ID
- Bot app ID/secret
- Azure OpenAI/Foundry endpoint and deployment
- Optional AI Search admin key if not using RBAC
- Optional Cosmos key if not using managed identity
- Teams app upload/admin approval
- Fabric/OneLake permissions if you connect enterprise material/BOM/PPI data

## 9. Case-study wording

Use this wording:

> I implemented VIPEX Coach with real Azure deployment seams: Teams Bot Framework endpoint, Service Bus-backed asynchronous queueing, Container Apps worker processing, Cosmos DB session and market memory containers, AI Search retrieval, Azure OpenAI/Foundry model adapter, and Bicep deployment. It can also run locally for review, but the Azure mode is enabled by `RUNTIME_MODE=AZURE` and environment variables or managed identity.


## Final recheck

Read `docs/RECHECK_AGAINST_CASE_STUDY.md` for the latest gap-fix list and document coverage matrix.

## Final document-alignment notes

The case-study architecture includes Redis for idempotency/rate limits/hot-session reads and messy image/PDF/whiteboard inputs. This package now includes:

- `app/azure/redis_adapter.py` for Azure Cache for Redis usage.
- `app/azure/document_intelligence_adapter.py` for OCR extraction of handwritten notes, PDFs, and whiteboard screenshots.
- Bicep resources for Redis Premium and Azure AI Document Intelligence.
- Container Apps worker scale rule based on Service Bus queue depth.
- Worker-side proactive Teams update seam after `running`, `completed`, and `failed` states.

For a strict production deployment, store `REDIS_PASSWORD`, `DOCUMENT_INTELLIGENCE_KEY`, `BOT_APP_PASSWORD`, and `AZURE_OPENAI_KEY` in Key Vault and mount them into Container Apps as secrets.
