"""Logging configuration for OpenManus-Lite.

A single ``omx`` logger is used throughout the codebase. Console output is
human-readable; file output is verbose and includes prompts/responses/actions.
"""
from __future__ import annotations

import logging
import sys
from logging import Logger
from pathlib import Path

_CONFIGURED = False


def setup_logging(level: str = "INFO", log_file: str = "omx.log") -> Logger:
    """Configure the ``omx`` logger. Idempotent."""
    global _CONFIGURED
    logger = logging.getLogger("omx")

    if _CONFIGURED:
        return logger

    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter
    logger.propagate = False

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(getattr(logging, level, logging.INFO))
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    except OSError as exc:  # pragma: no cover - filesystem oddity
        logger.warning("Could not open log file %s: %s", log_file, exc)

    _CONFIGURED = True
    return logger


def get_logger() -> Logger:
    """Return the shared ``omx`` logger."""
    return logging.getLogger("omx")
