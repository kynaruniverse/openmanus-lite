# 🌟 OpenManus-Lite: Universal AI Developer Agent

A mobile-first, terminal-based AI agent powered by Google Gemini. Plan and
execute coding tasks against any local repository — from your phone (Termux),
laptop, or Replit.

## 🚀 Usage Modes

### 1. Specialist mode (operate on an existing repo)
```bash
cd /path/to/your/project
omx --task "summarise this repo" --path .
```

### 2. Sandbox mode (safe scratch directory)
```bash
omx --task "create a snake game in python"
# Files are written under ./workspace/
```

### 3. Interactive shell
```bash
omx
OMX > list files
OMX > git status
OMX > exit
```

Shortcuts inside the shell: `1` → list files, `2` → git status, `3` → help.

## 🛠️ Installation

```bash
git clone https://github.com/kynaruniverse/openmanus-lite
cd openmanus-lite
pip install -e .
cp .env.example .env   # then add your Gemini API key
```

## 🔑 API key setup

1. Get a free Gemini key from <https://aistudio.google.com/>.
2. Either:
   - **Local dev**: paste it into `.env` as `GEMINI_API_KEY=...` (file is git-ignored)
   - **Replit**: open the **Secrets** tab and add `GEMINI_API_KEY` (preferred — never written to disk).

Optional environment variables:

| Variable        | Default                          | Purpose                              |
|-----------------|----------------------------------|--------------------------------------|
| `OMX_MODEL`     | `models/gemini-2.5-flash-lite`   | Override the Gemini model            |
| `OMX_LOG_LEVEL` | `INFO`                           | `DEBUG`, `INFO`, `WARNING`, `ERROR`  |
| `OMX_LOG_FILE`  | `omx.log`                        | Where to write the verbose log       |
| `OMX_MAX_STEPS` | `10`                             | Cap on steps per plan                |
| `OMX_WORKSPACE` | `workspace`                      | Default sandbox dir                  |

## 🛡️ Security

- The `file` tool is sandboxed to `--path` (or the default workspace) and rejects
  any path that escapes via `..`.
- The `shell` tool refuses obviously destructive commands (`rm -rf /`, `mkfs`,
  `dd if=`, fork bombs, …) and times out every command.
- API keys are loaded from environment variables only; the repo never contains
  a real key.

## 🧠 How it works

```
   user task ──▶ Planner (LLM) ──▶ Plan (JSON steps)
                                   │
                                   ▼
                              Executor ──▶ Tool registry
                                   │           ├── shell
                                   ▼           ├── file
                          (final answer        └── git
                            synthesised
                          from real outputs)
```

The planner produces a JSON plan in one call; the executor dispatches each step
to the tool of the matching name. If the plan ends with an `answer` step, a
second LLM call synthesises the response from the real tool outputs (so you get
facts, not placeholders).

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest -v
```

The unit tests cover plan parsing and tool sandboxing — no network calls.

## 📋 CLI flags

```
omx [--task TASK] [--path PATH] [--no-cache] [--debug]
```

| Flag         | Description                                         |
|--------------|-----------------------------------------------------|
| `--task`     | Run a single task and exit                          |
| `--path`     | Target directory (default `./workspace`)            |
| `--no-cache` | Ignore the memory cache and re-plan                 |
| `--debug`    | Verbose console logging (same as `OMX_LOG_LEVEL=DEBUG`) |
