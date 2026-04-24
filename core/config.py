"""Configuration for OpenManus-Lite."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=False)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


# Per-provider defaults: (env-var holding the API key, default model id)
PROVIDER_DEFAULTS: dict[str, tuple[Optional[str], str]] = {
    "gemini": ("GEMINI_API_KEY", "models/gemini-2.5-flash-lite"),
    "openai": ("OPENAI_API_KEY", "gpt-4o-mini"),
    "anthropic": ("ANTHROPIC_API_KEY", "claude-3-5-haiku-latest"),
    "openrouter": ("OPENROUTER_API_KEY", "meta-llama/llama-3.3-70b-instruct:free"),
    "ollama": (None, "llama3.2"),  # no key needed
}


@dataclass(frozen=True)
class Config:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str]
    max_steps: int
    log_level: str
    log_file: str
    workspace_dir: str
    cache_ttl: int

    @classmethod
    def from_env(cls) -> "Config":
        provider = (os.environ.get("OMX_PROVIDER") or "gemini").strip().lower()
        if provider not in PROVIDER_DEFAULTS:
            raise ConfigError(
                f"Unknown OMX_PROVIDER={provider!r}. "
                f"Choose one of: {', '.join(PROVIDER_DEFAULTS)}"
            )

        key_env, default_model = PROVIDER_DEFAULTS[provider]
        api_key = ""
        if key_env:
            api_key = (os.environ.get(key_env) or "").strip()
            if not api_key:
                raise ConfigError(
                    f"Missing API key for provider '{provider}'.\n"
                    f"  - On Replit: open the Secrets tab and add {key_env}.\n"
                    f"  - Locally: set {key_env} in .env or your shell environment."
                )

        model = (os.environ.get("OMX_MODEL") or default_model).strip()
        base_url = os.environ.get("OMX_BASE_URL", "").strip() or None

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_steps=_int_env("OMX_MAX_STEPS", 10),
            log_level=os.environ.get("OMX_LOG_LEVEL", "INFO").strip().upper(),
            log_file=os.environ.get("OMX_LOG_FILE", "omx.log").strip(),
            workspace_dir=os.environ.get("OMX_WORKSPACE", "workspace").strip(),
            cache_ttl=_int_env("OMX_CACHE_TTL", 0),
        )


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
