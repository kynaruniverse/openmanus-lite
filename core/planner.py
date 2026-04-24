"""Turn a natural-language task into a structured ``Plan`` of tool actions."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from core.llm import LLMClient, LLMError
from core.logging_setup import get_logger


class PlanError(RuntimeError):
    """Raised when the LLM output cannot be parsed into a valid plan."""


@dataclass
class Step:
    action: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    thought: str
    steps: List[Step]


SYSTEM_PROMPT = """\
You are OpenManus-Lite, an autonomous coding agent. You translate a user's
request into a JSON plan that the executor will run. Output ONLY valid JSON
matching this schema (no prose, no markdown fences):

{
  "thought": "<one short sentence explaining your approach>",
  "steps": [
    { "action": "<action_name>", ... action-specific fields ... }
  ]
}

Available actions:

- shell:      run a shell command in the target directory.
              Fields: { "command": "<string>" }
              Examples: list files, run tests, count lines.

- file_read:  read a text file relative to the target directory.
              Fields: { "file": "<relative path>" }

- file_write: create or overwrite a text file relative to the target directory.
              Fields: { "file": "<relative path>", "content": "<full file content>" }

- git:        run a git subcommand (no need to prefix with "git").
              Fields: { "args": ["status"] }   or   { "args": ["log", "-n", "5"] }

- answer:     respond directly to the user without running tools.
              Fields: { "text": "<your answer>" }

Rules:
1. Always emit valid JSON. No code fences. No commentary outside JSON.
2. Prefer the smallest plan that fully satisfies the task.
3. For "list files" or directory inspection, use a single shell step like `ls -la`.
4. For "analyze this repository", use a few shell/file_read steps to inspect the
   tree, then summarise via an `answer` step at the end.
5. Never use destructive shell commands (rm -rf /, mkfs, dd if=, etc.).
6. Paths must be relative to the target directory.

User task: {task}
"""


def _extract_json(text: str) -> str:
    """Pull a JSON object out of an LLM response that may wrap it in fences."""
    # Strip common code fences
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # If there's still surrounding prose, find the outermost {...}
    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            cleaned = match.group(0)
    return cleaned.strip()


def _parse_plan(raw: str) -> Plan:
    payload = _extract_json(raw)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise PlanError(
            f"Model did not return valid JSON: {exc}. Raw response:\n{raw}"
        ) from exc

    if not isinstance(data, dict):
        raise PlanError(f"Plan JSON must be an object, got {type(data).__name__}")

    # Backwards-compat: allow a single-step shorthand like {"type": "write", ...}
    if "steps" not in data and ("action" in data or "type" in data):
        data = {"thought": data.get("thought", ""), "steps": [data]}

    thought = str(data.get("thought", "")).strip()
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise PlanError("Plan must contain a non-empty 'steps' array.")

    steps: List[Step] = []
    for i, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise PlanError(f"Step #{i} is not an object: {raw_step!r}")
        action = raw_step.get("action") or raw_step.get("type")
        if not action:
            raise PlanError(f"Step #{i} is missing an 'action' field.")
        params = {k: v for k, v in raw_step.items() if k not in ("action", "type")}
        steps.append(Step(action=str(action), params=params))

    return Plan(thought=thought, steps=steps)


class Planner:
    """Builds prompts and parses model output into a ``Plan``."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self._log = get_logger()

    def plan(self, task: str) -> Plan:
        prompt = SYSTEM_PROMPT.replace("{task}", task)
        self._log.info("Planning task: %s", task)
        raw = self._llm.generate(prompt)
        try:
            plan = _parse_plan(raw)
        except PlanError as exc:
            self._log.error("Plan parse failed: %s", exc)
            raise
        self._log.info("Plan: %s (%d steps)", plan.thought, len(plan.steps))
        for i, step in enumerate(plan.steps, 1):
            self._log.debug("  step %d: %s %s", i, step.action, step.params)
        return plan
