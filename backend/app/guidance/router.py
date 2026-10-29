from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.errors import (
    DATABASE_UNAVAILABLE_RESPONSE,
    INVALID_REQUEST_RESPONSE,
    ErrorResponse,
)

from app.applicant.service import now
from app.catalogue.schemas import DegreeLevel
from app.config import get_settings
from app.db import get_db_session
from app.guidance.models import ProgramGuidance
from app.guidance.schemas import (
    CostIn,
    CostOut,
    EligibilityIn,
    EligibilityOut,
    FundingOut,
    Guidance,
    Language,
    RecommendationIn,
    RecommendationsOut,
)
from app.guidance.service import (
    active_program,
    cost_estimate,
    eligibility,
    funding,
    guidance_for,
    recommendations,
)
from app.staff.models import StaffUser
from app.staff.router import STAFF_RESPONSES, require_staff

router = APIRouter(
    tags=["admissions guidance"],
    responses={
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
        404: {"model": ErrorResponse},
    },
)
Db = Annotated[Session, Depends(get_db_session)]
Staff = Annotated[StaffUser, Depends(require_staff())]


@router.post("/eligibility/check", response_model=EligibilityOut)
def check(body: EligibilityIn, session: Db):
    return eligibility(
        active_program(session, body.program_id),
        guidance_for(session, body.program_id),
        body,
    )


@router.post("/recommendations", response_model=RecommendationsOut)
def recommend(body: RecommendationIn, session: Db):
    return recommendations(session, body, get_settings())


@router.post("/programs/{program_id}/cost-estimate", response_model=CostOut)
def estimate(program_id: str, body: CostIn, session: Db):
    return cost_estimate(
        active_program(session, program_id), guidance_for(session, program_id), body
    )


@router.get("/programs/{program_id}/guidance", response_model=Guidance)
def public_guidance(program_id: str, session: Db):
    active_program(session, program_id)
    return guidance_for(session, program_id)


@router.get("/funding", response_model=FundingOut)
def funding_guide(
    session: Db,
    language: Language = "en",
    degree_level: DegreeLevel | None = None,
    applicant_type: Literal["local", "international"] | None = None,
):
    return funding(session, language, degree_level, applicant_type)


@router.get(
    "/staff/programs/{program_id}/guidance",
    response_model=Guidance,
    responses=STAFF_RESPONSES,
)
def staff_guidance(program_id: str, session: Db, _: Staff):
    from app.catalogue.models import Program
    from app.api.errors import ApiProblem

    if session.get(Program, program_id) is None:
        raise ApiProblem(404, "PROGRAM_NOT_FOUND", "Program not found.")
    return guidance_for(session, program_id)


@router.put(
    "/staff/programs/{program_id}/guidance",
    response_model=Guidance,
    responses=STAFF_RESPONSES,
)
def update_guidance(program_id: str, body: Guidance, session: Db, user: Staff):
    staff_guidance(program_id, session, user)
    row = session.get(ProgramGuidance, program_id)
    if row is None:
        row = ProgramGuidance(program_id=program_id)
        session.add(row)
    from app.catalogue.models import Program

    program = session.get(Program, program_id)
    body.professional_kzt = program.tuition_per_ects_kzt
    body.professional_usd = program.tuition_per_ects_usd
    row.payload = body.model_dump(mode="json")
    row.updated_by_id, row.updated_at = user.id, now()
    session.commit()
    return body
