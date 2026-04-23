import importlib
import os

TOOLS = {}

def load():
    folder = "tools"
    for f in os.listdir(folder):
        if f.endswith(".py"):
            name = f[:-3]
            mod = importlib.import_module(f"tools.{name}")
            if hasattr(mod, "run"):
                TOOLS[name] = mod.run

def run(tool, args):
    if tool in TOOLS:
        return TOOLS[tool](args)
    return "UNKNOWN TOOL"
