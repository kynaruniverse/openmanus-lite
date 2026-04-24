"""ReAct-style reasoning loop with optional event streaming."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from core.executor import Executor
from core.llm import BudgetExceeded, LLMClient, LLMError
from core.logging_setup import get_logger
from core.planner import PlanError, Step, _parse_plan


EventCallback = Optional[Callable[[dict], None]]


@dataclass
class Trace:
    step: Step
    observation: str
    ok: bool


@dataclass
class ReActResult:
    ok: bool
    answer: str
    trace: List[Trace] = field(default_factory=list)
    finished: bool = False


SYSTEM_PROMPT = """\
You are OpenManus-Lite, an autonomous coding agent that solves the user's task
ONE STEP AT A TIME using a ReAct loop. After each action you take, you will
see its observation and decide the next action.

For each turn output ONLY a single JSON object (no prose, no markdown fences):

{
  "thought": "<one short sentence: what to do next and why>",
  "action": "<one of: shell, file_read, file_write, git, python, search, finish>",
  ...action-specific fields...
}

Action fields:
- shell:      {"command": "<shell command>"}
- file_read:  {"file": "<relative path>"}
- file_write: {"file": "<relative path>", "content": "<full file contents>"}
- git:        {"args": ["status"]}    or {"args": ["log", "-n", "5"]}    or {"args": ["diff"]}
- python:     {"code": "<python source to evaluate>"}
- search:     {"query": "<web search query>"}
- finish:     {"text": "<final answer for the user, in plain prose>"}

Rules:
1. Output exactly one JSON object per turn. Nothing else.
2. After each action you receive an "Observation". Use it before deciding the
   next step. Do NOT invent observations.
3. Use "finish" as soon as you can answer; do not pad with extra steps.
4. If an action fails, try a different approach. Do not repeat the exact same
   failing action.
5. Paths are relative to the target directory.
6. Never use destructive shell commands.

User task:
{task}

History so far:
{history}

Your next single-step JSON:
"""


def _format_history(traces: List[Trace]) -> str:
    if not traces:
        return "(none yet — this is your first action)"
    parts = []
    for i, t in enumerate(traces, 1):
        params = {k: v for k, v in t.step.params.items()}
        parts.append(
            f"Step {i}:\n"
            f"  Thought: {t.step.params.get('thought', '')}\n"
            f"  Action: {t.step.action} {params}\n"
            f"  Observation: {_truncate(t.observation, 1500)}"
        )
    return "\n\n".join(parts)


def _truncate(text: str, n: int) -> str:
    text = text.rstrip()
    if len(text) <= n:
        return text
    return text[:n] + f"\n…[truncated, {len(text) - n} bytes more]"


class ReActLoop:
    def __init__(self, llm: LLMClient, executor: Executor, max_steps: int = 10) -> None:
        self._llm = llm
        self._executor = executor
        self._max_steps = max_steps
        self._log = get_logger()

    def run(self, task: str, on_event: EventCallback = None) -> ReActResult:
        traces: List[Trace] = []
        last_error = ""

        def emit(ev: dict) -> None:
            if on_event:
                on_event(ev)

        for i in range(1, self._max_steps + 1):
            self._log.info("ReAct iter %d/%d", i, self._max_steps)
            emit({"type": "iter", "n": i, "max": self._max_steps})

            prompt = (
                SYSTEM_PROMPT
                .replace("{task}", task)
                .replace("{history}", _format_history(traces))
            )

            try:
                raw = self._llm.generate(prompt)
            except BudgetExceeded as exc:
                last_error = str(exc)
                emit({"type": "error", "message": last_error})
                break
            except LLMError as exc:
                last_error = str(exc)
                emit({"type": "error", "message": last_error})
                break

            try:
                step = self._parse_one_step(raw)
            except PlanError as exc:
                self._log.warning("Bad JSON from model: %s", exc)
                fake_step = Step(
                    action="answer",
                    params={"thought": "(unparseable model output)"},
                )
                traces.append(
                    Trace(
                        step=fake_step,
                        observation=f"❌ Your last response was not valid JSON: {exc}. "
                                    f"Reply again with a single JSON object.",
                        ok=False,
                    )
                )
                emit({"type": "parse_error", "raw": raw[:500], "error": str(exc)})
                continue

            emit({
                "type": "thought",
                "n": i,
                "text": step.params.get("thought", ""),
                "action": step.action,
                "params": {k: v for k, v in step.params.items() if k != "thought"},
            })

            if step.action == "finish":
                answer = str(step.params.get("text", "")).strip() or "(no answer text)"
                emit({"type": "finish", "answer": answer})
                return ReActResult(ok=True, answer=answer, trace=traces, finished=True)

            observation = self._executor.run_step(step)
            ok = not observation.lstrip().startswith(("❌", "🛡️", "BLOCKED", "INVALID"))
            emit({"type": "observation", "n": i, "content": observation,
                  "ok": ok, "action": step.action})
            traces.append(Trace(step=step, observation=observation, ok=ok))

        if last_error:
            return ReActResult(ok=False, answer=last_error, trace=traces)

        return ReActResult(
            ok=False,
            answer=(
                f"Step budget reached ({self._max_steps}) without a `finish` action. "
                f"Partial trace recorded."
            ),
            trace=traces,
        )

    @staticmethod
    def _parse_one_step(raw: str) -> Step:
        plan = _parse_plan(raw)
        if not plan.steps:
            raise PlanError("No step in model output.")
        first = plan.steps[0]
        if plan.thought and "thought" not in first.params:
            first.params["thought"] = plan.thought
        return first
