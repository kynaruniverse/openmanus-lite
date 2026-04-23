def route(user: str):
    u = user.lower().strip()

    # ---- FILE INTENT ----
    file_keywords = ["create file", "make file", "write file", "new file"]
    if any(k in u for k in file_keywords):
        return "file_write"

    if u.startswith("create ") and ".txt" in u:
        return "file_write"

    if "read file" in u or "open file" in u:
        return "file_read"

    # ---- SYSTEM INTENT ----
    if u in ["ls", "list files", "show files"]:
        return "ls"

    if "git status" in u:
        return "git"

    if "git" in u and "status" in u:
        return "git"

    # ---- SAFE SHELL INTENT ----
    shell_keywords = ["run", "execute", "command"]
    if any(k in u for k in shell_keywords):
        return "shell"

    # ---- DEFAULT ----
    return "llm"
