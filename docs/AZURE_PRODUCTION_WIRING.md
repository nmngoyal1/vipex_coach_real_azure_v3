# Azure Production Wiring Notes

This file explains how the case-study architecture would be wired in a real Azure environment. It is intentionally separated from the runnable demo because live deployment needs tenant credentials, resource names, managed identities, network rules, and approvals.

## Required Azure / Microsoft components

1. Microsoft Teams app and Bot registration
2. Microsoft Entra ID app registration and permissions
3. Azure Bot Service endpoint
4. Azure Service Bus Premium queue with DLQ
5. Azure Container Apps worker with queue-based scaling
6. Azure AI Foundry project and GPT deployment
7. Azure AI Search hybrid index with vector + keyword + semantic ranker
8. Azure Cosmos DB SQL API containers
9. Azure Cache for Redis
10. Microsoft Fabric / OneLake read-only data access
11. Azure Key Vault for secrets/configuration
12. Azure Container Registry
13. Azure Application Insights / Azure Monitor
14. VNet / private endpoints for corporate services

## Environment variables expected in production

```bash
APP_MODE=azure
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
SERVICE_BUS_NAMESPACE=
SERVICE_BUS_QUEUE_NAME=vipex-jobs
COSMOS_ENDPOINT=
COSMOS_DATABASE=vipex
AI_SEARCH_ENDPOINT=
AI_SEARCH_INDEX=vipex-kb
AI_FOUNDRY_ENDPOINT=
AI_FOUNDRY_DEPLOYMENT=gpt-5.2
FABRIC_ONELAKE_ENDPOINT=
KEY_VAULT_URI=
APPLICATIONINSIGHTS_CONNECTION_STRING=
```

## Containers

- `api`: Bot/FastAPI facade for Teams-style requests, job acknowledgement, feedback, and rule capture.
- `worker`: Service Bus consumer that invokes the runtime and writes results.

## Production behavior

1. Teams sends activity/file upload to Bot Service.
2. Bot validates payload and stores conversation reference.
3. Bot pushes job envelope to Service Bus and immediately acknowledges.
4. ACA Worker consumes job, invokes AI Foundry runtime/tools.
5. Agent retrieves KB context from AI Search and structured material data from OneLake/Fabric.
6. Session, idea history, market rules, feedback, and telemetry are persisted.
7. Bot sends final result to the original Teams thread.
8. Azure Monitor/App Insights tracks latency, cost, failures, DLQ, and drift signals.
