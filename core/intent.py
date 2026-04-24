def normalize(user: str):
    u = user.lower().strip()
    
    # Unified Keyword Mapping
    is_git = "git" in u
    is_list = any(x in u for x in ["list", "ls", "show files", "directory"])
    is_create = any(x in u for x in ["create", "make", "new", "write file"])
    is_read = any(x in u for x in ["read", "view", "open file"])
    is_shell = any(x in u for x in ["run", "exec", "cmd", "shell"])
    is_sys = any(x in u for x in ["clean", "clear workspace", "reset"])

    return {
        "raw": user,
        "is_file": any(x in u for x in [".txt", ".py", ".md", "file"]) or is_create or is_read,
        "is_create": is_create,
        "is_read": is_read,
        "is_list": is_list,
        "is_git": is_git,
        "is_shell": is_shell,
        "is_sys": is_sys
    }
