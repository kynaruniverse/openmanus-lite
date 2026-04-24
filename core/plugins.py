import os
import importlib.util
import sys

# This is the dictionary the executor looks for
TOOLS = {}

def load():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    folder = os.path.join(project_root, "tools")
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if not os.path.exists(folder):
        return

    for f in os.listdir(folder):
        if f.endswith("_tool.py"):
            # Example: file_tool.py becomes file
            name = f.replace("_tool.py", "")
            path = os.path.join(folder, f)
            
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Add the tool's run function to our registry
            if hasattr(mod, "run"):
                TOOLS[name] = mod.run
