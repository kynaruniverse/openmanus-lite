import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "models/gemini-2.5-flash"

def plan(task: str):
    prompt = f"""
You are a strict autonomous coding agent.

You MUST output ONLY valid JSON in this format:

{{
  "actions": [
    {{
      "type": "read|write|shell|git",
      "path": "file path (if needed)",
      "content": "file content (if write)",
      "command": "shell or git command (if needed)"
    }}
  ]
}}

Rules:
- No explanations
- No markdown
- No extra text
- Only JSON

Task:
{task}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text
