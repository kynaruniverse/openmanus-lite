import json
import os

FILE = "memory.json"

def load():
    if not os.path.exists(FILE):
        return {"history": []}
    return json.load(open(FILE))

def save(mem):
    json.dump(mem, open(FILE, "w"), indent=2)

def add(task, result):
    mem = load()

    if any(t["task"] == task for t in mem["history"]):
        return

    mem["history"].append({
        "task": task,
        "result": result
    })

    save(mem)

def find(task):
    mem = load()
    for t in mem["history"]:
        if t["task"] == task:
            return t["result"]
    return None
