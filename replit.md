# OpenManus-Lite

A multi-provider AI developer agent with both a CLI and a web UI. Plain Python
on the inside, optional standalone-binary distribution via PyInstaller.

## Project type

- Language: Python 3.12
- Entry points:
  - `python main.py …`  (CLI)
  - `python main.py --web` or `python -m web.server` (web UI on port 5000)
  - `omx` and `omx-web` (after `pip install -e .`)

## Layout

```
core/
  cli.py            argparse + interactive shell + --web flag
  agent.py          orchestrator; emits per-step events for streaming UIs
  llm.py            Provider-agnostic LLM client (budget, streaming, errors)
  react.py          ReAct loop (think → act → observe) with on_event callback
  planner.py        Legacy one-shot prompt + JSON plan parser
  executor.py       Single-step or full-plan dispatch to tools
  memory.py         Normalised cache with optional TTL
  plugins.py        Loads tools/*_tool.py
  config.py         Multi-provider env-driven config
  logging_setup.py  Shared "omx" logger
  providers/        Pluggable LLM backends
    base.py            BaseProvider interface
    gemini.py          Google Gemini
    openai_provider.py OpenAI (also reused by openrouter)
    anthropic_provider.py Anthropic Claude
    ollama.py          Local LLMs via Ollama (no API key)
    openrouter.py      OpenRouter (one key → 100+ models)
tools/
  shell_tool.py     Shell exec; pipes/redirects via bash -c; destructive blocked
  file_tool.py      Sandboxed read/write
  git_tool.py       Arbitrary git subcommands
  python_tool.py    Sandboxed `python -c` snippet evaluation
  search_tool.py    DuckDuckGo web search
web/
  server.py         FastAPI server, SSE streaming of agent events
  static/
    index.html      Single-page chat UI
    style.css       Modern dark theme, responsive (works on phone)
    app.js          Vanilla JS — fetch + SSE parsing, no build step
    favicon.svg
tests/
  test_basic.py        Offline unit tests for planner + tools
  test_integration.py  End-to-end ReAct tests with a stub LLM
build_binary.py     PyInstaller config — ships a single-file binary
main.py             Top-level launcher
```

## Required configuration

Pick a provider and supply the matching key:

| Provider     | Env var              | Where to get the key                       |
|--------------|----------------------|--------------------------------------------|
| `gemini` (default) | `GEMINI_API_KEY` | https://aistudio.google.com/             |
| `openai`     | `OPENAI_API_KEY`     | https://platform.openai.com/             |
| `anthropic`  | `ANTHROPIC_API_KEY`  | https://console.anthropic.com/           |
| `openrouter` | `OPENROUTER_API_KEY` | https://openrouter.ai/keys (100+ models) |
| `ollama`     | *(none)*             | https://ollama.com (runs locally, free)  |

Switch providers via `--provider openai` or `OMX_PROVIDER=ollama`.

### Optional environment variables

| name              | default                         | meaning                              |
|-------------------|---------------------------------|--------------------------------------|
| `OMX_PROVIDER`    | `gemini`                        | LLM backend                          |
| `OMX_MODEL`       | (per-provider)                  | Override the model id                |
| `OMX_BASE_URL`    | (none)                          | For ollama / OpenAI-compatible APIs  |
| `OMX_BUDGET`      | `0` (unlimited)                 | Hard cap on LLM calls per task       |
| `OMX_CACHE_TTL`   | `0` (no expiry)                 | Cache entry lifetime in seconds      |
| `OMX_MAX_STEPS`   | `10`                            | Max iterations per task              |
| `OMX_WORKSPACE`   | `workspace`                     | Default sandbox directory            |
| `OMX_LOG_LEVEL`   | `INFO`                          | DEBUG/INFO/WARNING/ERROR             |
| `OMX_LOG_FILE`    | `omx.log`                       | Structured log destination           |

## Workflows

- **Web UI** (default) — runs `python main.py --web --host 0.0.0.0 --port 5000`,
  serves the FastAPI app + static front-end. Output type: webview.
- **OpenManus CLI** — runs `python main.py --help` for sanity-checking the CLI
  is wired correctly.

## CLI flags

```
python main.py [--task "..."] [--path PATH] [--provider PROV] [--model MODEL]
               [--mode {react,one-shot}] [--budget N]
               [--cache {on,off}] [--no-cache] [--no-synthesis]
               [--web] [--host H] [--port P] [--debug]
```

## Validation

End-to-end runs verified against the live Gemini API:

- ReAct + python tool — computed `fib(12)=144`.
- ReAct + search tool — answered "Python released in 1991" via DuckDuckGo.
- ReAct + shell with pipes — `git ls-files | grep \.py$ | wc -l` works via bash.
- Budget enforcement — `--budget N` halts at exactly N calls.
- Web UI streams events correctly; SSE protocol verified end-to-end via curl.
- `/api/info` correctly reports provider readiness based on environment.
- 14 unit + integration tests pass (no network).

## Standalone binary

```bash
pip install -e ".[dev]"     # includes pyinstaller
python build_binary.py
./dist/omx --task "list files" --path .
./dist/omx --web --port 5000
```

The web UI's static assets are bundled inside the binary, so the same single
file runs both modes.

## Pushing to GitHub

The main agent cannot push directly. From the Shell tab:

```bash
git add -A
git commit -m "Add multi-provider support, web UI, PyInstaller binary"
git push origin main
```

If the saved credential is stale, generate a new PAT at
https://github.com/settings/tokens (scopes: `repo` + `workflow`).
