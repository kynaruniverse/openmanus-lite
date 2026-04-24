# 🌟 OpenManus-Lite: Universal AI Developer Agent

A mobile-first, context-aware AI agent built to help you build, edit, and manage repositories of any size—directly from your phone (Termux/Ubuntu) or PC.

## 🚀 Versatile Usage Modes

### 1. The "Specialist" Mode (Best for existing repos)
Run the agent on any folder (like a Pokémon Decomp) without moving files.
1. `cd /path/to/your/project`
2. `omx --task "description of task" --path .`

### 2. The "Sandbox" Mode (Safe testing)
Build new things in an isolated environment.
1. `omx --task "create a snake game in python"`
*Files will be created in the `OpenManus/workspace` folder.*

## 🛠️ Installation
1. `git clone https://github.com/kynaruniverse/openmanus-lite`
2. `cd openmanus-lite`
3. `pip install -e .`
4. `cp .env.example .env` (Then add your Gemini API Key to .env)

## 🕹️ CLI Commands
- `omx`: Start interactive mobile shell.
- `omx --task "..."`: Run a single prompt.
- `omx --path "."`: Set current directory as target.
- `omx --no-cache`: Force the agent to re-think (ignore memory).

## 🛡️ Security
The agent is restricted to the path you provide via `--path`. It cannot access files outside that target or the default `workspace`.

## 🔑 Setting up your API Key
1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Open the `.env` file in the project folder.
3. Paste your key: `GEMINI_API_KEY=your_actual_key_here`
