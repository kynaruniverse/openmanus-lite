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
            cmd = plan.get("command", "")
            # Mobile Safety: Prevent destructive commands in the terminal
            forbidden = ["rm -rf /", "mkfs", "dd if="]
            if any(bad in cmd for bad in forbidden):
                return "BLOCKED: Potential destructive command detected for mobile safety."
            return shell_tool.run(cmd.split())


        if t == "sys_clean":
            import shutil
            import os
            if os.path.exists("workspace"):
                shutil.rmtree("workspace")
                os.makedirs("workspace")
            return "🧹 Workspace cleared."

        if t == "error":
            return plan.get("msg")

    return "INVALID PLAN"
