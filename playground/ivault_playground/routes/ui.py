from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()

_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "index.html"

@router.get("/", response_class=HTMLResponse)
def index() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")
