import json
import os
from agent.safety import run_safe
from agent.approval import require_approval
from agent.validator import validate_plan

REPO_PATH = os.getcwd()


def parse_plan(raw):
    """
    Gemini sometimes returns JSON wrapped in text.
    We try to safely extract it.
    """
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"actions": []}


def execute(plan_raw):
    plan = parse_plan(plan_raw)

    ok, reason = validate_plan(plan)
    if not ok:
        return f"BLOCKED PLAN: {reason}"

    results = []

    for action in plan.get("actions", []):
        t = action.get("type")

        # WRITE FILE
        if t == "write":
            path = action.get("path")
            content = action.get("content", "")

            full_path = os.path.join(REPO_PATH, path)

            if full_path and os.path.dirname(full_path):
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w") as f:
                f.write(content)

            results.append(f"WROTE: {path}")

        # SHELL COMMAND
        elif t == "shell":
            cmd = action.get("command", "")

            if require_approval("shell", cmd):
                out = run_safe(cmd)
            else:
                out = "BLOCKED: requires approval"

            results.append(str(out))

        # GIT COMMAND
        elif t == "git":
            cmd = action.get("command", "")

            if require_approval("git", cmd):
                out = run_safe("git " + cmd)
            else:
                out = "BLOCKED: git action requires approval"

            results.append(str(out))

        # READ FILE
        elif t == "read":
            path = action.get("path", "")

            try:
                with open(path, "r") as f:
                    results.append(f.read())
            except Exception:
                results.append(f"FAILED READ: {path}")

    return "\n".join(results)
