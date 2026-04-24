import subprocess
import shlex

def run(plan):
    # Determine command based on type
    if plan.get("type") == "ls":
        cmd_str = "ls -p"
    else:
        cmd_str = plan.get("command", "")

    if not cmd_str:
        return "❌ No command provided."

    # Mobile Safety Guardrail
    forbidden = ["rm -rf /", "mkfs", "dd if="]
    if any(bad in cmd_str for bad in forbidden):
        return "BLOCKED: Potential destructive command detected."

    try:
        # Use shlex for safe argument splitting
        args = shlex.split(cmd_str)
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()
    except Exception as e:
        return f"❌ Shell Error: {str(e)}"
