from __future__ import annotations
from typing import Any
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from app.settings import get_settings

class AzureAISearchRetriever:
    """Real Azure AI Search hybrid/semantic retrieval adapter.

    The Bicep creates the service. Create/index documents using scripts/index_kb.py.
    """
    def __init__(self) -> None:
        s = get_settings()
        if not s.azure_search_endpoint:
            raise RuntimeError("AZURE_SEARCH_ENDPOINT is required in AZURE mode")
        credential = AzureKeyCredential(s.azure_search_key) if s.azure_search_key else DefaultAzureCredential()
        self.client = SearchClient(s.azure_search_endpoint, s.azure_search_index, credential=credential)

    def search(self, query: str, market: str, k: int = 5, include_cross_market: bool = False) -> list[dict[str, Any]]:
        filters = f"market eq '{market}'" if not include_cross_market else f"market eq '{market}' or scope eq 'cross_market'"
        results = self.client.search(
            search_text=query,
            filter=filters,
            top=k,
            query_type="semantic",
            semantic_configuration_name="default",
            select=["id", "title", "content", "market", "category", "source", "valid_to"],
        )
        return [dict(r) for r in results]
