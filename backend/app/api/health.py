from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )
    return JSONResponse(content={"status": "ok", "database": "ok"})
