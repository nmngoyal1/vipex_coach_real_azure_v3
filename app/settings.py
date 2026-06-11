from __future__ import annotations
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Runtime settings.

    LOCAL mode runs with SQLite + local queue + local retrieval.
    AZURE mode uses Azure Service Bus, Cosmos DB, AI Search, Azure OpenAI/Foundry-compatible endpoint,
    Bot Framework credentials, and Application Insights when configured.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    runtime_mode: str = Field(default="LOCAL", alias="RUNTIME_MODE")  # LOCAL or AZURE

    # Bot / Teams
    bot_app_id: str | None = Field(default=None, alias="BOT_APP_ID")
    bot_app_password: str | None = Field(default=None, alias="BOT_APP_PASSWORD")
    bot_tenant_id: str | None = Field(default=None, alias="BOT_TENANT_ID")
    public_base_url: str | None = Field(default=None, alias="PUBLIC_BASE_URL")

    # Service Bus
    service_bus_fully_qualified_namespace: str | None = Field(default=None, alias="SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE")
    service_bus_connection_string: str | None = Field(default=None, alias="SERVICE_BUS_CONNECTION_STRING")
    service_bus_queue_name: str = Field(default="vipex-jobs", alias="SERVICE_BUS_QUEUE_NAME")

    # Cosmos DB
    cosmos_endpoint: str | None = Field(default=None, alias="COSMOS_ENDPOINT")
    cosmos_key: str | None = Field(default=None, alias="COSMOS_KEY")
    cosmos_database: str = Field(default="vipex", alias="COSMOS_DATABASE")
    cosmos_jobs_container: str = Field(default="jobs", alias="COSMOS_JOBS_CONTAINER")
    cosmos_sessions_container: str = Field(default="sessions", alias="COSMOS_SESSIONS_CONTAINER")
    cosmos_rules_container: str = Field(default="marketRules", alias="COSMOS_RULES_CONTAINER")
    cosmos_feedback_container: str = Field(default="feedback", alias="COSMOS_FEEDBACK_CONTAINER")

    # AI Search
    azure_search_endpoint: str | None = Field(default=None, alias="AZURE_SEARCH_ENDPOINT")
    azure_search_key: str | None = Field(default=None, alias="AZURE_SEARCH_KEY")
    azure_search_index: str = Field(default="vipex-kb", alias="AZURE_SEARCH_INDEX")

    # Azure OpenAI / Foundry-compatible chat completion endpoint
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str | None = Field(default=None, alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field(default="gpt-5.2", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-10-21", alias="AZURE_OPENAI_API_VERSION")

    # Redis / hot cache / idempotency
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    # Azure AI Document Intelligence for handwritten notes / PDFs / whiteboard screenshots
    document_intelligence_endpoint: str | None = Field(default=None, alias="DOCUMENT_INTELLIGENCE_ENDPOINT")
    document_intelligence_key: str | None = Field(default=None, alias="DOCUMENT_INTELLIGENCE_KEY")

    # Fabric / OneLake placeholder
    fabric_workspace_id: str | None = Field(default=None, alias="FABRIC_WORKSPACE_ID")
    onelake_account_url: str = Field(default="https://onelake.dfs.fabric.microsoft.com", alias="ONELAKE_ACCOUNT_URL")
    onelake_file_system: str | None = Field(default=None, alias="ONELAKE_FILE_SYSTEM")
    onelake_material_path: str | None = Field(default=None, alias="ONELAKE_MATERIAL_PATH")

    # Observability
    applicationinsights_connection_string: str | None = Field(default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING")

    @property
    def is_azure(self) -> bool:
        return self.runtime_mode.upper() == "AZURE"

@lru_cache
def get_settings() -> Settings:
    return Settings()
