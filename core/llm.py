"""Thin wrapper around the Google Gemini client.

Centralises API construction, retry/error handling, request/response logging,
streaming, and a hard call-budget so the rest of the codebase never touches the
SDK directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

from google import genai
from google.genai import errors as genai_errors

from core.logging_setup import get_logger


class LLMError(RuntimeError):
    """Raised when the LLM call fails in a way the agent cannot recover from."""


class BudgetExceeded(LLMError):
    """Raised when the configured per-task call budget is exhausted."""


@dataclass
class LLMClient:
    api_key: str
    model: str
    max_calls: int = 0  # 0 = unlimited
    call_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise LLMError("LLMClient created without an API key.")
        self._client = genai.Client(api_key=self.api_key)
        self._log = get_logger()

    def reset_budget(self) -> None:
        self.call_count = 0

    def _check_budget(self) -> None:
        if self.max_calls and self.call_count >= self.max_calls:
            raise BudgetExceeded(
                f"LLM budget exhausted: {self.call_count}/{self.max_calls} calls "
                f"already used. Pass --budget N (or OMX_BUDGET=N) to raise it."
            )

    def generate(self, prompt: str) -> str:
        """Send ``prompt`` and return the full text. Raises ``LLMError``."""
        self._check_budget()
        self.call_count += 1
        self._log.debug("LLM PROMPT (call=%d, model=%s):\n%s",
                        self.call_count, self.model, prompt)

        try:
            response = self._client.models.generate_content(
                model=self.model, contents=prompt
            )
        except genai_errors.ClientError as exc:
            msg = self._explain_client_error(exc)
            self._log.error("LLM client error: %s", msg)
            raise LLMError(msg) from exc
        except genai_errors.ServerError as exc:
            self._log.error("LLM server error: %s", exc)
            raise LLMError(f"Gemini server error: {exc}") from exc
        except Exception as exc:
            self._log.exception("Unexpected LLM failure")
            raise LLMError(f"Unexpected LLM failure: {exc}") from exc

        text = (response.text or "").strip()
        self._log.debug("LLM RESPONSE (call=%d):\n%s", self.call_count, text)
        if not text:
            raise LLMError("Gemini returned an empty response.")
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        """Yield response chunks as they arrive. Raises ``LLMError``.

        Tracks the call against the budget exactly like ``generate``. The full
        response is also logged at DEBUG once streaming completes.
        """
        self._check_budget()
        self.call_count += 1
        self._log.debug("LLM STREAM PROMPT (call=%d, model=%s):\n%s",
                        self.call_count, self.model, prompt)

        try:
            stream = self._client.models.generate_content_stream(
                model=self.model, contents=prompt
            )
            collected = []
            for chunk in stream:
                piece = getattr(chunk, "text", "") or ""
                if piece:
                    collected.append(piece)
                    yield piece
        except genai_errors.ClientError as exc:
            msg = self._explain_client_error(exc)
            self._log.error("LLM client error during stream: %s", msg)
            raise LLMError(msg) from exc
        except genai_errors.ServerError as exc:
            self._log.error("LLM server error during stream: %s", exc)
            raise LLMError(f"Gemini server error: {exc}") from exc
        except Exception as exc:
            self._log.exception("Unexpected LLM stream failure")
            raise LLMError(f"Unexpected LLM stream failure: {exc}") from exc

        full = "".join(collected).strip()
        self._log.debug("LLM STREAM COMPLETE (call=%d):\n%s", self.call_count, full)

    @staticmethod
    def _explain_client_error(exc: genai_errors.ClientError) -> str:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        message = str(exc)
        lowered = message.lower()
        if (
            code in (400, 401)
            and ("api_key_invalid" in lowered or "api key" in lowered)
        ):
            return (
                "Gemini rejected the API key (the key is invalid or expired). "
                "Generate a fresh key at https://aistudio.google.com/ and update "
                "the GEMINI_API_KEY secret."
            )
        if code == 403:
            if "leaked" in lowered:
                return (
                    "Gemini reports the API key has been leaked and is disabled. "
                    "Generate a new key at https://aistudio.google.com/ and update "
                    "GEMINI_API_KEY."
                )
            return f"Gemini denied the request (403): {message}"
        if code == 429:
            return (
                "Gemini quota exceeded (429). Wait for the quota to reset or use a "
                "key with higher limits."
            )
        if code == 404:
            return (
                f"Gemini model not found (404). Set OMX_MODEL to a valid model id. "
                f"Detail: {message}"
            )
        return f"Gemini client error ({code}): {message}"
