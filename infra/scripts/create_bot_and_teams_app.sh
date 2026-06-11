#!/usr/bin/env bash
set -euo pipefail

# Creates Azure Bot resource + Entra app credentials using Azure CLI.
# You may need tenant admin rights and Teams app upload permissions.
# Usage:
#   export RESOURCE_GROUP=rg-vipex-dev
#   export LOCATION=global
#   export BOT_NAME=vipex-coach-bot-dev
#   export MESSAGING_ENDPOINT=https://<container-app-url>/api/messages
#   ./infra/scripts/create_bot_and_teams_app.sh

RESOURCE_GROUP=${RESOURCE_GROUP:?RESOURCE_GROUP is required}
BOT_NAME=${BOT_NAME:-vipex-coach-bot-dev}
LOCATION=${LOCATION:-global}
MESSAGING_ENDPOINT=${MESSAGING_ENDPOINT:?MESSAGING_ENDPOINT is required}

APP_JSON=$(az ad app create --display-name "$BOT_NAME")
APP_ID=$(echo "$APP_JSON" | python -c 'import sys,json; print(json.load(sys.stdin)["appId"])')
PASSWORD_JSON=$(az ad app credential reset --id "$APP_ID" --display-name vipex-secret)
APP_PASSWORD=$(echo "$PASSWORD_JSON" | python -c 'import sys,json; print(json.load(sys.stdin)["password"])')

az bot create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$BOT_NAME" \
  --appid "$APP_ID" \
  --password "$APP_PASSWORD" \
  --kind registration \
  --sku F0 \
  --endpoint "$MESSAGING_ENDPOINT" \
  --location "$LOCATION"

az bot msteams create --resource-group "$RESOURCE_GROUP" --name "$BOT_NAME"

cat <<EOF
BOT_APP_ID=$APP_ID
BOT_APP_PASSWORD=$APP_PASSWORD
MESSAGING_ENDPOINT=$MESSAGING_ENDPOINT

Next: put BOT_APP_ID/BOT_APP_PASSWORD into deployment parameters or Key Vault, then upload infra/teams/manifest.json to Teams Admin Center.
EOF
