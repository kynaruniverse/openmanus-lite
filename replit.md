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
  agent.py          orchestrator (plan → execute → synthesise)
  llm.py            Gemini client wrapper with explicit error handling
  planner.py        prompt + JSON plan parser
  executor.py       dispatch each step to a tool
  memory.py         exact-match cache (only successful runs)
  plugins.py        loads tools/*_tool.py
  config.py         env-driven config (fails fast on missing key)
  logging_setup.py  shared "omx" logger (console + file)
  main.py           thin shim exporting cli.run_from_cli for back-compat
tools/
  file_tool.py      sandboxed read / write inside the target directory
  shell_tool.py     shell exec with destructive-command blocklist
  git_tool.py       git subcommands
tests/
  test_basic.py     unit tests for planner + tools (no network)
main.py             top-level launcher
```

## Required configuration

- `GEMINI_API_KEY` — set as a Replit Secret (preferred) or in a local `.env`.

The committed `.env` (which contained a leaked key) was deleted; `.env.example`
documents the schema. If `GEMINI_API_KEY` is missing the program exits with a
clear error (exit code 2).

## Workflow

A console workflow named **OpenManus CLI** runs `python main.py --help` to
verify the CLI is wired correctly without burning API quota on every restart.
Real tasks should be run from the shell, e.g.:

```bash
python main.py --task "list files in current directory" --path .
python main.py --task "analyze this repository" --path .
python main.py        # interactive shell
```

## Validation

Real end-to-end tasks have been verified against the live Gemini API:

- list directory → planner picked `shell ls -la`, executor returned the tree.
- analyze repo → planner produced a 3-step plan (shell + file_read + answer),
  executor ran tools, synthesis pass produced a real prose summary.
- write file → planner picked `file_write`, file was created and runs.
- interactive shell → shortcut `1` resolved to "list files" and ran cleanly.

`pytest -v` runs 8 offline unit tests covering plan parsing and tool sandboxing.

## Known limitations

- One-shot planner (no live re-planning if a tool fails mid-plan).
- Cache is exact-match by task string.
- No streaming output from Gemini.

## Pushing to GitHub

The main agent cannot push to GitHub directly. Use Replit's **Git** pane in
the workspace to commit and push, or rotate the GitHub Personal Access Token
in Account → Connected services and run `git push origin main` from a shell.
