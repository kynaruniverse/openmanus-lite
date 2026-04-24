def normalize(text):
    """Clean up user input or LLM output."""
    if not text:
        return ""
    return text.strip()
