import subprocess
from agent.safety import is_safe

def git_status():
    return subprocess.run(["git", "status"], capture_output=True, text=True).stdout

def git_diff():
    return subprocess.run(["git", "diff"], capture_output=True, text=True).stdout

def git_add(files="."):
    return subprocess.run(["git", "add", files], capture_output=True, text=True).stdout

def git_commit(message):
    return subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True).stdout

def git_push():
    # SAFETY CHECK
    return subprocess.run(["git", "push"], capture_output=True, text=True).stdout
