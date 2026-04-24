import json
import os

# Memory is stored in the project root, not the target path,
# so the agent remembers tasks across different projects.
MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.json")

def find(user_query):
    if not os.path.exists(MEMORY_FILE):
        return None
    try:
        with open(MEMORY_FILE, "r") as f:
            mem = json.load(f)
            return mem.get(user_query)
    except:
        return None

def add(user_query, result):
    mem = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                mem = json.load(f)
        except:
            pass
    
    mem[user_query] = result
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)
