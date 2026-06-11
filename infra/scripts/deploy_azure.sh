#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   export AZURE_SUBSCRIPTION_ID="..."
#   export RESOURCE_GROUP="rg-vipex-dev"
#   export LOCATION="eastus"
#   export ACR_NAME="youracrname" # optional; if omitted, use Bicep-created ACR after first deploy
#   export BOT_APP_ID="..."       # from Entra app registration / Azure Bot
#   export BOT_APP_PASSWORD="..." # secret for the Bot app registration
#   export AZURE_OPENAI_ENDPOINT="https://<your-openai>.openai.azure.com/"
#   export AZURE_OPENAI_DEPLOYMENT="gpt-5.2"
#   ./infra/scripts/deploy_azure.sh

SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-vipex-dev}
LOCATION=${LOCATION:-eastus}
ENVIRONMENT=${ENVIRONMENT:-dev}
BOT_APP_ID=${BOT_APP_ID:-}
BOT_APP_PASSWORD=${BOT_APP_PASSWORD:-}
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT:-}
AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT:-gpt-5.2}

az account set --subscription "$SUBSCRIPTION_ID"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" >/dev/null

# First deploy infrastructure with placeholder images. Then use output ACR to build and redeploy.
PLACEHOLDER="mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/bicep/main.bicep \
  --parameters environment="$ENVIRONMENT" location="$LOCATION" apiImage="$PLACEHOLDER" workerImage="$PLACEHOLDER" \
    botAppId="$BOT_APP_ID" botAppPassword="$BOT_APP_PASSWORD" azureOpenAiEndpoint="$AZURE_OPENAI_ENDPOINT" azureOpenAiDeployment="$AZURE_OPENAI_DEPLOYMENT"

ACR_LOGIN_SERVER=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name main --query properties.outputs.acrLoginServer.value -o tsv)
ACR_NAME=${ACR_LOGIN_SERVER%%.azurecr.io}

az acr build --registry "$ACR_NAME" --image vipex-api:latest .
az acr build --registry "$ACR_NAME" --image vipex-worker:latest .

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/bicep/main.bicep \
  --parameters environment="$ENVIRONMENT" location="$LOCATION" \
    apiImage="$ACR_LOGIN_SERVER/vipex-api:latest" workerImage="$ACR_LOGIN_SERVER/vipex-worker:latest" \
    botAppId="$BOT_APP_ID" botAppPassword="$BOT_APP_PASSWORD" azureOpenAiEndpoint="$AZURE_OPENAI_ENDPOINT" azureOpenAiDeployment="$AZURE_OPENAI_DEPLOYMENT"

az deployment group show --resource-group "$RESOURCE_GROUP" --name main --query properties.outputs -o table
