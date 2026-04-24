"""OpenRouter provider — one key, hundreds of models.

Reuses the OpenAI client because OpenRouter exposes an OpenAI-compatible API.
"""
from __future__ import annotations

from .openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(
            api_key=api_key,
            model=model or "meta-llama/llama-3.3-70b-instruct:free",
            base_url="https://openrouter.ai/api/v1",
        )
