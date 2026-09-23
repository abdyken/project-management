from typing import Literal

from pydantic import BaseModel, ConfigDict

ApplicantType = Literal["local", "international"]
DocumentFormat = Literal["original", "copy"]


class DocumentRequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    format: DocumentFormat
    translation: bool
    notarisation: bool
    deadline: str


class ChecklistResponse(BaseModel):
    program_id: str
    applicant_type: ApplicantType
    items: list[DocumentRequirementOut]
    warning: str | None = None
