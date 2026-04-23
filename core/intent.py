def normalize(user: str):
    u = user.lower().strip()

    # convert natural language → structured intent hints
    return {
        "raw": user,
        "is_file": any(x in u for x in ["file", ".txt", ".py", ".md"]),
        "is_create": "create" in u or "make" in u,
        "is_list": "list" in u or "ls" in u,
        "is_git": "git" in u,
        "is_shell": any(x in u for x in ["run", "execute", "command"])
    }
