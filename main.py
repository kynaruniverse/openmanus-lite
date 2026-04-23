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
            print("[CACHED]\n", cached)
            return

    steps = plan(user)
    result = execute(steps)

    memory.add(user, result)
    print(result)

if args.task:
    run_task(args.task)
else:
    print("OpenManus-X CLI\n")
    while True:
        user = input("You: ")
        if user in ["exit", "quit"]:
            break
        run_task(user)
