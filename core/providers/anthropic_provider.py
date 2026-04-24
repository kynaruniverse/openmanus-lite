"""Anthropic Claude provider."""
from __future__ import annotations

from typing import Iterator

from .base import BaseProvider, ProviderError


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ProviderError(
                "Anthropic provider needs an API key. Set ANTHROPIC_API_KEY."
            )
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ProviderError(
                "The 'anthropic' package is required for this provider. "
                "Install with: pip install anthropic"
            ) from exc
        self._client = Anthropic(api_key=api_key)
        self._model = model or "claude-3-5-haiku-latest"

    def generate(self, prompt: str) -> str:
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc
        try:
            text = resp.content[0].text or ""
        except (AttributeError, IndexError):
            text = ""
        text = text.strip()
        if not text:
            raise ProviderError("Anthropic returned an empty response.")
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            with self._client.messages.stream(
                model=self._model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc

    @staticmethod
    def _explain(exc: Exception) -> str:
        msg = str(exc)
        low = msg.lower()
        if "invalid api key" in low or "authentication" in low:
            return "Anthropic rejected the API key. Check ANTHROPIC_API_KEY."
        if "rate limit" in low or "429" in low:
            return "Anthropic rate limit reached. Wait and retry."
        if "not found" in low and "model" in low:
            return f"Anthropic model not found. Set OMX_MODEL to a valid id. Detail: {msg}"
        return f"Anthropic error: {msg}"
