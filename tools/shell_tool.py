import subprocess

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr
