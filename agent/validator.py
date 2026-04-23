import json

ALLOWED_TYPES = {"write", "read", "shell", "git"}

def validate_plan(plan):
    if "actions" not in plan:
        return False, "Missing actions"

    for a in plan["actions"]:
        if a.get("type") not in ALLOWED_TYPES:
            return False, f"Invalid action type: {a.get('type')}"

    return True, "OK"


def safe_parse(raw):
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"actions": []}
