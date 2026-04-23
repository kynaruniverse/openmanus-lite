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

    import json
    prompt = f"""
    You are a mobile-optimized agent. Return a JSON object for this task: "{user}"
    
    Format:
    {{
      "type": "write" | "read" | "shell" | "git",
      "file": "filename (if applicable)",
      "content": "content to write (if applicable)",
      "command": "terminal command (if shell)",
      "args": ["git", "args", "list"]
    }}
    
    Rules:
    1. Only return valid JSON. No markdown.
    2. For mobile safety, avoid 'rm -rf' or system-destructive commands.
    3. Use 'ls -p' to distinguish directories.
    4. Shorten 'content' strings in responses to save mobile data/memory.
    """


    from google.genai import errors

    try:
        res = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        )
        # Cleaner extraction and safer json.loads
        text = res.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except errors.ClientError as e:
        if "429" in str(e):
            return {"type": "error", "msg": "☕ Quota hit! Gemini needs a 30s break. Please try again in a moment."}
        return {"type": "error", "msg": f"API Error: {str(e)}"}
    except Exception as e:
        return {"type": "error", "msg": f"Unexpected Error: {str(e)}"}
    except Exception as e:
        return {"type": "error", "msg": f"LLM Parse Error: {str(e)}"}



def plan(user):
    intent = normalize(user)

    # 1. deterministic first
    p = local_plan(user, intent)
    if p:
        return p

    # 2. fallback
    return llm_plan(user)
