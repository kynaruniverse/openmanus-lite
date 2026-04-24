"""Command-line interface for OpenManus-Lite."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from core.agent import Agent
from core.config import Config, ConfigError
from core.logging_setup import setup_logging
from core.providers import PROVIDERS


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omx",
        description="OpenManus-Lite: a mobile-first AI developer agent.",
    )
    p.add_argument("--task", type=str, help="Run a single task and exit.")
    p.add_argument("--path", type=str, default=None,
                   help="Target project directory. Defaults to ./workspace.")
    p.add_argument("--provider", choices=PROVIDERS, default=None,
                   help="LLM provider (default: $OMX_PROVIDER or gemini).")
    p.add_argument("--model", type=str, default=None,
                   help="Override the model id for the chosen provider.")
    p.add_argument("--mode", choices=("react", "one-shot"), default="react",
                   help="Agent loop: react (default) or one-shot legacy planner.")
    p.add_argument("--budget", type=int, default=None,
                   help="Hard cap on LLM calls per task.")
    p.add_argument("--cache", choices=("on", "off"), default="on",
                   help="Disable the cache entirely (no reads or writes).")
    p.add_argument("--no-cache", action="store_true",
                   help="Ignore the cache for this run only.")
    p.add_argument("--no-synthesis", action="store_true",
                   help="Skip the second LLM pass in one-shot mode.")
    p.add_argument("--web", action="store_true",
                   help="Launch the web UI instead of the CLI.")
    p.add_argument("--host", default="0.0.0.0",
                   help="Web server bind host (only with --web). Default 0.0.0.0.")
    p.add_argument("--port", type=int, default=5000,
                   help="Web server port (only with --web). Default 5000.")
    p.add_argument("--debug", action="store_true",
                   help="Verbose console logging.")
    return p


SHORTCUTS = {"1": "list files", "2": "git status", "3": "help"}

BANNER = (
    "🌟 OpenManus-Lite — interactive shell.\n"
    "   Type a task in plain English, or use shortcuts: 1=list files, "
    "2=git status, 3=help.\n"
    "   Type 'exit' / 'quit' / 'q' to leave.\n"
)


def _print_result(result, mode: str, provider: str) -> None:
    prefix = "🚀 [CACHED]" if result.cached else ("✅" if result.ok else "❌")
    print(f"\n{prefix} ({result.llm_calls} LLM call(s) · {provider} · mode={mode})")
    print(result.summary.rstrip())
    print()


def _interactive(agent: Agent, target_path, use_cache, mode) -> int:
    print(BANNER)
    print(f"   Provider: {agent.provider} · model: {agent.model}\n")
    while True:
        try:
            user = input("OMX > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        user = SHORTCUTS.get(user, user)
        if not user:
            continue
        if user.lower() in {"exit", "quit", "q"}:
            return 0
        result = agent.run_task(user, target_path=target_path, use_cache=use_cache)
        _print_result(result, mode, agent.provider)


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    # CLI overrides for env-driven config.
    if args.provider:
        os.environ["OMX_PROVIDER"] = args.provider
    if args.model:
        os.environ["OMX_MODEL"] = args.model

    if args.web:
        # Defer config errors to the request handler so the UI can render them.
        log_level = "DEBUG" if args.debug else os.environ.get("OMX_LOG_LEVEL", "INFO")
        setup_logging(level=log_level, log_file=os.environ.get("OMX_LOG_FILE", "omx.log"))
        from web.server import serve
        serve(host=args.host, port=args.port)
        return 0

    try:
        config = Config.from_env()
    except ConfigError as exc:
        print(f"❌ Configuration error:\n{exc}", file=sys.stderr)
        return 2

    log_level = "DEBUG" if args.debug else config.log_level
    setup_logging(level=log_level, log_file=config.log_file)

    budget = args.budget if args.budget is not None else _int_env_default("OMX_BUDGET", 0)

    agent = Agent(
        config=config,
        mode=args.mode,
        synthesise=not args.no_synthesis,
        budget=budget,
        cache_enabled=(args.cache == "on"),
    )
    use_cache = (not args.no_cache) and args.cache == "on"

    if args.task:
        result = agent.run_task(args.task, target_path=args.path, use_cache=use_cache)
        _print_result(result, args.mode, agent.provider)
        return 0 if result.ok else 1

    return _interactive(agent, args.path, use_cache, args.mode)


def _int_env_default(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def run_from_cli() -> None:
    sys.exit(main())


def run_web() -> None:
    """Console-script entry point: ``omx-web``."""
    sys.exit(main(["--web"] + sys.argv[1:]))
