from __future__ import annotations
from openai import AzureOpenAI
from app.settings import get_settings

class AzureFoundryAgentClient:
    """Azure AI Foundry / Azure OpenAI-compatible generation adapter.

    This uses an Azure OpenAI chat deployment as the model runtime seam. If your tenant uses the newer
    Foundry Agents SDK, keep this class boundary and replace only this file.
    """
    def __init__(self) -> None:
        s = get_settings()
        if not (s.azure_openai_endpoint and s.azure_openai_key):
            raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY are required for real model calls")
        self.deployment = s.azure_openai_deployment
        self.client = AzureOpenAI(
            azure_endpoint=s.azure_openai_endpoint,
            api_key=s.azure_openai_key,
            api_version=s.azure_openai_api_version,
        )

    def complete_json(self, system: str, user: str, max_tokens: int = 1200) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or "{}"
