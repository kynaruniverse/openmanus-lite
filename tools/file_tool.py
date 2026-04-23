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
        path = os.path.join(WORKSPACE, args.get("file",""))
        if not os.path.exists(path):
            return "NOT FOUND"
        return open(path).read()

    return "INVALID FILE ACTION"
