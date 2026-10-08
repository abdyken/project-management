import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.errors import register_error_handlers
from app.assistant import embeddings
from app.assistant.router import router as assistant_router
from app.catalogue.router import router as catalogue_router
from app.checklist.router import router as checklist_router
from app.config import get_settings
from app.conversation.retention import purge_daily

settings = get_settings()

_app_log_handler = logging.StreamHandler()
_app_log_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
logging.getLogger("app").addHandler(_app_log_handler)
logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    embeddings.warm_up()
    purge = asyncio.create_task(purge_daily(settings))
    yield
    purge.cancel()


app = FastAPI(title="Admissions Portal API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(health.router, prefix="/api")
app.include_router(catalogue_router, prefix="/api")
app.include_router(checklist_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
