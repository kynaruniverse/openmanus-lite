"""Ollama (local LLM) provider — no API key required.

Uses the Ollama HTTP API directly via the standard library so this provider
adds no dependencies. Run an Ollama server locally first (ollama.com) and
``ollama pull llama3.2`` (or any model you like).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Iterator

from .base import BaseProvider, ProviderError


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        self._model = model or "llama3.2"
        self._base = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        body = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderError(self._explain(exc)) from exc
        except Exception as exc:
            raise ProviderError(f"Ollama error: {exc}") from exc

        text = (payload.get("response") or "").strip()
        if not text:
            raise ProviderError("Ollama returned an empty response.")
        return text

    def stream(self, prompt: str) -> Iterator[str]:
        body = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    piece = chunk.get("response", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break
        except urllib.error.URLError as exc:
            raise ProviderError(self._explain(exc)) from exc
        except Exception as exc:
            raise ProviderError(f"Ollama stream error: {exc}") from exc

    def _explain(self, exc: Exception) -> str:
        msg = str(exc)
        if "Connection refused" in msg or "Errno 111" in msg or "10061" in msg:
            return (
                f"Cannot reach the Ollama server at {self._base}. "
                "Start it with 'ollama serve' (download from https://ollama.com), "
                f"then pull a model: 'ollama pull {self._model}'."
            )
        if "404" in msg:
            return (
                f"Ollama model '{self._model}' is not installed. "
                f"Install it: ollama pull {self._model}"
            )
        return f"Ollama error: {msg}"
