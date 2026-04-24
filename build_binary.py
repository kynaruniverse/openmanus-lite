"""Build a standalone OpenManus-Lite executable with PyInstaller.

Usage:
  pip install pyinstaller
  python build_binary.py

The result is dropped in ``dist/omx`` (Linux/macOS) or ``dist\\omx.exe`` (Windows).
The web UI assets (``web/static/``) are bundled inside the binary, so the same
single file runs ``omx`` (CLI) and ``omx --web`` (server).
"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

ROOT = Path(__file__).parent

DATA_SEP = ";" if platform.system() == "Windows" else ":"


def main() -> int:
    try:
        import PyInstaller.__main__ as pyi
    except ImportError:
        print("PyInstaller is not installed. Run: pip install pyinstaller",
              file=sys.stderr)
        return 1

    args = [
        "main.py",
        "--name=omx",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--add-data=web/static{DATA_SEP}web/static",
        # All providers loaded lazily via importlib — tell PyInstaller about them.
        "--hidden-import=core.providers.gemini",
        "--hidden-import=core.providers.openai_provider",
        "--hidden-import=core.providers.anthropic_provider",
        "--hidden-import=core.providers.ollama",
        "--hidden-import=core.providers.openrouter",
        "--hidden-import=tools.shell_tool",
        "--hidden-import=tools.file_tool",
        "--hidden-import=tools.git_tool",
        "--hidden-import=tools.python_tool",
        "--hidden-import=tools.search_tool",
        "--hidden-import=web.server",
        "--collect-submodules=google.genai",
        "--collect-submodules=ddgs",
    ]
    pyi.run(args)
    print("\n✅ Build complete. Binary: dist/omx" +
          (".exe" if platform.system() == "Windows" else ""))
    print("Try it:  ./dist/omx --task 'list files' --path .")
    print("Or web:  ./dist/omx --web --port 5000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
