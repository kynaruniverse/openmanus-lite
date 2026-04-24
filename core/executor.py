import shlex
from core import plugins

def execute(plan):
    if not isinstance(plan, dict):
        return "INVALID PLAN"

    t = plan.get("type")
    
    # 1. System Internal Actions
    if t == "sys_clean":
        import shutil
        import os
        if os.path.exists("workspace"):
            shutil.rmtree("workspace")
            os.makedirs("workspace")
        return "🧹 Workspace cleared."

    if t == "error":
        return plan.get("msg")

    # 2. Plugin-Based Actions
    # Map intent types to tool filenames
    tool_map = {
        "write": "file_tool",
        "read": "file_tool",
        "ls": "shell_tool",
        "shell": "shell_tool",
        "git": "git_tool"
    }

    tool_name = tool_map.get(t)
    if tool_name in plugins.TOOLS:
        # Pass the whole plan to the tool
        return plugins.TOOLS[tool_name](plan)

    return f"UNKNOWN ACTION: {t}"
