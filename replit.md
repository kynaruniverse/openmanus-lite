# OpenManus-Lite

A terminal-based AI developer agent powered by Google Gemini. Pure Python CLI —
no web server, no frontend.

## Project type

- Language: Python 3.12
- Entry points:
  - `python main.py …`
  - `omx …` (installed by `pip install -e .` via `setup.py`)

## Layout

```
core/
  cli.py            argparse + interactive shell
  agent.py          orchestrator: chooses react / one-shot, manages cache + budget
  llm.py            Gemini client wrapper (streaming, retries, hard call budget)
  react.py          ReAct loop: think → act → observe → repeat
  planner.py        legacy one-shot prompt + JSON plan parser (still used in --mode one-shot)
  executor.py       dispatches a single Step or full Plan to the tool registry
  memory.py         normalised cache with optional TTL, opt-out flag
  plugins.py        loads tools/*_tool.py at startup
  config.py         env-driven config (fails fast on missing key)
  logging_setup.py  shared "omx" logger (console + rotating file)
  main.py           thin shim exporting cli.run_from_cli for back-compat
tools/
  file_tool.py      sandboxed read / write inside the target directory
  shell_tool.py     shell exec with destructive-command blocklist; pipes/redirects via bash -c
  git_tool.py       arbitrary git subcommands (status, log, diff, …)
  python_tool.py    sandboxed `python -c` snippet evaluation (10s timeout)
  search_tool.py    DuckDuckGo web search (no API key required)
tests/
  test_basic.py        offline unit tests for planner + tools
  test_integration.py  end-to-end ReAct tests with a stub LLM (no network)
main.py             top-level launcher
```

## Required configuration

- `GEMINI_API_KEY` — set as a Replit Secret (preferred) or in a local `.env`.

The committed `.env` (which contained a leaked key) was deleted; `.env.example`
documents the schema. If `GEMINI_API_KEY` is missing the program exits with a
clear error (exit code 2).

### Optional environment variables

| name              | default                     | meaning                              |
|-------------------|-----------------------------|--------------------------------------|
| `OMX_MODEL`       | `models/gemini-2.5-flash-lite` | Gemini model id                   |
| `OMX_LOG_LEVEL`   | `INFO`                      | DEBUG / INFO / WARNING / ERROR       |
| `OMX_LOG_FILE`    | `omx.log`                   | log destination                      |
| `OMX_BUDGET`      | `0` (unlimited)             | hard cap on LLM calls per task       |
| `OMX_CACHE_TTL`   | `0` (no expiry)             | cache entry lifetime in seconds      |
| `OMX_MAX_STEPS`   | `10`                        | max iterations per task              |
| `OMX_WORKSPACE`   | `workspace`                 | default working directory            |

## CLI flags

```
--task "…"            run one task and exit (otherwise interactive)
--path PATH           target project directory (defaults to OMX_WORKSPACE)
--mode {react,one-shot}   loop mode (default: react)
--budget N            hard cap on LLM calls per task
--cache {on,off}      disable cache reads + writes entirely
--no-cache            ignore cache for this run only
--no-synthesis        skip the second LLM call in one-shot mode
--debug               verbose logging
```

## Workflow

A console workflow named **OpenManus CLI** runs `python main.py --help` to
verify the CLI is wired correctly without burning API quota on every restart.
Real tasks should be run from the shell, e.g.:

```bash
python main.py --task "count the python files in this repo" --path .
python main.py --task "what year was python released?"           # uses search
python main.py --mode one-shot --task "show git status"
python main.py                                                   # interactive
```

## Validation

End-to-end runs verified against the live Gemini API:

- ReAct + python tool — computed `fib(12)=144` in 3 LLM calls.
- ReAct + search tool — answered "Python first released in 1991" via DuckDuckGo.
- ReAct + shell with pipes — `git ls-files | grep \.py$ | wc -l` works via bash.
- Budget enforcement — `--budget 2` halts the agent at exactly 2 calls.
- One-shot mode — legacy planner + synthesis still produces real prose.

`pytest -v` runs **14 tests** (8 offline unit + 6 integration tests that drive
the full ReAct loop with a stub LLM).

## Production-ready improvements (this round)

1. **Reactive ReAct loop** is now the default — plans one step at a time,
   feeds tool observations back into the next prompt, recovers from bad JSON.
2. **Cache** keys are normalised (lowercased, punctuation-stripped) and
   support a TTL. `--cache off` disables it entirely.
3. **Streaming** is exposed via `LLMClient.stream()` and used by debug logs;
   the same call-counting and budget apply to streamed and non-streamed calls.
4. **Cost guardrail**: `--budget N` (or `OMX_BUDGET`) enforces a hard cap on
   LLM calls per task. `--no-synthesis` skips the second pass in one-shot mode.
5. **New tools**: `python` (sandboxed snippet eval) and `search` (DuckDuckGo).
   `git diff` works through the existing git tool.
6. **Integration tests** exercise the ReAct loop end-to-end with a stub LLM,
   including JSON-recovery, multi-step file round trip, and budget exhaustion.

## Pushing to GitHub

The main agent cannot push to GitHub directly. Use Replit's **Git** pane in
the workspace to commit and push, or run `git push origin main` from a shell
after making sure your GitHub PAT has the `workflow` scope.
