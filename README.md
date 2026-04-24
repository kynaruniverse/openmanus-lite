# 🌟 OpenManus-Lite

**A pocket-sized AI developer agent.** Tell it what you want in plain English; it
plans, runs real shell commands, edits files, searches the web, and reports back.
Runs anywhere Python runs — laptop, Replit, or your phone via Termux.

Powered by Google Gemini, sandboxed for safety, and small enough to read in an
afternoon.

---

## ✨ What it can do

- **Explore code** — *"summarise this repo", "where is the auth logic?", "show me the diff for core/agent.py"*
- **Build things** — *"create a snake game in python", "scaffold a flask hello-world"*
- **Crunch numbers** — *"what's the 12th fibonacci?"* (runs in a sandboxed Python subprocess)
- **Search the web** — *"what year was python released?"* (no API key required)
- **Run safe shell** — pipes, globs and redirects work; destructive commands are blocked
- **Use your git history** — *"summarise the last 10 commits"*

---

## 🚀 Quick start

```bash
git clone https://github.com/kynaruniverse/openmanus-lite
cd openmanus-lite
pip install -e .
cp .env.example .env       # add your Gemini key here
omx --task "summarise this repo" --path .
```

Get a free Gemini key in 30 seconds at <https://aistudio.google.com/>.

---

## 💬 Three ways to use it

### 1. One-shot task on a real project
```bash
omx --task "write a unit test for utils.py" --path .
```

### 2. Sandbox mode — safe scratch directory (default `./workspace/`)
```bash
omx --task "create a tic-tac-toe game in python"
```

### 3. Interactive shell
```bash
omx
OMX > list files
OMX > git status
OMX > how many python files are in this repo?
OMX > exit
```
Shortcuts: `1` → list files · `2` → git status · `3` → help.

---

## 🧠 How it thinks

OpenManus-Lite ships with **two reasoning modes**:

### ReAct loop (default)
*Think → Act → Observe → repeat.* The agent plans **one step at a time**, runs
the tool, sees the actual output, then decides what to do next. Handles
surprises, recovers from errors, and only calls the LLM as many times as it
needs.

```
        ┌──────────────┐
        │   user task  │
        └──────┬───────┘
               ▼
   ┌──────────────────────┐
   │ LLM: pick next step  │◀──┐
   └──────┬───────────────┘   │
          ▼                   │
   ┌──────────────┐           │  observation
   │  tool call   │───────────┘
   └──────┬───────┘
          ▼
       finish? ──▶ final answer
```

### One-shot mode (`--mode one-shot`)
The classic approach: plan everything in a single LLM call, run the steps,
then synthesise an answer. Cheaper and faster for simple, predictable tasks.

---

## 🧰 Tools the agent can use

| Tool       | What it does                                                  |
|------------|---------------------------------------------------------------|
| `shell`    | Run shell commands (pipes, redirects, globs OK; destructive blocked) |
| `file`     | Read or write files **inside the target path** (sandbox-enforced) |
| `git`      | Any git subcommand — `status`, `log`, `diff`, …               |
| `python`   | Evaluate a small Python snippet in an isolated subprocess     |
| `search`   | Web search via DuckDuckGo (no API key needed)                 |

Drop a new file into `tools/` matching `*_tool.py` with a `run(plan: dict) -> str`
function and it loads automatically — no other plumbing required.

---

## 🛡️ Safety

- File reads/writes are **clamped to the target directory** via `os.path.commonpath`. `..` escapes are rejected.
- Shell commands are matched against a destructive-command blocklist (`rm -rf /`, `mkfs`, `dd if=`, fork bombs, …) and have a 30-second wall-clock timeout.
- Python snippets run in a fresh `python -I` subprocess with their own 10-second timeout.
- API keys are loaded from environment variables only. The repo never contains a real key, and `.env` is git-ignored.
- A configurable **call budget** (`--budget N` / `OMX_BUDGET`) caps how many LLM calls a single task can use, so a runaway agent can't blow your quota.

---

## 🔑 Configuration

### Required
| Variable          | Purpose                                |
|-------------------|----------------------------------------|
| `GEMINI_API_KEY`  | Your Google Gemini key (Replit Secret or `.env`) |

### Optional
| Variable          | Default                            | Purpose                              |
|-------------------|------------------------------------|--------------------------------------|
| `OMX_MODEL`       | `models/gemini-2.5-flash-lite`     | Override the Gemini model id         |
| `OMX_BUDGET`      | `0` (unlimited)                    | Hard cap on LLM calls per task       |
| `OMX_MAX_STEPS`   | `10`                               | Max iterations per task              |
| `OMX_CACHE_TTL`   | `0` (no expiry)                    | Cache entry lifetime in seconds      |
| `OMX_WORKSPACE`   | `workspace`                        | Default sandbox directory            |
| `OMX_LOG_LEVEL`   | `INFO`                             | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `OMX_LOG_FILE`    | `omx.log`                          | Where to write the structured log    |

---

## 📋 CLI flags

```
omx [--task TASK] [--path PATH] [--mode {react,one-shot}]
    [--budget N] [--cache {on,off}] [--no-cache]
    [--no-synthesis] [--debug]
```

| Flag             | Description                                              |
|------------------|----------------------------------------------------------|
| `--task`         | Run a single task and exit (otherwise interactive)       |
| `--path`         | Target project directory (default: `./workspace`)        |
| `--mode`         | `react` (default) or `one-shot`                          |
| `--budget N`     | Hard cap on LLM calls per task                           |
| `--cache off`    | Disable cache reads + writes entirely                    |
| `--no-cache`     | Ignore the cache for this run only                       |
| `--no-synthesis` | Skip the second LLM pass in one-shot mode                |
| `--debug`        | Verbose console logging                                  |

---

## 🏗️ Project layout

```
core/
  cli.py            argparse + interactive shell
  agent.py          orchestrator: react vs one-shot, cache, budget
  llm.py            Gemini client wrapper (streaming, retries, budget)
  react.py          ReAct loop: think → act → observe
  planner.py        legacy one-shot prompt + JSON plan parser
  executor.py       single-step or full-plan dispatch to tools
  memory.py         normalised cache with optional TTL
  plugins.py        loads tools/*_tool.py at startup
  config.py         env-driven config (fails fast on missing key)
  logging_setup.py  shared "omx" logger (console + file)
tools/
  shell_tool.py     shell exec, destructive-command blocklist
  file_tool.py      sandboxed read/write
  git_tool.py       arbitrary git subcommands
  python_tool.py    sandboxed `python -c` snippet evaluation
  search_tool.py    DuckDuckGo web search
tests/
  test_basic.py        offline unit tests for planner + tools
  test_integration.py  ReAct end-to-end tests with a stub LLM
```

---

## 🧪 Running the tests

```bash
pip install -e ".[dev]"
pytest -v
```

14 tests, all offline (no network, no API quota burned). Covers plan parsing,
tool sandboxing, the full ReAct loop with a fake LLM, JSON-recovery, file
round-trip, and budget enforcement.

---

## 📱 Mobile-friendly

OpenManus-Lite was designed to be usable from a phone via [Termux](https://termux.dev/):

```bash
pkg install python git
git clone https://github.com/kynaruniverse/openmanus-lite
cd openmanus-lite
pip install -e .
omx
```

No GUI, no Electron, no 200 MB of node_modules — just Python and a terminal.

---

## 🤝 Contributing

1. Fork and clone the repo.
2. `pip install -e ".[dev]"`
3. Make your change, run `pytest -v`.
4. Open a pull request.

Adding a new tool is a single ~40-line file in `tools/` — see `python_tool.py`
for a minimal example.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
