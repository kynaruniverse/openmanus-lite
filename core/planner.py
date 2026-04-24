import os
import json
from google import genai
from dotenv import load_dotenv

# Load keys from a .env file if it exists
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def llm_plan(user):
    if not client:
        return {
            "type": "error", 
            "msg": "🔑 No API Key found! Please set GEMINI_API_KEY in your .env file or terminal."
        }

    prompt = f"""
    You are a professional terminal-based AI developer. 
    Task: "{user}"
    Return a JSON object only.
    Format: {{"type": "write", "file": "name", "content": "data"}}
    """

    try:
        res = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        )
        text = res.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except Exception as e:
        return {"type": "error", "msg": str(e)}

def plan(user):
    return llm_plan(user)
