def route(user: str):
    u = user.lower()

    if "create" in u and "file" in u:
        return "write"

    if "list" in u or "files" in u:
        return "ls"

    if "git status" in u:
        return "git"

    return "llm"
