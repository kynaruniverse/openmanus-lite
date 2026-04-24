"""Google Gemini provider."""
from __future__ import annotations

from typing import Iterator

from .base import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ProviderError(
                "Gemini provider needs an API key. Set GEMINI_API_KEY "
                "(get one at https://aistudio.google.com/)."
            )
        try:
            from google import genai
            from google.genai import errors as genai_errors  # noqa: F401
        except ImportError as exc:
            raise ProviderError(
                "The 'google-genai' package is required for the Gemini provider. "
                "Install with: pip install google-genai"
            ) from exc
        self._client = genai.Client(api_key=api_key)
        self._model = model or "models/gemini-2.5-flash-lite"

    def generate(self, prompt: str) -> str:
        try:
            resp = self._client.models.generate_content(
                model=self._model, contents=prompt
            )
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc
        text = (resp.text or "").strip()
        if not text:
            raise ProviderError("Gemini returned an empty response.")
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            stream = self._client.models.generate_content_stream(
                model=self._model, contents=prompt
            )
            for chunk in stream:
                piece = getattr(chunk, "text", "") or ""
                if piece:
                    yield piece
        except Exception as exc:
            raise ProviderError(self._explain(exc)) from exc

    @staticmethod
    def _explain(exc: Exception) -> str:
        msg = str(exc)
        low = msg.lower()
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code in (400, 401) and ("api key" in low or "api_key_invalid" in low):
            return ("Gemini rejected the API key. Generate a fresh one at "
                    "https://aistudio.google.com/ and update GEMINI_API_KEY.")
        if code == 403 and "leaked" in low:
            return ("Gemini reports the API key has been leaked and is disabled. "
                    "Generate a new key.")
        if code == 429:
            return "Gemini quota exceeded (429). Wait or use a key with higher limits."
        if code == 404:
            return f"Gemini model not found (404). Check OMX_MODEL. Detail: {msg}"
        return f"Gemini error: {msg}"
