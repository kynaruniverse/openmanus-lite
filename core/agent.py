"""High-level agent orchestration.

Two modes:
  * react (default): one-step-at-a-time ReAct loop.
  * one-shot: legacy upfront planner followed by a synthesis pass.

Both modes share the same tool registry, executor, cache, and budget. Both
optionally emit progress events through ``on_event(dict)`` so a UI can stream
the agent's thoughts and tool outputs in real time.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Optional

from core import memory, plugins
from core.config import Config
from core.executor import Executor, StepResult, summarise
from core.llm import BudgetExceeded, LLMClient, LLMError
from core.logging_setup import get_logger
from core.planner import PlanError, Planner
from core.providers import make_provider
from core.react import ReActLoop


EventCallback = Optional[Callable[[dict], None]]


@dataclass
class AgentResult:
    ok: bool
    summary: str
    cached: bool = False
    llm_calls: int = 0


class Agent:
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
        provider = make_provider(
            config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
        )
        self._llm = LLMClient(provider=provider, max_calls=budget)
        self._planner = Planner(self._llm)
        self._executor = Executor(plugins.TOOLS, max_steps=config.max_steps)
        self._react = ReActLoop(self._llm, self._executor, max_steps=config.max_steps)

    @property
    def provider(self) -> str:
        return self._config.provider

    @property
    def model(self) -> str:
        return self._config.model

    def run_task(
        self,
        task: str,
        target_path: Optional[str] = None,
        use_cache: bool = True,
        on_event: EventCallback = None,
    ) -> AgentResult:
        task = (task or "").strip()
        if not task:
            return AgentResult(ok=False, summary="No task provided.")

        target = self._resolve_target(target_path)
        os.environ["OMX_TARGET_PATH"] = target
        self._log.info("Task target: %s | provider=%s | model=%s | mode=%s",
                       target, self._config.provider, self._config.model, self._mode)

        if on_event:
            on_event({"type": "start", "task": task, "target": target,
                      "provider": self._config.provider, "model": self._config.model,
                      "mode": self._mode})

        self._llm.reset_budget()

        if self._cache_enabled and use_cache:
            cached = memory.find(task, ttl_seconds=self._config.cache_ttl)
            if cached:
                if on_event:
                    on_event({"type": "cache_hit", "answer": cached})
                return AgentResult(ok=True, summary=cached, cached=True)

        try:
            if self._mode == "one-shot":
                result = self._run_one_shot(task, on_event)
            else:
                result = self._run_react(task, on_event)
        except BudgetExceeded as exc:
            if on_event:
                on_event({"type": "error", "message": str(exc)})
            return AgentResult(ok=False, summary=str(exc),
                               llm_calls=self._llm.call_count)
        except LLMError as exc:
            if on_event:
                on_event({"type": "error", "message": str(exc)})
            return AgentResult(ok=False, summary=str(exc),
                               llm_calls=self._llm.call_count)

        if result.ok and self._cache_enabled:
            memory.add(task, result.summary)

        if on_event:
            on_event({"type": "done", "ok": result.ok, "summary": result.summary,
                      "llm_calls": self._llm.call_count})
        return AgentResult(ok=result.ok, summary=result.summary,
                           llm_calls=self._llm.call_count)

    def _run_react(self, task: str, on_event: EventCallback) -> AgentResult:
        outcome = self._react.run(task, on_event=on_event)
        return AgentResult(ok=outcome.ok, summary=outcome.answer)

    def _run_one_shot(self, task: str, on_event: EventCallback) -> AgentResult:
        try:
            plan = self._planner.plan(task)
        except (LLMError, PlanError) as exc:
            return AgentResult(ok=False, summary=str(exc))

        if on_event:
            for i, step in enumerate(plan.steps, 1):
                on_event({"type": "planned_step", "n": i, "action": step.action,
                          "params": step.params})

        results: list[StepResult] = []
        for i, step in enumerate(plan.steps[: self._config.max_steps], 1):
            if on_event:
                on_event({"type": "thought", "n": i, "text": "",
                          "action": step.action, "params": step.params})
            output = self._executor.run_step(step)
            ok = not output.lstrip().startswith(("❌", "🛡️", "BLOCKED", "INVALID"))
            if on_event:
                on_event({"type": "observation", "n": i, "content": output,
                          "ok": ok, "action": step.action})
            results.append(StepResult(step=step, output=output, ok=ok))
            if not ok:
                break

        all_ok = bool(results) and all(r.ok for r in results)

        if (
            self._synthesise and all_ok and len(results) >= 2
            and results[-1].step.action == "answer"
        ):
            try:
                synthesised = self._synthesise_answer(task, results[:-1])
                results[-1] = StepResult(
                    step=results[-1].step, output=synthesised, ok=True
                )
                if on_event:
                    on_event({"type": "finish", "answer": synthesised})
            except LLMError as exc:
                self._log.warning("Answer synthesis skipped: %s", exc)

        return AgentResult(ok=all_ok, summary=summarise(results))

    def _synthesise_answer(self, task: str, prior: list[StepResult]) -> str:
        evidence_parts = [
            f"[step {i}: {r.step.action}]\n{r.output.strip()}"
            for i, r in enumerate(prior, 1)
        ]
        evidence = "\n\n".join(evidence_parts) or "(no prior output)"
        prompt = (
            "You are answering the user's request using the data collected by "
            "the tools. Write a concise, factual answer in plain prose. Do NOT "
            "use placeholders. Do NOT output JSON. Quote concrete details from "
            "the evidence when useful.\n\n"
            f"User task: {task}\n\nEvidence:\n{evidence}\n\nAnswer:"
        )
        return self._llm.generate(prompt).strip()

    def _resolve_target(self, target_path: Optional[str]) -> str:
        if target_path:
            target = os.path.abspath(target_path)
        else:
            target = os.path.abspath(self._config.workspace_dir)
        os.makedirs(target, exist_ok=True)
        return target
