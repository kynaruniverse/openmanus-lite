def require_approval(action_type, value):
    """
    Simple safety gate for dangerous operations.
    """
    dangerous = ["push", "delete", "rm", "reset", "rebase"]

    if action_type in ["git", "shell"]:
        if any(d in value for d in dangerous):
            return False
    return True
