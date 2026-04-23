def route(user: str):
    u = user.lower().strip()

    # LOCAL FILE OPS (NO LLM)
    if any(x in u for x in ["create file", "make file", "write file"]):
        return "local_write"

    if any(x in u for x in ["list files", "ls", "show files", "directory"]):
        return "local_ls"

    if "git status" in u:
        return "local_git_status"

    if "read file" in u:
        return "local_read"

    # SAFE DEFAULT
    return "llm"
