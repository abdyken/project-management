from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_db_session)) -> JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )
    return JSONResponse(content={"status": "ok", "database": "ok"})


class Features(BaseModel):
    applicant_accounts: bool
    applications: bool


@router.get("/features", response_model=Features, summary="Which optional features are switched on")
def features() -> Features:
    # The frontend hides links to switched-off areas (e.g. Sprint 7 applications in production).
    settings = get_settings()
    return Features(
        applicant_accounts=settings.applicant_accounts_enabled,
        applications=settings.applicant_accounts_enabled and settings.applications_enabled,
    )
