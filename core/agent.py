"""High-level agent orchestration: plan → execute → summarise."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from core import memory, plugins
from core.config import Config
from core.executor import Executor, summarise
from core.llm import LLMClient, LLMError
from core.logging_setup import get_logger
from core.planner import PlanError, Planner


@dataclass
class AgentResult:
    ok: bool
    summary: str
    cached: bool = False


class Agent:
    """End-to-end orchestrator. Stateless across runs apart from the cache."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._log = get_logger()
        plugins.load()
        self._llm = LLMClient(api_key=config.api_key, model=config.model)
        self._planner = Planner(self._llm)
        self._executor = Executor(plugins.TOOLS, max_steps=config.max_steps)

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
        self._log.info("Task target directory: %s", target)

        if use_cache:
            cached = memory.find(task)
            if cached:
                self._log.info("Cache hit for task: %s", task)
                return AgentResult(ok=True, summary=cached, cached=True)

        try:
            plan = self._planner.plan(task)
        except (LLMError, PlanError) as exc:
            return AgentResult(ok=False, summary=str(exc))

        results = self._executor.run(plan)
        summary = summarise(results)
        all_ok = bool(results) and all(r.ok for r in results)

        if all_ok:
            memory.add(task, summary)
        return AgentResult(ok=all_ok, summary=summary)

    def _resolve_target(self, target_path: Optional[str]) -> str:
        if target_path:
            target = os.path.abspath(target_path)
        else:
            target = os.path.abspath(self._config.workspace_dir)
        os.makedirs(target, exist_ok=True)
        return target
