# 📱 OpenManus-X (Mobile-First Edition)

**OpenManus-X** is a high-performance, local-first autonomous agent framework. It is specifically engineered to be lean, fast, and safe for mobile terminals (like Termux and iSH) while remaining fully capable on desktop environments.

Unlike traditional agents that burn cloud tokens for every thought, OpenManus-X uses **Intelligent Local Routing** to handle common tasks on-device, only calling the cloud when complex reasoning is required.

---

## 🔥 Why OpenManus-X?

- 🧠 **Local-First Intelligence**: Tasks like file management, directory listing, and git operations are handled by a deterministic local router. This saves battery, data, and API costs.
- 🛡️ **Hardened Safety**: Built-in guardrails block destructive commands (e.g., `rm -rf /`) at the executor level, ensuring your device remains safe.
- ♻️ **Persistent Instant Memory**: Features a local JSON-based cache. If you repeat a task, the agent retrieves the result instantly without re-processing.
- ☕ **Quota Resilience**: Optimized for the Gemini Free Tier. It gracefully handles rate limits (429 errors) with user-friendly notifications instead of crashing.
- ⚡ **Mobile Optimized UX**:
    - **Shortcuts**: Use numeric keys (`1`, `2`, `3`) for common actions.
    - **Visual Feedback**: Emoji status indicators (🧠, ⚡, ✅) make progress tracking easy on small screens.

---

## 🚀 Installation

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/kynaruniverse/openmanus-lite.git
cd openmanus-lite

# Install requirements
pip install -r requirements.txt
```

### 2. Enable CLI Shortcut
To use the omx command from anywhere in your terminal:
```bash
pip install -e .
export PYTHONPATH=$PYTHONPATH:.
```

## 🔑 Configuration
OpenManus-X is model-agnostic. You can customize the "brain" via environment variables:
```bash
# Required for advanced tasks
export GEMINI_API_KEY="your_google_ai_key"

# Optional: Override the default model
export OMX_MODEL="models/gemini-2.0-flash"
```

## 🕹️ Usage
### Interactive Mode
The best way to use the agent on mobile. Just type:
```bash
omx
```
*Quick Actions inside the shell:*
 - Type 1 for list files
 - Type 2 for git status
 - Type 3 for help
### Single Task Mode
Execute a command directly and exit:
```bash
omx --task "create a python script that calculates fibonacci"
omx --task "list files"
```
### Workspace Cleanup
Reset your agent's temporary workspace and clear the local cache:
```bash
omx --task "clean"
```

## 🧩 Plugin System
Expanding OpenManus-X is simple. Drop any Python script into the tools/ directory. As long as it contains a run(args) function, the agent will automatically detect and integrate it into its capabilities.
```python
# tools/hello_tool.py
def run(args):
    return "Hello from your custom tool!"
```

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.