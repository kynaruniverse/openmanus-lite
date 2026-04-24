# OpenManus-Lite

A mobile-first, terminal-based AI developer agent powered by Google Gemini. Runs as a Python CLI — no web server or frontend.

## Project Type
- Language: Python 3.12
- Type: Command-line interface (CLI)
- Entry point: `main.py` (also exposed as `omx` console script via `setup.py`)

## Layout
- `main.py` — CLI entry point that dispatches to `core.main:run_from_cli`
- `core/` — planner, executor, memory, plugin loader, config
- `tools/` — pluggable tool modules (`file_tool.py`, `git_tool.py`, `shell_tool.py`)
- `workspace/` — default sandbox folder for generated files

## Dependencies
Installed via Replit's package manager:
- `google-genai` — Gemini LLM client
- `python-dotenv` — loads `GEMINI_API_KEY` from `.env`

## Configuration
- `GEMINI_API_KEY` is read from `.env` (already present in the repo).
- Model defaults to `models/gemini-2.0-flash`.

## Usage
- Show help: `python main.py --help`
- Run a single task: `python main.py --task "list files" --path .`
- Interactive shell: `python main.py`

## Workflow
A console workflow named **OpenManus CLI** runs `python main.py --help` to verify the CLI is installed and working. For real usage, run commands manually in the shell.

## Notes
- This project has no HTTP server, so no deployment configuration is required.
- `memory.json` (created at runtime) caches task results.
