"""LLM provider registry.

Each provider is loaded lazily so users only need the SDK for the provider
they actually use. New providers can be added by dropping a module in this
package that implements the ``BaseProvider`` interface.
"""
from __future__ import annotations

from typing import Optional

from .base import BaseProvider, ProviderError

PROVIDERS = ("gemini", "openai", "anthropic", "ollama", "openrouter")


def make_provider(
    name: str,
    *,
    api_key: str = "",
    model: str = "",
    base_url: Optional[str] = None,
) -> BaseProvider:
    """Instantiate a provider by short name."""
    name = (name or "gemini").lower()
    if name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider(api_key=api_key, model=model)
    if name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key, model=model)
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider(model=model, base_url=base_url or "http://localhost:11434")
    if name == "openrouter":
        from .openrouter import OpenRouterProvider
        return OpenRouterProvider(api_key=api_key, model=model)
    raise ProviderError(f"Unknown provider: {name!r}. Choose from {PROVIDERS}.")


__all__ = ["BaseProvider", "ProviderError", "PROVIDERS", "make_provider"]
