"""Discover tools from the ``tools/`` directory.

Each ``*_tool.py`` module must expose a ``run(args: dict) -> str`` function.
The tool's name is derived from the filename (e.g. ``shell_tool.py`` -> ``shell``).
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Callable, Dict

from core.logging_setup import get_logger

ToolFn = Callable[[dict], str]
TOOLS: Dict[str, ToolFn] = {}


def load() -> Dict[str, ToolFn]:
    """Populate the ``TOOLS`` registry. Idempotent."""
    log = get_logger()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(project_root, "tools")

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if not os.path.isdir(folder):
        log.warning("Tools directory not found: %s", folder)
        return TOOLS

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith("_tool.py"):
            continue
        name = filename[: -len("_tool.py")]
        path = os.path.join(folder, filename)
        try:
            spec = importlib.util.spec_from_file_location(f"tools.{name}", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as exc:
            log.error("Failed to load tool %s: %s", filename, exc)
            continue

        run_fn = getattr(mod, "run", None)
        if callable(run_fn):
            TOOLS[name] = run_fn
            log.debug("Loaded tool: %s", name)
        else:
            log.warning("Tool %s has no callable run(); skipped", filename)

    return TOOLS
