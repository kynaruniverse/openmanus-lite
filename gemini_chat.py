import os
import subprocess
import time
from google import genai
from google.genai.errors import ServerError

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not set")

client = genai.Client(api_key=API_KEY)

REPO_PATH = os.getcwd()
WORKSPACE = os.path.join(REPO_PATH, "workspace")

os.makedirs(WORKSPACE, exist_ok=True)

print("OpenManus Autonomous Agent (PHASE 3)")
print(f"Repo: {REPO_PATH}\n")

def run(cmd):
    return subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)

def git(cmd):
    result = run(["git"] + cmd)
    return result.stdout + result.stderr

# ---------------- SAFE FILE SYSTEM ----------------

def safe_path(path):
    # force everything into workspace
    return os.path.join(WORKSPACE, path.lstrip("/"))

def write_file(path, content):
    full_path = safe_path(path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    return f"Wrote workspace/{path}"

def read_file(path):
    full_path = safe_path(path)
    try:
        with open(full_path, "r") as f:
            return f.read()
    except Exception:
        return f"FAILED READ: workspace/{path}"

# ---------------- AGENT ----------------

def apply_agent(task):
    prompt = f"""
You are an autonomous coding agent.

Return ONLY valid JSON in this format:

{{
  "actions": [
    {{
      "type": "write",
      "path": "file.txt",
      "content": "hello"
    }},
    {{
      "type": "shell",
      "command": "ls"
    }},
    {{
      "type": "git",
      "command": "status"
    }}
  ]
}}

RULES:
- Only JSON, no text
- Only workspace file paths
- No absolute paths
- No outside filesystem access

TASK:
{task}
"""

    models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash"
    ]

    last_err = None

    for model in models:
        for _ in range(3):
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return res.text
            except ServerError as e:
                last_err = e
                time.sleep(2)

    return f"ERROR: {last_err}"

# ---------------- EXECUTOR ----------------

def execute(plan):
    import json

    try:
        start = plan.find("{")
        end = plan.rfind("}") + 1
        data = json.loads(plan[start:end])
    except:
        return "INVALID JSON PLAN"

    results = []

    for action in data.get("actions", []):
        t = action.get("type")

        if t == "write":
            results.append(write_file(
                action.get("path", ""),
                action.get("content", "")
            ))

        elif t == "read":
            results.append(read_file(action.get("path", "")))

        elif t == "git":
            results.append(git(action.get("command", "").split()))

        elif t == "shell":
            cmd = action.get("command", "").split()
            if cmd:
                results.append(run(cmd).stdout)

    return "\n".join(results)

# ---------------- LOOP ----------------

while True:
    user = input("\nYou: ")

    if user in ["/exit", "exit"]:
        break

    plan = apply_agent(user)

    print("\n--- PLAN ---\n")
    print(plan)

    print("\n--- EXECUTION ---\n")
    print(execute(plan))
