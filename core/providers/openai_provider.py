"""OpenAI provider (also used as the base for OpenAI-compatible APIs)."""
from __future__ import annotations

from typing import Iterator, Optional

from .base import BaseProvider, ProviderError


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
    ) -> None:
        if not api_key:
            raise ProviderError(
                "OpenAI provider needs an API key. Set OPENAI_API_KEY."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError(
                "The 'openai' package is required for this provider. "
                "Install with: pip install openai"
            ) from exc
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model or "gpt-4o-mini"

    def generate(self, prompt: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError(f"{self.name} returned an empty response.")
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc

    def _explain(self, exc: Exception) -> str:
        msg = str(exc)
        low = msg.lower()
        if "invalid api key" in low or "invalid_api_key" in low:
            return f"{self.name} rejected the API key. Check the key in your secrets."
        if "rate limit" in low or "429" in low:
            return f"{self.name} rate limit reached. Wait and retry."
        if "model" in low and ("not found" in low or "does not exist" in low):
            return f"{self.name} model '{self._model}' not found. Set OMX_MODEL to a valid id."
        return f"{self.name} error: {msg}"
