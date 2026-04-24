"""Tiny exact-match cache so repeated tasks don't burn tokens.

Stored as JSON in the project root so it persists across runs but is git-ignored.
Errors are never cached.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from core.logging_setup import get_logger

MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json"
)


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


def find(user_query: str) -> Optional[str]:
    return _load().get(user_query)


def add(user_query: str, result: str) -> None:
    if not user_query or not result:
        return
    mem = _load()
    mem[user_query] = result
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2)
    except OSError as exc:
        get_logger().warning("Could not write memory file %s: %s", MEMORY_FILE, exc)


def clear() -> None:
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
