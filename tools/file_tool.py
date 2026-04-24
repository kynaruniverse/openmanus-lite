import os

WORKSPACE = os.path.abspath("workspace")

def run(args):
    action = args.get("action") or args.get("type")
    filename = args.get("file", "").strip()
    
    if not filename:
        return "❌ Error: No filename provided."

    # Security: Prevent Directory Traversal
    target_path = os.path.abspath(os.path.join(WORKSPACE, filename))
    if not target_path.startswith(WORKSPACE):
        return "🛡️ Security Block: Access outside workspace denied."

    if action == "write":
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(args.get("content", ""))
        return f"WROTE {filename}"

    if action == "read":
        try:
            if not os.path.exists(target_path):
                return f"🔍 Error: File '{filename}' not found in workspace."
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"❌ Read Error: {str(e)}"

    return "INVALID FILE ACTION"
