import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analytics.router import router as analytics_router
from app.applicant.router import router as applicant_router
from app.applicant.reminders import reminders_hourly
from app.api import health
from app.api.errors import register_error_handlers
from app.assistant import embeddings
from app.assistant.router import router as assistant_router
from app.catalogue.router import router as catalogue_router
from app.catalogue.staff import router as staff_catalogue_router
from app.checklist.router import router as checklist_router
from app.config import get_settings
from app.conversation.retention import purge_daily
from app.faq.router import router as faq_router
from app.followups.router import router as inbox_router
from app.staff.router import register_staff_error_handler
from app.staff.router import router as staff_router

settings = get_settings()

_app_log_handler = logging.StreamHandler()
_app_log_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
logging.getLogger("app").addHandler(_app_log_handler)
logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    embeddings.warm_up()
    purge = asyncio.create_task(purge_daily(settings))
    reminders = asyncio.create_task(reminders_hourly(settings)) if settings.applicant_accounts_enabled else None
    try:
        yield
    finally:
        tasks = [purge, *([reminders] if reminders else [])]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Admissions Portal API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
register_staff_error_handler(app)

app.include_router(health.router, prefix="/api")
app.include_router(catalogue_router, prefix="/api")
app.include_router(checklist_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(staff_router, prefix="/api")
app.include_router(faq_router, prefix="/api")
app.include_router(inbox_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(staff_catalogue_router, prefix="/api")
app.include_router(applicant_router, prefix="/api")


@app.middleware("http")
async def private_applicant_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/applicant"):
        response.headers["Cache-Control"] = "no-store"
    return response
