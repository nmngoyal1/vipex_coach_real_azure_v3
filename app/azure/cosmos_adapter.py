from __future__ import annotations
from typing import Any
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient, PartitionKey
from app.settings import get_settings

class AzureCosmosStore:
    """Real Cosmos DB SQL API store for jobs, sessions, market rules, and feedback."""
    def __init__(self) -> None:
        s = get_settings()
        if not s.cosmos_endpoint:
            raise RuntimeError("COSMOS_ENDPOINT is required in AZURE mode")
        credential = s.cosmos_key if s.cosmos_key else DefaultAzureCredential()
        self.client = CosmosClient(s.cosmos_endpoint, credential=credential)
        self.db = self.client.create_database_if_not_exists(s.cosmos_database)
        self.jobs = self.db.create_container_if_not_exists(s.cosmos_jobs_container, PartitionKey(path="/market"))
        self.sessions = self.db.create_container_if_not_exists(s.cosmos_sessions_container, PartitionKey(path="/conversation_id"))
        self.rules = self.db.create_container_if_not_exists(s.cosmos_rules_container, PartitionKey(path="/market"))
        self.feedback = self.db.create_container_if_not_exists(s.cosmos_feedback_container, PartitionKey(path="/market"))

    def upsert_job(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc["id"] = doc.get("job_id", doc.get("id"))
        return self.jobs.upsert_item(doc)

    def get_job(self, job_id: str, market: str) -> dict[str, Any] | None:
        try:
            return self.jobs.read_item(job_id, partition_key=market)
        except Exception:
            return None

    def upsert_session(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc["id"] = doc.get("conversation_id", doc.get("id"))
        return self.sessions.upsert_item(doc)

    def insert_rule(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc["id"] = doc.get("rule_id", doc.get("id"))
        return self.rules.upsert_item(doc)

    def insert_feedback(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc["id"] = doc.get("feedback_id", doc.get("id"))
        return self.feedback.upsert_item(doc)
