import os

WORKSPACE = "workspace"

def run(args):
    cmd = args.get("action")

    if cmd == "write":
        path = os.path.join(WORKSPACE, args.get("file",""))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(args.get("content",""))
        return f"WROTE {path}"

    if cmd == "read":
        file_name = args.get("file","")
        path = os.path.join(WORKSPACE, file_name)
        try:
            if not os.path.exists(path):
                # Mobile UX: If file isn't in workspace, check root as fallback
                if os.path.exists(file_name):
                    return open(file_name).read()
                return f"🔍 Error: File '{file_name}' not found."
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"❌ Read Error: {str(e)}"

    return "INVALID FILE ACTION"
