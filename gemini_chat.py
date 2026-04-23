import os
import json
import asyncio
import subprocess
from router import route
from google import genai

# ---------------- CONFIG ----------------

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

REPO = os.getcwd()
WORKSPACE = os.path.join(REPO, "workspace")
os.makedirs(WORKSPACE, exist_ok=True)

MEM_FILE = os.path.join(REPO, "agent_memory_v7.json")

# ---------------- MEMORY ----------------

def load_memory():
    if not os.path.exists(MEM_FILE):
        return {"tasks": []}
    return json.load(open(MEM_FILE))

def save_memory(m):
    with open(MEM_FILE, "w") as f:
        json.dump(m, f, indent=2)

MEMORY = load_memory()

# ---------------- TOOL LAYER ----------------

def run(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True).stdout

def write_file(path, content):
    full = os.path.join(WORKSPACE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    return f"WROTE {path}"

def read_file(path):
    try:
        return open(os.path.join(WORKSPACE, path)).read()
    except:
        return "READ ERROR"

# ---------------- WORKERS ----------------

CALLS = 0
LIMIT = 6

def llm(prompt):
    global CALLS

    if not client or CALLS >= LIMIT:
        return '{"nodes":[]}'

    CALLS += 1

    res = client.models.generate_content(
        model="models/gemini-2.0-flash",
        contents=prompt
    )
    return res.text

# ---------- PLANNER WORKER ----------

def planner(task):
    return llm(f"""
You are Planner Worker.

Return ONLY JSON graph:

{{
  "nodes": [
    {{
      "id": "n1",
      "action": "write|read|shell",
      "target": "",
      "content": "",
      "command": "",
      "depends": []
    }}
  ]
}}

TASK:
{task}
""")

# ---------- EXECUTOR WORKER ----------

async def executor_node(node, results):
    deps = node.get("depends", [])

    while not all(d in results for d in deps):
        await asyncio.sleep(0.05)

    a = node["action"]

    if a == "write":
        out = write_file(node.get("target","file.txt"), node.get("content",""))
    elif a == "read":
        out = read_file(node.get("target",""))
    elif a == "shell":
        out = run(node.get("command",""))
    else:
        out = "UNKNOWN ACTION"

    results[node["id"]] = out
    return out

async def executor(nodes):
    results = {}
    tasks = [executor_node(n, results) for n in nodes]
    await asyncio.gather(*tasks)
    return "\n".join(results.values())

# ---------- CRITIC WORKER ----------

def critic(output):
    if len(output) == 0:
        return False
    if "ERROR" in output:
        return False
    return True

# ---------------- AGENT CORE ----------------

async def agent(task):
    print("\nTASK:", task)

    mode = route(task)
    print("MODE:", mode)

    # LOCAL FAST PATH
    if mode == "local_ls":
        return run(["ls"])

    if mode == "local_write":
        return write_file("hello.txt", "hello world")

    if mode == "local_git_status":
        return run(["git", "status"])

    # MEMORY CHECK
    for m in MEMORY["tasks"]:
        if m["task"] == task:
            print("MEMORY HIT")
            return m["result"]

    # PLANNING
    raw = planner(task)
    print("\nPLAN RAW:\n", raw)

    try:
        data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except:
        return "PLAN FAIL"

    nodes = data.get("nodes", [])

    # EXECUTION
    result = await executor(nodes)

    # CRITIC (1 PASS ONLY)
    if not critic(result):
        fix = llm(f"""
Fix this execution graph.

TASK: {task}
RESULT: {result}

Return JSON only.
""")

        try:
            d2 = json.loads(fix[fix.find("{"):fix.rfind("}")+1])
            result = await executor(d2.get("nodes", []))
        except:
            pass

    MEMORY["tasks"].append({"task": task, "result": result})
    save_memory(MEMORY)

    return result

# ---------------- LOOP ----------------

print("OpenManus V7 Multi-Worker Agent System\n")

while True:
    u = input("You: ")

    if u in ["exit","quit","/exit"]:
        break

    print(asyncio.run(agent(u)))
