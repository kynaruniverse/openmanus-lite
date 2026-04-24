"""FastAPI web UI for OpenManus-Lite.

Streams the agent's thoughts, tool actions and observations to the browser via
Server-Sent Events. Designed to be read by ``web/static/app.js``.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.agent import Agent
from core.config import Config, ConfigError, PROVIDER_DEFAULTS
from core.logging_setup import setup_logging
from core.providers import PROVIDERS


HERE = Path(__file__).parent
STATIC_DIR = HERE / "static"

app = FastAPI(title="OpenManus-Lite")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/info")
def info() -> dict:
    """Tell the UI which providers are configured (have keys present)."""
    available = []
    for name in PROVIDERS:
        env_var, _model = PROVIDER_DEFAULTS[name]
        if env_var is None:  # ollama needs no key
            available.append({"name": name, "ready": True, "key_var": None})
        else:
            present = bool(os.environ.get(env_var, "").strip())
            available.append({"name": name, "ready": present, "key_var": env_var})
    return {
        "providers": available,
        "defaults": {
            name: {"key_var": ev, "model": mdl}
            for name, (ev, mdl) in PROVIDER_DEFAULTS.items()
        },
        "current_provider": os.environ.get("OMX_PROVIDER", "gemini"),
    }


class ChatRequest(BaseModel):
    task: str
    provider: Optional[str] = None
    model: Optional[str] = None
    mode: str = "react"
    budget: int = 0
    path: Optional[str] = None
    use_cache: bool = True


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    q: "queue.Queue[Optional[dict]]" = queue.Queue()

    def on_event(ev: dict) -> None:
        q.put(ev)

    def run_agent() -> None:
        try:
            # Per-request env overrides (server is single-process so this is
            # fine for one user; for multi-user, switch to per-request Config).
            if req.provider:
                os.environ["OMX_PROVIDER"] = req.provider
            if req.model:
                os.environ["OMX_MODEL"] = req.model

            try:
                cfg = Config.from_env()
            except ConfigError as exc:
                q.put({"type": "error", "message": str(exc)})
                return

            agent = Agent(
                config=cfg,
                mode=req.mode if req.mode in ("react", "one-shot") else "react",
                budget=max(0, int(req.budget or 0)),
                cache_enabled=True,
            )
            agent.run_task(
                req.task,
                target_path=req.path,
                use_cache=req.use_cache,
                on_event=on_event,
            )
        except Exception as exc:  # pragma: no cover - defensive
            q.put({"type": "error", "message": f"Server error: {exc}"})
        finally:
            q.put(None)

    threading.Thread(target=run_agent, daemon=True).start()

    async def stream():
        loop = asyncio.get_event_loop()
        # Initial comment so the browser opens the stream promptly.
        yield ": connected\n\n"
        while True:
            ev: Any = await loop.run_in_executor(None, q.get)
            if ev is None:
                yield "event: end\ndata: {}\n\n"
                break
            payload = json.dumps(ev, ensure_ascii=False)
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def serve(host: str = "0.0.0.0", port: int = 5000) -> None:
    """Run the FastAPI server with uvicorn."""
    setup_logging(
        level=os.environ.get("OMX_LOG_LEVEL", "INFO"),
        log_file=os.environ.get("OMX_LOG_FILE", "omx.log"),
    )
    logging.getLogger("omx").info("Starting OpenManus-Lite web UI on %s:%d", host, port)
    import uvicorn
    uvicorn.run(
        "web.server:app",
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    serve()
