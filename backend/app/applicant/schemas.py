from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.assistant.schemas import Language
from app.catalogue.schemas import ProgramOut
from app.checklist.schemas import ApplicantType, DocumentRequirementOut
from app.staff.service import normalize_email


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    # Ignored: the password is chosen on the verification page, by whoever opens the link
    # from the inbox. Still accepted so older clients keep working.
    password: str | None = Field(default=None, max_length=200)
    language: Language = "en"

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        import re

        value = normalize_email(value)
        if not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value
        ):
            raise ValueError("Enter a valid e-mail address.")
        return value


class VerifyRequest(BaseModel):
    token: str = Field(min_length=20, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    # Set here, not at registration: only the inbox owner reaches this page.
    password: str = Field(min_length=10, max_length=200)


class ApplicantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    language: Language
    reminders_enabled: bool


class PreferencesIn(BaseModel):
    language: Language
    reminders_enabled: bool


class MessageOut(BaseModel):
    message: str


class TrackerItem(DocumentRequirementOut):
    id: int
    prepared: bool


class SavedChecklistOut(BaseModel):
    program: ProgramOut
    applicant_type: ApplicantType
    items: list[TrackerItem]
    prepared: int
    total: int
    warning: str | None
    contact: str | None


class SavedProgramsOut(BaseModel):
    items: list[SavedChecklistOut]


class ProgressIn(BaseModel):
    prepared: bool
