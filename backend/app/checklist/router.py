from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import (
    DATABASE_UNAVAILABLE_RESPONSE,
    INVALID_REQUEST_RESPONSE,
    PROGRAM_NOT_FOUND,
    ErrorResponse,
)
from app.catalogue.service import get_active_program
from app.checklist.schemas import ApplicantType, ChecklistResponse, DocumentRequirementOut
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import get_settings
from app.db import get_db_session
from app.followups.service import log_missing_documents

router = APIRouter(tags=["checklist"])


@router.get(
    "/programs/{program_id}/checklist",
    response_model=ChecklistResponse,
    responses={
        404: {"model": ErrorResponse, "description": "No active program with this id."},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Get a programme's document checklist",
)
def get_checklist(
    session: Annotated[Session, Depends(get_db_session)],
    program_id: Annotated[str, Path(max_length=64)],
    applicant_type: Annotated[ApplicantType, Query()],
) -> ChecklistResponse | JSONResponse:
    if get_active_program(session, program_id) is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error_code=PROGRAM_NOT_FOUND, message="Program not found.").model_dump(),
        )

    requirements = get_requirements(session, program_id, applicant_type)
    if not requirements:
        log_missing_documents(session, program_id, applicant_type)
        return ChecklistResponse(
            program_id=program_id,
            applicant_type=applicant_type,
            items=[],
            warning=MISSING_REQUIREMENTS_WARNING,
            contact=get_settings().admissions_office_contact,
        )

    return ChecklistResponse(
        program_id=program_id,
        applicant_type=applicant_type,
        items=[
            DocumentRequirementOut(
                name=requirement.name,
                format=requirement.document_format,
                translation=requirement.translation_required,
                notarisation=requirement.notarisation_required,
                deadline=requirement.deadline,
            )
            for requirement in requirements
        ],
    )
