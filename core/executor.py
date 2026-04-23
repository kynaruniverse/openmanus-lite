from tools import file_tool, shell_tool, git_tool

def execute(plan):

    if isinstance(plan, dict):

        t = plan.get("type")

        if t == "write":
            return file_tool.run({
                "action": "write",
                "file": plan.get("file"),
                "content": plan.get("content")
            })

        if t == "read":
            return file_tool.run({
                "action": "read",
                "file": plan.get("file")
            })

        if t == "ls":
            return shell_tool.run(["ls"])

        if t == "git":
            return git_tool.run(plan.get("args", ["status"]))

        if t == "shell":
            return shell_tool.run(plan.get("command", "").split())

        if t == "error":
            return plan.get("msg")

    return "INVALID PLAN"
