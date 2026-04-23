import subprocess

BLOCKED = [
    "rm -rf",
    "sudo",
    "mkfs",
    ":(){",
]

def is_safe(command: str) -> bool:
    return not any(bad in command for bad in BLOCKED)

def run_safe(command: str):
    if not is_safe(command):
        return "BLOCKED: unsafe command"

    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout
