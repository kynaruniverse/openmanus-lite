import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def llm_plan(user):
    if not client:
        return {"type": "error", "msg": "🔑 API Key missing in .env"}

    prompt = f"""
    Task: "{user}"
    Respond ONLY with a JSON object. No prose.
    Example: {{"type": "write", "file": "main.py", "content": "print('hello')"}}
    
    Rules:
    1. Only use "write" for creating/editing files.
    2. Filename must be exact (e.g., 'main.py' NOT 'main.py'').
    """

    try:
        res = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        )
        text = res.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"type": "error", "msg": str(e)}

def plan(user):
    return llm_plan(user)
