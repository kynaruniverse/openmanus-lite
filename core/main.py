import argparse
import os
import sys

# Get the directory where THIS file is (core/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (OpenManus root)
project_root = os.path.dirname(current_dir)

# Add the project root to sys.path so 'import core' works everywhere
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.planner import plan
from core.executor import execute
from core import memory
from core.plugins import load

load()

parser = argparse.ArgumentParser(description="OpenManus-Lite: Universal AI Agent")
parser.add_argument("--task", type=str, help="Run a single task")
parser.add_argument("--path", type=str, default=None, help="Target project directory")
parser.add_argument("--no-cache", action="store_true")
args = parser.parse_args()

def run_task(user, work_dir):
    if work_dir:
        target_path = os.path.abspath(work_dir)
    else:
        target_path = os.path.join(project_root, "workspace")
    
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)

    os.environ["OMX_TARGET_PATH"] = target_path

    if not args.no_cache:
        cached = memory.find(user)
        if cached:
            print(f"🚀 [CACHED]: {cached}")
            return

    print(f"🧠 Planning in {target_path}...")
    steps = plan(user)

    if steps.get("type") == "error":
        print(f"❌ Error: {steps.get('msg')}")
        return

    print(f"⚡ Executing {steps.get('type')}...")
    result = execute(steps)

    memory.add(user, result)
    if not result.startswith("🚀 [CACHED]"):
        print(f"\n✅ Result from {os.path.basename(target_path)}:\n{result}")

def main_interactive():
    print("🌟 OpenManus-Lite: Universal Edition")
    print(f"Current Directory: {os.getcwd()}")
    
    while True:
        user = input("OMX > ").strip()
        shortcuts = {"1": "list files", "2": "git status", "3": "help"}
        user = shortcuts.get(user, user)

        if user.lower() in ["exit", "quit", "q"]:
            break
        if not user:
            continue

        run_task(user, args.path or ".")

def run_from_cli():
    if args.task:
        run_task(args.task, args.path)
    else:
        main_interactive()
