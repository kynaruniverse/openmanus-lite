"""Provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator


class ProviderError(RuntimeError):
    """Raised by a provider for any non-recoverable failure."""


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the full response text. Raise ``ProviderError`` on failure."""

    @abstractmethod
    def stream(self, prompt: str) -> Iterator[str]:
        """Yield response chunks. Raise ``ProviderError`` on failure."""
