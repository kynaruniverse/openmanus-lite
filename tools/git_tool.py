"""Run git subcommands inside the active target directory."""
from __future__ import annotations

import os
import shutil
import subprocess

TIMEOUT_SECONDS = 20


def _coerce_args(payload) -> list[str]:
    if isinstance(payload, list):
        return [str(a) for a in payload]
    if isinstance(payload, str):
        return payload.split()
    return []


def run(plan: dict) -> str:
    if not shutil.which("git"):
        return "❌ git is not installed in this environment."

    args = _coerce_args(plan.get("args"))
    if not args and plan.get("command"):
        args = _coerce_args(plan["command"])
    if not args:
        args = ["status"]

    cwd = os.environ.get("OMX_TARGET_PATH") or os.getcwd()
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"⏳ git timed out after {TIMEOUT_SECONDS}s."
    except Exception as exc:
        return f"❌ git error: {exc}"

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return f"❌ git exit {result.returncode}: {output or '(no output)'}"
    return output or "(no output)"
