"""Backwards-compatible shim. The real CLI lives in :mod:`core.cli`."""
from core.cli import main, run_from_cli  # noqa: F401

__all__ = ["main", "run_from_cli"]
