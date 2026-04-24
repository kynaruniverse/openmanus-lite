"""Thin wrapper around the Google Gemini client.

Centralises API construction, retry/error handling, and request/response logging
so the rest of the codebase never touches the SDK directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import errors as genai_errors

from core.logging_setup import get_logger


class LLMError(RuntimeError):
    """Raised when the LLM call fails in a way the agent cannot recover from."""


@dataclass
class LLMClient:
    api_key: str
    model: str

    def __post_init__(self) -> None:
        if not self.api_key:
            raise LLMError("LLMClient created without an API key.")
        self._client = genai.Client(api_key=self.api_key)
        self._log = get_logger()

    def generate(self, prompt: str) -> str:
        """Send ``prompt`` to the model and return raw text. Raises ``LLMError``."""
        self._log.debug("LLM PROMPT (model=%s):\n%s", self.model, prompt)

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except genai_errors.ClientError as exc:
            msg = self._explain_client_error(exc)
            self._log.error("LLM client error: %s", msg)
            raise LLMError(msg) from exc
        except genai_errors.ServerError as exc:
            self._log.error("LLM server error: %s", exc)
            raise LLMError(f"Gemini server error: {exc}") from exc
        except Exception as exc:  # network etc.
            self._log.exception("Unexpected LLM failure")
            raise LLMError(f"Unexpected LLM failure: {exc}") from exc

        text = (response.text or "").strip()
        self._log.debug("LLM RESPONSE:\n%s", text)
        if not text:
            raise LLMError("Gemini returned an empty response.")
        return text

    @staticmethod
    def _explain_client_error(exc: genai_errors.ClientError) -> str:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        message = str(exc)
        if code == 401 or "API key" in message and "invalid" in message.lower():
            return "Gemini rejected the API key (401). Check GEMINI_API_KEY."
        if code == 403:
            if "leaked" in message.lower():
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
