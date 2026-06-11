@description('Optional private networking skeleton for corporate deployment. Use after validating private DNS zones and service SKUs in the target tenant.')
param location string = resourceGroup().location
param prefix string = 'vipex-prod'

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${prefix}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.42.0.0/16'] }
    subnets: [
      { name: 'container-apps-infra', properties: { addressPrefix: '10.42.0.0/23' } }
      { name: 'private-endpoints', properties: { addressPrefix: '10.42.2.0/24', privateEndpointNetworkPolicies: 'Disabled' } }
    ]
  }
}

// Private endpoints for Service Bus, Cosmos DB, AI Search, Key Vault, ACR, and Azure OpenAI/AI Foundry
// should be added here in production. They are intentionally kept in a separate optional file because
// private DNS zone names and existing hub/spoke networking differ by enterprise tenant.
output vnetName string = vnet.name
