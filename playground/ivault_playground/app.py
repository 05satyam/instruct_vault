from __future__ import annotations
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routes.api import router as api_router
from .routes.ui import router as ui_router

app = FastAPI(title="ivault-playground", version="0.1.0")

_API_KEY = os.getenv("IVAULT_PLAYGROUND_API_KEY")

@app.middleware("http")
async def _api_key_guard(request: Request, call_next):
    if not _API_KEY:
        return await call_next(request)
    if request.url.path in ("/health",):
        return await call_next(request)
    key = request.headers.get("x-ivault-api-key")
    if key != _API_KEY:
        return HTMLResponse("Unauthorized", status_code=401)
    return await call_next(request)

app.include_router(ui_router)
app.include_router(api_router)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
