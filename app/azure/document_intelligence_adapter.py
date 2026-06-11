from __future__ import annotations
from app.settings import get_settings

class AzureDocumentIntelligenceExtractor:
    """OCR/document extraction seam for screenshots, whiteboards, handwritten notes, and PDFs.

    This covers the case-study input types that are not already structured as CSV/XLSX/TXT/JSON.
    It uses Azure AI Document Intelligence prebuilt-read when configured.
    """
    def __init__(self) -> None:
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install azure-ai-documentintelligence to enable OCR extraction.") from exc
        s = get_settings()
        if not (s.document_intelligence_endpoint and s.document_intelligence_key):
            raise RuntimeError("DOCUMENT_INTELLIGENCE_ENDPOINT and DOCUMENT_INTELLIGENCE_KEY are required for OCR extraction")
        self.client = DocumentIntelligenceClient(s.document_intelligence_endpoint, AzureKeyCredential(s.document_intelligence_key))

    def extract_lines(self, content: bytes) -> list[str]:
        poller = self.client.begin_analyze_document("prebuilt-read", body=content)
        result = poller.result()
        lines: list[str] = []
        for page in getattr(result, "pages", []) or []:
            for line in getattr(page, "lines", []) or []:
                if getattr(line, "content", None):
                    lines.append(line.content.strip())
        return [l for l in lines if l]
