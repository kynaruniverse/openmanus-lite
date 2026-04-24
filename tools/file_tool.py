import os

def get_workspace():
    # Use the path set by main.py, otherwise fallback to local workspace
    return os.environ.get("OMX_TARGET_PATH", os.path.abspath("workspace"))

def run(args):
    WORKSPACE = get_workspace()
    action = args.get("action") or args.get("type")
    filename = args.get("file", "").strip()

    if not filename:
        return "❌ Error: No filename provided."

    # Prevent escaping the target project folder
    target_path = os.path.abspath(os.path.join(WORKSPACE, filename))
    if not target_path.startswith(WORKSPACE):
        return "🛡️ Security Block: Attempted access outside of target path."

    if action == "write":
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(args.get("content", ""))
        return f"SUCCESS: Wrote to {filename}"

    if action == "read":
        try:
            if not os.path.exists(target_path):
                return f"🔍 Error: File '{filename}' not found."
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"❌ Read Error: {str(e)}"

    return "INVALID FILE ACTION"
