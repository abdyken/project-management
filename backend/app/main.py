from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.assistant.router import router as assistant_router
from app.catalogue.router import router as catalogue_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Admissions Portal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(catalogue_router, prefix="/api")
# US3 - FAQ assistant (Serdar); the router defines its own /api/assistant/... paths
app.include_router(assistant_router)
