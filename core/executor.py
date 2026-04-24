"""Execute a ``Plan`` by dispatching each step to the registered tools."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from core.logging_setup import get_logger
from core.planner import Plan, Step


ToolFn = Callable[[Step], str]


@dataclass
class StepResult:
    step: Step
    output: str
    ok: bool


# Action -> (tool module name, normalised step kwargs)
# Actions are routed to tools by mapping their name to a tool's `run`.
ACTION_ALIASES = {
    # canonical -> tool name
    "shell": "shell",
    "ls": "shell",
    "git": "git",
    "file_read": "file",
    "file_write": "file",
    "read": "file",
    "write": "file",
}


class Executor:
    def __init__(self, tools: Dict[str, ToolFn], max_steps: int = 10) -> None:
        self._tools = tools
        self._max_steps = max_steps
        self._log = get_logger()

    def run(self, plan: Plan) -> List[StepResult]:
        results: List[StepResult] = []
        for i, step in enumerate(plan.steps[: self._max_steps], start=1):
            self._log.info("→ Step %d/%d: %s", i, len(plan.steps), step.action)
            try:
                output = self._dispatch(step)
                ok = not output.lstrip().startswith(("❌", "🛡️", "BLOCKED", "INVALID"))
            except Exception as exc:  # tool crashed unexpectedly
                self._log.exception("Step %d crashed", i)
                output = f"❌ Internal error in '{step.action}': {exc}"
                ok = False

            self._log.info("← Step %d %s: %s", i, "OK" if ok else "FAIL",
                           output[:200].replace("\n", " "))
            results.append(StepResult(step=step, output=output, ok=ok))

            if not ok:
                break
        return results

    def _dispatch(self, step: Step) -> str:
        action = step.action.lower()

        if action == "answer":
            return step.params.get("text", "").strip() or "(no answer provided)"

        tool_name = ACTION_ALIASES.get(action, action)
        tool = self._tools.get(tool_name)
        if tool is None:
            return f"❌ Unknown action: {step.action!r} (no tool registered)"

        # Build the dict the tool's run() expects. Tools historically read
        # several keys (action, type, command, file, content, args). Pass
        # everything we know and include the canonical action name.
        normalised = dict(step.params)
        normalised.setdefault("action", action.replace("file_", ""))  # write/read
        normalised.setdefault("type", normalised["action"])
        return tool(normalised)


def summarise(results: List[StepResult]) -> str:
    """Return a human-readable summary of step outputs for the CLI."""
    if not results:
        return "(no steps were executed)"
    parts: List[str] = []
    for i, r in enumerate(results, 1):
        marker = "✅" if r.ok else "❌"
        header = f"{marker} step {i}: {r.step.action}"
        body = r.output.rstrip()
        parts.append(f"{header}\n{body}")
    return "\n\n".join(parts)
