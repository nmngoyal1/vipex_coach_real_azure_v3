@description('Short environment name, for example dev or prod')
param environment string = 'dev'

@description('Azure region')
param location string = resourceGroup().location

@description('Unique suffix for globally unique service names')
param suffix string = uniqueString(resourceGroup().id)

@description('Container image for API/Bot. Example: myacr.azurecr.io/vipex-api:latest')
param apiImage string

@description('Container image for Worker. Example: myacr.azurecr.io/vipex-worker:latest')
param workerImage string

@description('Azure OpenAI endpoint. Keep empty if model deployment is created separately later.')
param azureOpenAiEndpoint string = ''

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-5.2'

@description('Bot App ID created in Microsoft Entra / Azure Bot')
param botAppId string = ''

@secure()
@description('Bot App password/secret. Prefer Key Vault in production.')
param botAppPassword string = ''

var prefix = 'vipex-${environment}-${suffix}'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-mi'
  location: location
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-law'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-appi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: replace('${prefix}acr', '-', '')
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: '${prefix}-sb'
  location: location
  sku: {
    name: 'Premium'
    tier: 'Premium'
    capacity: 1
  }
}

resource jobsQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBus
  name: 'vipex-jobs'
  properties: {
    lockDuration: 'PT5M'
    maxDeliveryCount: 5
    deadLetteringOnMessageExpiration: true
    defaultMessageTimeToLive: 'P14D'
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
  }
}


resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, identity.id, 'AcrPull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource serviceBusSenderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, identity.id, 'AzureServiceBusDataSender')
  scope: serviceBus
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource serviceBusReceiverRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, identity.id, 'AzureServiceBusDataReceiver')
  scope: serviceBus
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: '${prefix}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [{ locationName: location, failoverPriority: 0, isZoneRedundant: false }]
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: 'vipex'
  properties: { resource: { id: 'vipex' } }
}

resource jobsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'jobs'
  properties: { resource: { id: 'jobs', partitionKey: { paths: ['/market'], kind: 'Hash' } } }
}
resource sessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'sessions'
  properties: { resource: { id: 'sessions', partitionKey: { paths: ['/conversation_id'], kind: 'Hash' } } }
}
resource rulesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'marketRules'
  properties: { resource: { id: 'marketRules', partitionKey: { paths: ['/market'], kind: 'Hash' } } }
}
resource feedbackContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'feedback'
  properties: { resource: { id: 'feedback', partitionKey: { paths: ['/market'], kind: 'Hash' } } }
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${prefix}-search'
  location: location
  sku: { name: 'basic' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    semanticSearch: 'standard'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${prefix}-kv'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}


resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: '${prefix}-redis'
  location: location
  sku: {
    name: 'Premium'
    family: 'P'
    capacity: 1
  }
  properties: {
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${prefix}-docint'
  location: location
  kind: 'FormRecognizer'
  sku: { name: 'S0' }
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

resource containerEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${prefix}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${prefix}-api'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: { external: true, targetPort: 8000, transport: 'auto' }
      registries: [{ server: acr.properties.loginServer, identity: identity.id }]
      secrets: [
        { name: 'bot-app-password', value: botAppPassword }
      ]
    }
    template: {
      containers: [{
        name: 'api'
        image: apiImage
        env: [
          { name: 'RUNTIME_MODE', value: 'AZURE' }
          { name: 'SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE', value: '${serviceBus.name}.servicebus.windows.net' }
          { name: 'SERVICE_BUS_QUEUE_NAME', value: jobsQueue.name }
          { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
          { name: 'COSMOS_DATABASE', value: cosmosDb.name }
          { name: 'AZURE_SEARCH_ENDPOINT', value: 'https://${search.name}.search.windows.net' }
          { name: 'AZURE_SEARCH_INDEX', value: 'vipex-kb' }
          { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
          { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
          { name: 'BOT_APP_ID', value: botAppId }
          { name: 'BOT_APP_PASSWORD', secretRef: 'bot-app-password' }
          { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          { name: 'REDIS_URL', value: 'rediss://${redis.properties.hostName}:6380' }
          { name: 'DOCUMENT_INTELLIGENCE_ENDPOINT', value: documentIntelligence.properties.endpoint }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}



resource azureBot 'Microsoft.BotService/botServices@2022-09-15' = if (!empty(botAppId)) {
  name: '${prefix}-bot'
  location: 'global'
  sku: { name: 'F0' }
  kind: 'azurebot'
  properties: {
    displayName: 'VIPEX Coach ${environment}'
    endpoint: 'https://${api.properties.configuration.ingress.fqdn}/api/messages'
    msaAppId: botAppId
    msaAppTenantId: tenant().tenantId
    msaAppType: 'SingleTenant'
  }
}

resource worker 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${prefix}-worker'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      registries: [{ server: acr.properties.loginServer, identity: identity.id }]
    }
    template: {
      containers: [{
        name: 'worker'
        image: workerImage
        command: ['python', 'scripts/run_worker.py']
        env: [
          { name: 'RUNTIME_MODE', value: 'AZURE' }
          { name: 'SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE', value: '${serviceBus.name}.servicebus.windows.net' }
          { name: 'SERVICE_BUS_QUEUE_NAME', value: jobsQueue.name }
          { name: 'COSMOS_ENDPOINT', value: cosmos.properties.documentEndpoint }
          { name: 'COSMOS_DATABASE', value: cosmosDb.name }
          { name: 'AZURE_SEARCH_ENDPOINT', value: 'https://${search.name}.search.windows.net' }
          { name: 'AZURE_SEARCH_INDEX', value: 'vipex-kb' }
          { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
          { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
          { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          { name: 'REDIS_URL', value: 'rediss://${redis.properties.hostName}:6380' }
          { name: 'DOCUMENT_INTELLIGENCE_ENDPOINT', value: documentIntelligence.properties.endpoint }
        ]
      }]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [{
          name: 'servicebus-queue-depth'
          custom: {
            type: 'azure-servicebus'
            metadata: {
              namespace: serviceBus.name
              queueName: jobsQueue.name
              messageCount: '1'
            }
            identity: identity.id
          }
        }]
      }
    }
  }
}

output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output botMessagingEndpoint string = 'https://${api.properties.configuration.ingress.fqdn}/api/messages'
output serviceBusNamespace string = serviceBus.name
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output redisHostName string = redis.properties.hostName
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output acrLoginServer string = acr.properties.loginServer
output azureBotName string = empty(botAppId) ? 'not-created' : '${prefix}-bot'
