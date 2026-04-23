import os
import subprocess
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not set in environment")

client = genai.Client(api_key=API_KEY)

REPO_PATH = os.getcwd()

print("OpenManus Autonomous Agent (LEVEL 3)")
print(f"Repo: {REPO_PATH}\n")

def run(cmd):
    return subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)

def git(cmd):
    result = run(["git"] + cmd)
    return result.stdout + result.stderr

def write_file(path, content):
    full_path = os.path.join(REPO_PATH, path)
    with open(full_path, "w") as f:
        f.write(content)
    return f"Wrote {path}"

def read_file(path):
    full_path = os.path.join(REPO_PATH, path)
    with open(full_path, "r") as f:
        return f.read()

def apply_agent(task):
    prompt = f"""
You are an autonomous dev agent.

You can output actions in this format ONLY:

COMMAND: git <args>
COMMAND: write <file>|<content>
COMMAND: read <file>
COMMAND: shell <command>

Task:
{task}
"""

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )

    return response.text

while True:
    user = input("\nYou: ")

    if user in ["/exit", "exit"]:
        break

    result = apply_agent(user)

    result = result.replace("```", "")

    print("\n--- Agent Plan ---\n")
    print(result)

    print("\n--- Execution ---\n")

    ALLOWED = ["ls", "cat", "git", "python3", "echo", "pwd"]

    for line in result.splitlines():
        if line.startswith("COMMAND: git"):
            cmd = line.replace("COMMAND: git", "").strip().split()
            print(git(cmd))

        elif line.startswith("COMMAND: write"):
            _, rest = line.split("COMMAND: write", 1)
            file_path, content = rest.split("|", 1)
            print(write_file(file_path.strip(), content))

        elif line.startswith("COMMAND: read"):
            file_path = line.replace("COMMAND: read", "").strip()
            print(read_file(file_path))

        elif line.startswith("COMMAND: shell"):
            cmd = line.replace("COMMAND: shell", "").strip().split()

            if not cmd:
                continue

            if cmd[0] not in ALLOWED:
                print("Blocked unsafe command:", cmd[0])
                continue

            print(run(cmd).stdout)
