"""Evaluate small Python snippets in a sandboxed subprocess.

Runs in a fresh ``python -c`` subprocess so it cannot mutate the agent's
process state. Constrained by a wall-clock timeout and an output cap.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap

TIMEOUT_SECONDS = 10
MAX_OUTPUT = 8000


def run(args: dict) -> str:
    code = args.get("code")
    if not code or not isinstance(code, str):
        return "❌ python tool: missing 'code' parameter."

    # Block the same destructive patterns the shell tool refuses, just in case.
    lowered = code.lower()
    for needle in ("os.system(", "subprocess.run(['rm'", "shutil.rmtree('/'"):
        if needle in lowered:
            return f"BLOCKED: refusing to execute snippet containing {needle!r}."

    cwd = os.environ.get("OMX_TARGET_PATH") or os.getcwd()
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", textwrap.dedent(code)],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"⏳ python tool: snippet timed out after {TIMEOUT_SECONDS}s."
    except Exception as exc:
        return f"❌ python tool error: {exc}"

    output = (completed.stdout + completed.stderr).strip()
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + f"\n…[truncated, {len(output) - MAX_OUTPUT} bytes more]"

    if completed.returncode != 0:
        return f"❌ python exit {completed.returncode}: {output or '(no output)'}"
    return output or "(no output)"
