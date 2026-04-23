def normalize(user: str):
    u = user.lower().strip()

    # convert natural language → structured intent hints
    return {
        "raw": user,
        "is_file": any(x in u for x in ["file", ".txt", ".py", ".md", "read", "view"]),
        "is_create": any(x in u for x in ["create", "make", "new", "touch"]),
        "is_list": any(x in u for x in ["list", "ls", "show", "directory"]),
        "is_git": "git" in u,
        "is_shell": any(x in u for x in ["run", "exec", "cmd", "shell", "terminal"])
    }

