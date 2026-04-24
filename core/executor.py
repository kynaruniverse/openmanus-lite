from core import plugins

def execute(steps):
    tool_name = steps.get("type")
    
    # Mapping 'write' and 'read' to the 'file' tool
    if tool_name in ["write", "read"]:
        actual_tool = "file"
    else:
        actual_tool = tool_name

    if actual_tool in plugins.TOOLS:
        try:
            # Call the tool's run function with the planner's steps
            return plugins.TOOLS[actual_tool](steps)
        except Exception as e:
            return f"❌ Execution Error in {actual_tool}: {str(e)}"
    
    return f"❌ Unknown Action: {tool_name} (Mapped to: {actual_tool})"
