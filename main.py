import argparse
from core.router import route
from core.planner import plan
from core.executor import execute
from core import memory
from core.plugins import load

load()

parser = argparse.ArgumentParser(description="OpenManus-X CLI")
parser.add_argument("--task", type=str, help="Run a single task")
parser.add_argument("--no-cache", action="store_true")
args = parser.parse_args()

def run_task(user):
    if not args.no_cache:
        cached = memory.find(user)
        if cached:
            print(f"🚀 [CACHED]: {cached}")
            return

    print(f"🧠 Planning: {user}...")
    steps = plan(user)
    
    if steps.get("type") == "error":
        print(f"❌ Error: {steps.get('msg')}")
        return

    print(f"⚡ Executing {steps.get('type')}...")
    result = execute(steps)

    memory.add(user, result)
    print(f"✅ Result:\n{result}")


if args.task:
    run_task(args.task)
else:
    print("OpenManus-X CLI\n")
    print("Quick Actions: [1] ls  [2] git status  [3] help")
    while True:
        user = input("OpenManus-X > ").strip()
        
        # Quick Shortcuts for Mobile Typing
        shortcuts = {"1": "list files", "2": "git status", "3": "help"}
        user = shortcuts.get(user, user)
        
        if user.lower() in ["exit", "quit", "q"]:
            break
        if not user:
            continue
            
        run_task(user)


def run_from_cli():
    # Helper to allow the 'omx' command to work after 'pip install -e .'
    if args.task:
        run_task(args.task)
    else:
        # Launch interactive mode
        import sys
        main_interactive() # Wrap your while loop in this function name
