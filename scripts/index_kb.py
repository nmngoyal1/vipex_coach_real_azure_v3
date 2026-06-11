from __future__ import annotations
import json
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch
from azure.search.documents import SearchClient
from app.settings import get_settings

s = get_settings()
if not s.azure_search_endpoint:
    raise SystemExit("AZURE_SEARCH_ENDPOINT is required")
cred = AzureKeyCredential(s.azure_search_key) if s.azure_search_key else DefaultAzureCredential()
index_client = SearchIndexClient(s.azure_search_endpoint, cred)

fields = [
    SimpleField(name="id", type="Edm.String", key=True),
    SearchableField(name="title", type="Edm.String"),
    SearchableField(name="content", type="Edm.String"),
    SimpleField(name="market", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="source", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="scope", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="valid_to", type="Edm.String", filterable=True),
]
semantic = SemanticSearch(configurations=[SemanticConfiguration(name="default", prioritized_fields=SemanticPrioritizedFields(title_field=SemanticField(field_name="title"), content_fields=[SemanticField(field_name="content")]))])
index = SearchIndex(name=s.azure_search_index, fields=fields, semantic_search=semantic)
try:
    index_client.create_or_update_index(index)
except Exception as e:
    print(f"Index create/update warning: {e}")

rules = json.loads(Path("data/market_rules.json").read_text(encoding="utf-8"))
docs = []
for r in rules:
    docs.append({
        "id": r["rule_id"],
        "title": f"{r['market']} {r['category']} rule {r['rule_id']}",
        "content": f"{r['constraint']} Rationale: {r['rationale']}",
        "market": r["market"],
        "category": r["category"],
        "source": "market_rule",
        "scope": "market",
        "valid_to": r.get("valid_to") or "",
    })

# prior idea / SOP stubs from synthetic appendix
for row in Path("data/rejection_history.csv").read_text(encoding="utf-8").splitlines()[1:]:
    if not row.strip():
        continue
    idea_ref, market, category, reason, rejected_at = next(__import__('csv').reader([row]))
    docs.append({"id": idea_ref, "title": f"Rejected prior idea {idea_ref}", "content": reason, "market": market, "category": category, "source": "rejection_history", "scope": "market", "valid_to": ""})

client = SearchClient(s.azure_search_endpoint, s.azure_search_index, cred)
if docs:
    client.upload_documents(docs)
print(f"Uploaded {len(docs)} KB documents to {s.azure_search_index}")
