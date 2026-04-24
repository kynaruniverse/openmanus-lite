# 🌟 OpenManus-Lite: Universal AI Developer Agent

A mobile-first, context-aware AI agent built to help you build, edit, and manage repositories of any size—directly from your phone (Termux/Spck) or PC.

## 🚀 Versatile Usage Modes

### 1. The "Specialist" Mode (Best for existing huge repos)
Drop the agent into any folder (like a Pokémon Decompilation) without moving files.
1. `cd /path/to/your/massive-repo`
2. `omx --task "refactor the damage calculation in battle.c" --path .`
*The agent treats your current folder as its workspace.*

### 2. The "Sandbox" Mode (Safe testing)
Build new things in an isolated environment.
1. `omx --task "create a snake game in python"`
*Files will be created safely in the `OpenManus/workspace` folder.*

### 3. The "Bake-In" Mode
Add the agent as a tool inside your own project's repo.
1. `git submodule add https://github.com/kynaruniverse/openmanus-lite .agent`

## 🛠️ Installation
1. `git clone https://github.com/kynaruniverse/openmanus-lite`
2. `cd openmanus-lite`
3. `pip install -e .`
4. `cp config.json.example config.json` (Add your Gemini API Key)

## 🕹️ CLI Commands
- `omx`: Start interactive mobile shell.
- `omx --task "..."`: Run a single prompt.
- `omx --path "/path/to/project"`: Set a specific working directory.

## 🛡️ Security
The agent is restricted to the path you provide. It cannot access files outside of the `--path` or the default `workspace` folder.

## 🔑 Setting up your API Key
1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Open the `.env` file in the project folder.
3. Paste your key: `GEMINI_API_KEY=your_actual_key_here`
4. Save and run!

*Note: You can also set it globally in your terminal using `export GEMINI_API_KEY=your_key`.*
