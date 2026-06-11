# Azure Resource Checklist

## Core resources

- Resource group: `rg-vipex-coach-asia`
- Azure Container Registry: `acrvipexcoach`
- Azure Service Bus Premium namespace and queue: `vipex-jobs`
- Azure Container Apps environment with VNet integration
- API app container: Bot/Teams public ingress
- Worker app/job container: internal, Service Bus-triggered scale rule, 1–10 replicas
- Cosmos DB SQL API containers:
  - `sessions`, partition `/conversation_id`
  - `jobs`, partition `/market`
  - `ideas`, partition `/market`
  - `market_rules`, partition `/market`
  - `feedback`, partition `/market`
- Azure AI Search index with hybrid vector + keyword + semantic ranker
- Microsoft Fabric / OneLake shortcuts/views for material master, BOM, supplier PPI
- Azure AI Foundry project and gpt-class deployment
- Key Vault for connection strings, deployment names, and API config
- Application Insights / Azure Monitor

## Managed identity

Use managed identity from Bot/API and Worker to access:

- Service Bus sender/receiver
- Cosmos DB data contributor
- AI Search query role
- Key Vault secrets user
- ACR pull
- AI Foundry project access

## Production observability

Minimum dashboard tiles:

- Service Bus active message count
- Service Bus DLQ depth
- Worker replica count
- Worker failures by exception class
- Foundry run status: running / failed / requires_action / completed
- Token and cost per workshop file
- End-to-end P50/P95 latency
- Tool-call success rate
- Feedback acceptance/reject/edit rate
- Market rule application rate
- Market rules expiring in next 60 days

## Release gate targets

- Pilot acceptance rate >= 70%
- P95 workshop processing <= 2 minutes
- Dead-letter depth = 0 before launch cutover
- P99 cost/workshop within budget envelope
- Eval suite passes with no critical regression
