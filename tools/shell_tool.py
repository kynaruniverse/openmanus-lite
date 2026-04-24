"""Run shell commands inside the active target directory."""
from __future__ import annotations

import os
import shlex
import subprocess

FORBIDDEN = (
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){:|:&};:",
    "> /dev/sda", "> /dev/nvme", "shutdown", "reboot",
    "chmod -R 000", "chown -R root",
)
TIMEOUT_SECONDS = 30
MAX_OUTPUT = 8000
SHELL_METACHARS = ("|", ">", "<", "&&", "||", ";", "$(", "`", "*", "?")


def run(plan: dict) -> str:
    action = (plan.get("action") or plan.get("type") or "").lower()
    if action == "ls" and not plan.get("command"):
        cmd_str = "ls -la"
    else:
        cmd_str = (plan.get("command") or "").strip()

    if not cmd_str:
        return "❌ shell tool: no command provided."

    if any(bad in cmd_str for bad in FORBIDDEN):
        return f"BLOCKED: refusing to run destructive command: {cmd_str}"

    cwd = os.environ.get("OMX_TARGET_PATH") or os.getcwd()
    use_shell = any(meta in cmd_str for meta in SHELL_METACHARS)

    try:
        if use_shell:
            # Pipes / redirects / globs etc. — run through bash -c.
            completed = subprocess.run(
                ["bash", "-c", cmd_str],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        else:
            try:
                args = shlex.split(cmd_str)
            except ValueError as exc:
                return f"❌ shell tool: could not parse command ({exc})."
            completed = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
    except FileNotFoundError as exc:
        return f"❌ shell tool: command not found ({exc})."
    except subprocess.TimeoutExpired:
        return f"⏳ shell tool: command timed out after {TIMEOUT_SECONDS}s."
    except Exception as exc:
        return f"❌ shell tool error: {exc}"

    output = (completed.stdout + completed.stderr).strip()
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + f"\n…[truncated, {len(output) - MAX_OUTPUT} bytes more]"

    if completed.returncode != 0:
        return f"❌ exit {completed.returncode}: {output}"
    return output or "(no output)"
