from core.plugins import run as run_tool
from tools import shell_tool, git_tool

def execute(plan):
    results = []

    for step in plan:
        t = step.get("type")

        if t == "file_tool":
            results.append(run_tool("file_tool", step))

        elif t == "shell":
            results.append(shell_tool.run(step.get("command", [])))

        elif t == "git":
            results.append(git_tool.run(step.get("args", [])))

        elif t == "error":
            results.append("ERROR")

    return "\n".join(results)
