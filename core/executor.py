"""Execute a ``Plan`` (one-shot mode) or single ``Step`` (ReAct mode)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from core.logging_setup import get_logger
from core.planner import Plan, Step


ToolFn = Callable[[dict], str]


@dataclass
class StepResult:
    step: Step
    output: str
    ok: bool


# Action -> tool registry name (filename minus _tool.py).
ACTION_ALIASES = {
    "shell": "shell",
    "ls": "shell",
    "git": "git",
    "file_read": "file",
    "file_write": "file",
    "read": "file",
    "write": "file",
    "python": "python",
    "search": "search",
}


class Executor:
    def __init__(self, tools: Dict[str, ToolFn], max_steps: int = 10) -> None:
        self._tools = tools
        self._max_steps = max_steps
        self._log = get_logger()

    # --- one-shot plan execution ---------------------------------------------
    def run(self, plan: Plan) -> List[StepResult]:
        results: List[StepResult] = []
        for i, step in enumerate(plan.steps[: self._max_steps], start=1):
            self._log.info("→ Step %d/%d: %s", i, len(plan.steps), step.action)
            output = self.run_step(step)
            ok = not output.lstrip().startswith(
                ("❌", "🛡️", "BLOCKED", "INVALID")
            )
            self._log.info(
                "← Step %d %s: %s",
                i, "OK" if ok else "FAIL",
                output[:200].replace("\n", " "),
            )
            results.append(StepResult(step=step, output=output, ok=ok))
            if not ok:
                break
        return results

    # --- single-step execution (used by ReAct loop) --------------------------
    def run_step(self, step: Step) -> str:
        action = step.action.lower()

        if action == "answer":
            return str(step.params.get("text", "")).strip() or "(no answer provided)"

        tool_name = ACTION_ALIASES.get(action, action)
        tool = self._tools.get(tool_name)
        if tool is None:
            return f"❌ Unknown action: {step.action!r} (no tool registered)"

        normalised = dict(step.params)
        normalised.setdefault("action", action.replace("file_", ""))
        normalised.setdefault("type", normalised["action"])
        try:
            return tool(normalised)
        except Exception as exc:
            self._log.exception("Tool %s crashed", tool_name)
            return f"❌ Internal error in '{step.action}': {exc}"


def summarise(results: List[StepResult]) -> str:
    if not results:
        return "(no steps were executed)"
    parts: List[str] = []
    for i, r in enumerate(results, 1):
        marker = "✅" if r.ok else "❌"
        parts.append(f"{marker} step {i}: {r.step.action}\n{r.output.rstrip()}")
    return "\n\n".join(parts)
