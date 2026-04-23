import subprocess

def run(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    return result.stdout + result.stderr
