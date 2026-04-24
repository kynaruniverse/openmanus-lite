"""Tiny normalised cache so repeated tasks don't burn tokens.

Stored as JSON in the project root so it persists across runs but is git-ignored.
- Keys are normalised (lowercased, whitespace-collapsed, punctuation-stripped).
- Each entry has a timestamp so callers can opt into TTL filtering.
- Errors are never cached.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Optional

from core.logging_setup import get_logger

MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json"
)

_PUNCT_RE = re.compile(r"[^\w\s]+", flags=re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")


def _normalise(query: str) -> str:
    if not query:
        return ""
    q = query.strip().lower()
    q = _PUNCT_RE.sub(" ", q)
    q = _WHITESPACE_RE.sub(" ", q).strip()
    return q


def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        get_logger().warning("Could not read memory file %s: %s", MEMORY_FILE, exc)
        return {}


def find(user_query: str, ttl_seconds: int = 0) -> Optional[str]:
    """Return the cached result for ``user_query`` or ``None``.

    If ``ttl_seconds`` is positive, entries older than that are ignored
    (and lazily expired on the next ``add``).
    """
    key = _normalise(user_query)
    if not key:
        return None
    entry = _load().get(key)
    if not entry:
        return None
    if isinstance(entry, str):
        # Legacy schema: bare string.
        return entry
    if not isinstance(entry, dict):
        return None
    if ttl_seconds > 0:
        ts = entry.get("ts", 0)
        if ts and (time.time() - ts) > ttl_seconds:
            return None
    return entry.get("result")


def add(user_query: str, result: str) -> None:
    key = _normalise(user_query)
    if not key or not result:
        return
    mem = _load()
    mem[key] = {"result": result, "ts": int(time.time())}
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2)
    except OSError as exc:
        get_logger().warning("Could not write memory file %s: %s", MEMORY_FILE, exc)


def clear() -> None:
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
