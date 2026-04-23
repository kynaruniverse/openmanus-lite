import subprocess

import shutil

def run(args):
    if not shutil.which("git"):
        return "⚠️ Git is not installed on this mobile environment. Please install it (e.g., 'pkg install git' in Termux)."
    
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=15)
        return (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return "⏳ Git command timed out. Network might be slow."
    except Exception as e:
        return f"❌ Git Error: {str(e)}"
