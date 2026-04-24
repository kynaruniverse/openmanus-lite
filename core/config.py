"""Configuration for OpenManus-Lite.

Reads required and optional settings from environment variables (loaded from
``.env`` if present). Fails fast with a clear message when required values are
missing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env if it exists (developer convenience). On Replit, prefer Secrets.
load_dotenv(override=False)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    max_steps: int
    log_level: str
    log_file: str
    workspace_dir: str
    cache_ttl: int  # seconds; 0 = no expiry

    @classmethod
    def from_env(cls) -> "Config":
        api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise ConfigError(
                "GEMINI_API_KEY is not set.\n"
                "  - On Replit: open the Secrets tab and add GEMINI_API_KEY.\n"
                "  - Locally: copy .env.example to .env and fill in the key.\n"
                "  Get a key at https://aistudio.google.com/."
            )

        model = os.environ.get("OMX_MODEL", "models/gemini-2.5-flash-lite").strip()
        log_level = os.environ.get("OMX_LOG_LEVEL", "INFO").strip().upper()
        log_file = os.environ.get("OMX_LOG_FILE", "omx.log").strip()
        workspace_dir = os.environ.get("OMX_WORKSPACE", "workspace").strip()
        max_steps = _int_env("OMX_MAX_STEPS", 10)
        cache_ttl = _int_env("OMX_CACHE_TTL", 0)

        return cls(
            api_key=api_key,
            model=model,
            max_steps=max_steps,
            log_level=log_level,
            log_file=log_file,
            workspace_dir=workspace_dir,
            cache_ttl=cache_ttl,
        )


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
