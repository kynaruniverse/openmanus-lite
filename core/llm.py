"""Provider-agnostic LLM client.

Wraps a concrete ``BaseProvider`` and adds: hard call budget, structured
logging, uniform error type, streaming support. The rest of the codebase
never imports a specific provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from core.logging_setup import get_logger
from core.providers import BaseProvider, ProviderError


class LLMError(RuntimeError):
    """Raised when the LLM call fails."""


class BudgetExceeded(LLMError):
    """Raised when the configured per-task call budget is exhausted."""


@dataclass
class LLMClient:
    provider: BaseProvider
    max_calls: int = 0  # 0 = unlimited
    call_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._log = get_logger()

    @property
    def name(self) -> str:
        return self.provider.name

    def reset_budget(self) -> None:
        self.call_count = 0

    def _check_budget(self) -> None:
        if self.max_calls and self.call_count >= self.max_calls:
            raise BudgetExceeded(
                f"LLM budget exhausted: {self.call_count}/{self.max_calls} calls. "
                f"Pass --budget N (or OMX_BUDGET=N) to raise it."
            )

    def generate(self, prompt: str) -> str:
        self._check_budget()
        self.call_count += 1
        self._log.debug("LLM PROMPT (provider=%s call=%d):\n%s",
                        self.provider.name, self.call_count, prompt)
        try:
            text = self.provider.generate(prompt)
        except ProviderError as exc:
            self._log.error("Provider error: %s", exc)
            raise LLMError(str(exc)) from exc
        except Exception as exc:
            self._log.exception("Unexpected provider failure")
            raise LLMError(f"Unexpected {self.provider.name} failure: {exc}") from exc
        self._log.debug("LLM RESPONSE (call=%d):\n%s", self.call_count, text)
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        self._check_budget()
        self.call_count += 1
        self._log.debug("LLM STREAM PROMPT (provider=%s call=%d):\n%s",
                        self.provider.name, self.call_count, prompt)
        collected = []
        try:
            for piece in self.provider.stream(prompt):
                collected.append(piece)
                yield piece
        except ProviderError as exc:
            self._log.error("Provider stream error: %s", exc)
            raise LLMError(str(exc)) from exc
        except Exception as exc:
            self._log.exception("Unexpected provider stream failure")
            raise LLMError(f"Unexpected stream failure: {exc}") from exc
        self._log.debug("LLM STREAM COMPLETE (call=%d):\n%s",
                        self.call_count, "".join(collected).strip())
