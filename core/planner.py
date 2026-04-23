import os
from google import genai
from core.intent import normalize

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def local_plan(user, intent):
    u = user.lower()

    # FILE WRITE
    if intent["is_create"] and intent["is_file"]:
        name = u.split()[-1]
        return {"type": "write", "file": name, "content": "hello world"}

    # LIST FILES
    if intent["is_list"]:
        return {"type": "ls"}

    # GIT
    if intent["is_git"]:
        return {"type": "git", "args": ["status"]}

    return None


def llm_plan(user):
    if not client:
        return {"type": "error", "msg": "No API key"}

    prompt = f"""
Return ONLY JSON:

{{
  "type": "write|read|shell|git",
  "file": "name",
  "content": "text",
  "command": "command"
}}

Task: {user}
"""

    res = client.models.generate_content(
        model="models/gemini-2.0-flash",
        contents=prompt
    )

    try:
        start = res.text.find("{")
        end = res.text.rfind("}") + 1
        return eval(res.text[start:end])  # safe fallback parse
    except:
        return {"type": "error", "msg": "bad llm output"}


def plan(user):
    intent = normalize(user)

    # 1. deterministic first
    p = local_plan(user, intent)
    if p:
        return p

    # 2. fallback
    return llm_plan(user)
