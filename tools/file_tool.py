"""Read and write files inside the active target directory."""
from __future__ import annotations

import os


def _get_workspace() -> str:
    return os.environ.get("OMX_TARGET_PATH") or os.path.abspath("workspace")


def _safe_join(workspace: str, filename: str) -> str | None:
    """Return an absolute path under ``workspace`` or ``None`` if it escapes."""
    workspace_abs = os.path.realpath(workspace)
    candidate = os.path.realpath(os.path.join(workspace_abs, filename))
    try:
        common = os.path.commonpath([workspace_abs, candidate])
    except ValueError:
        return None
    if common != workspace_abs:
        return None
    return candidate


def run(args: dict) -> str:
    workspace = _get_workspace()
    action = (args.get("action") or args.get("type") or "").lower()
    # Normalise the canonical action names used by the planner.
    if action in {"file_read"}:
        action = "read"
    elif action in {"file_write"}:
        action = "write"

    filename = (args.get("file") or "").strip()
    if not filename:
        return "❌ file tool: missing 'file' parameter."

    target = _safe_join(workspace, filename)
    if target is None:
        return f"🛡️ Security block: '{filename}' escapes the target directory."

    if action == "write":
        try:
            os.makedirs(os.path.dirname(target) or workspace, exist_ok=True)
            content = args.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"SUCCESS: wrote {len(content)} chars to {filename}"
        except OSError as exc:
            return f"❌ file write error: {exc}"

    if action == "read":
        if not os.path.exists(target):
            return f"🔍 file not found: {filename}"
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError as exc:
            return f"❌ file read error: {exc}"

    return f"❌ file tool: unknown action {action!r}"
