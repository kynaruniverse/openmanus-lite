"""High-level agent orchestration.

Two modes:

- **react** (default): ReAct loop — think one step, act, observe, repeat.
- **one-shot**: legacy planner that emits the whole plan in one LLM call,
  followed by a synthesis pass to fill in the final answer.

Both modes share the same tool registry, executor, cache, and budget.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from core import memory, plugins
from core.config import Config
from core.executor import Executor, StepResult, summarise
from core.llm import BudgetExceeded, LLMClient, LLMError
from core.logging_setup import get_logger
from core.planner import PlanError, Planner
from core.react import ReActLoop, Trace


@dataclass
class AgentResult:
    ok: bool
    summary: str
    cached: bool = False
    llm_calls: int = 0


class Agent:
    """End-to-end orchestrator. Stateless apart from the optional cache."""

    def __init__(
        self,
        config: Config,
        mode: str = "react",
        synthesise: bool = True,
        budget: int = 0,
        cache_enabled: bool = True,
    ) -> None:
        self._config = config
        self._mode = mode
        self._synthesise = synthesise
        self._cache_enabled = cache_enabled
        self._log = get_logger()

        plugins.load()
        self._llm = LLMClient(
            api_key=config.api_key,
            model=config.model,
            max_calls=budget,
        )
        self._planner = Planner(self._llm)
        self._executor = Executor(plugins.TOOLS, max_steps=config.max_steps)
        self._react = ReActLoop(self._llm, self._executor, max_steps=config.max_steps)

    # ------------------------------------------------------------------ entry
    def run_task(
        self,
        task: str,
        target_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> AgentResult:
        task = (task or "").strip()
        if not task:
            return AgentResult(ok=False, summary="No task provided.")

        target = self._resolve_target(target_path)
        os.environ["OMX_TARGET_PATH"] = target
        self._log.info("Task target directory: %s | mode=%s", target, self._mode)

        # Reset per-task budget counter.
        self._llm.reset_budget()

        if self._cache_enabled and use_cache:
            cached = memory.find(task, ttl_seconds=self._config.cache_ttl)
            if cached:
                self._log.info("Cache hit.")
                return AgentResult(ok=True, summary=cached, cached=True)

        try:
            if self._mode == "one-shot":
                result = self._run_one_shot(task)
            else:
                result = self._run_react(task)
        except BudgetExceeded as exc:
            return AgentResult(
                ok=False, summary=str(exc), llm_calls=self._llm.call_count
            )
        except LLMError as exc:
            return AgentResult(
                ok=False, summary=str(exc), llm_calls=self._llm.call_count
            )

        if result.ok and self._cache_enabled:
            memory.add(task, result.summary)

        return AgentResult(
            ok=result.ok, summary=result.summary, llm_calls=self._llm.call_count
        )

    # ------------------------------------------------------------------ react
    def _run_react(self, task: str) -> AgentResult:
        outcome = self._react.run(task)
        return AgentResult(ok=outcome.ok, summary=outcome.answer)

    # --------------------------------------------------------------- one-shot
    def _run_one_shot(self, task: str) -> AgentResult:
        try:
            plan = self._planner.plan(task)
        except (LLMError, PlanError) as exc:
            return AgentResult(ok=False, summary=str(exc))

        results = self._executor.run(plan)
        all_ok = bool(results) and all(r.ok for r in results)

        if (
            self._synthesise
            and all_ok
            and len(results) >= 2
            and results[-1].step.action == "answer"
        ):
            try:
                synthesised = self._synthesise_answer(task, results[:-1])
                results[-1] = StepResult(
                    step=results[-1].step, output=synthesised, ok=True
                )
            except LLMError as exc:
                self._log.warning("Answer synthesis skipped: %s", exc)

        summary = summarise(results)
        return AgentResult(ok=all_ok, summary=summary)

    def _synthesise_answer(self, task: str, prior: list[StepResult]) -> str:
        evidence_parts = []
        for i, r in enumerate(prior, 1):
            evidence_parts.append(
                f"[step {i}: {r.step.action}]\n{r.output.strip()}"
            )
        evidence = "\n\n".join(evidence_parts) or "(no prior output)"
        prompt = (
            "You are answering the user's request using the data collected by "
            "the tools. Write a concise, factual answer in plain prose. "
            "Do NOT use placeholders like {{...}}. Do NOT output JSON. "
            "Quote concrete details from the evidence when useful.\n\n"
            f"User task: {task}\n\n"
            f"Evidence:\n{evidence}\n\nAnswer:"
        )
        self._log.info("Synthesising final answer from %d prior step(s)", len(prior))
        return self._llm.generate(prompt).strip()

    # ------------------------------------------------------------------ utils
    def _resolve_target(self, target_path: Optional[str]) -> str:
        if target_path:
            target = os.path.abspath(target_path)
        else:
            target = os.path.abspath(self._config.workspace_dir)
        os.makedirs(target, exist_ok=True)
        return target
