# OpenManus-X

Local-first autonomous agent framework.

## 🔥 Why this exists

Most AI agents:
- require API keys
- burn tokens constantly
- are unpredictable

OpenManus-X:
- runs locally first
- uses AI only when needed
- works without API keys

## ⚡ Features

- Local-first execution (no API required)
- Plugin system
- Persistent memory
- Multi-step planning
- CLI interface

## 🚀 Install

```bash
git clone https://github.com/YOUR_USERNAME/openmanus-x.git
cd openmanus-x
pip install -r requirements.txt
▶️ Run
Bash
python3 main.py
or
Bash
python3 main.py --task "create file test.txt"
🔑 Optional AI
Bash
export GEMINI_API_KEY=your_key
🧠 Examples

create file test.txt
list files
git status
🧩 Plugins
Add new tools in:

tools/
Each tool must implement:
Python
def run(args):
    return "result"
📜 License
MIT EOF

---

# 📜 STEP 6 — LICENSE (IMPORTANT)

```bash
cat > LICENSE << 'EOF'
MIT License

Permission is hereby granted, free of charge...
