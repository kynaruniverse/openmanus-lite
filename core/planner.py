import os
import json
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def safe_parse(text):
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        return json.loads(text[start:end])
    except:
        return [{"type": "error"}]

def local_plan(user):
    u = user.lower()

    if "create" in u and "file" in u:
        return [{"type": "file_tool", "action": "write", "file": u.split()[-1], "content": "hello world"}]

    if "list" in u:
        return [{"type": "shell", "command": ["ls"]}]

    return None

def llm_plan(user):
    if not client:
        return [{"type": "error"}]

    prompt = f"""
Return JSON ARRAY of steps:

[
  {{"type": "...", "action": "...", "file": "...", "command": "..."}}
]

Task: {user}
"""

    res = client.models.generate_content(
        model="models/gemini-2.0-flash",
        contents=prompt
    )

    return safe_parse(res.text)

def plan(user):
    return local_plan(user) or llm_plan(user)
