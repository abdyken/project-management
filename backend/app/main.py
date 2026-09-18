"""Standalone runner for local development of the assistant module only.

Once T0.3 (Dinmukhamed) ships the shared backend skeleton, replace this file:
mount ``app.assistant.router.router`` into the real FastAPI app instead of
running this one. Run locally with:

    uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI

from app.assistant.router import router as assistant_router

app = FastAPI(title="Assistant module (Serdar — AI/IS developer)")
app.include_router(assistant_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
