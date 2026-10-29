from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.catalogue.schemas import ProgramOut

Language = Literal["en", "ru", "kk"]
ApplicantType = Literal["local", "international"]
Route = Literal["school", "college", "bachelor", "master"]
Metric = Literal[
    "unt_total",
    "ct_total",
    "gpa",
    "phd_total",
    "toefl_ibt",
    "toefl_pbt",
    "toeic",
    "duolingo",
    "work_months",
    "ielts_overall",
    "ielts_component_min",
    "sdu_english",
    "interview",
    "special_exam",
    "creative_exam",
    "kaztest",
    "subject_pair",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictModel):
    url: str = Field(max_length=1000, pattern=r"^https://")
    quote: str = Field(min_length=1, max_length=6000)
    academic_year: str = Field(default="2026-2027", pattern=r"^20\d{2}-20\d{2}$")
    checked_on: date
    status: Literal["confirmed", "pending", "conflict"] = "confirmed"


class Scope(StrictModel):
    applicant_type: ApplicantType | None = None
    education_route: Route | None = None
    track: Literal["scientific", "profile"] | None = None
    admission_basis: Literal["paid", "grant"] | None = None


class Condition(StrictModel):
    metric: Metric
    minimum: float | None = Field(default=None, ge=0, le=1000, allow_inf_nan=False)
    equals: str | bool | None = None

    @model_validator(mode="after")
    def one_operator(self):
        if (self.minimum is None) == (self.equals is None):
            raise ValueError("Use exactly one of minimum / equals")
        numeric = {
            "unt_total",
            "ct_total",
            "gpa",
            "phd_total",
            "toefl_ibt",
            "toefl_pbt",
            "toeic",
            "duolingo",
            "work_months",
            "ielts_overall",
            "ielts_component_min",
        }
        if (self.metric in numeric) != (self.minimum is not None):
            raise ValueError(
                "Numeric metrics require minimum; other metrics require equals"
            )
        if self.metric == "subject_pair" and not isinstance(self.equals, str):
            raise ValueError("subject_pair requires a string")
        if self.metric not in numeric | {"subject_pair"} and not isinstance(
            self.equals, bool
        ):
            raise ValueError("Exam results require a boolean")
        return self


class Rule(Scope):
    key: str = Field(min_length=1, max_length=100)
    # OR of groups; each group is an AND (IELTS overall AND every component).
    alternatives: list[list[Condition]] = Field(min_length=1, max_length=10)
    evidence: Evidence

    @model_validator(mode="after")
    def nonempty_groups(self):
        if any(not group or len(group) > 10 for group in self.alternatives):
            raise ValueError("Each alternative needs 1-10 conditions")
        return self


class LanguageTariff(StrictModel):
    language_group: str = Field(min_length=1, max_length=50)
    kzt: int | None = Field(default=None, ge=0, le=10000000)
    usd: int | None = Field(default=None, ge=0, le=100000)
    evidence: Evidence


class Guidance(StrictModel):
    professional_kzt: int | None = Field(default=None, ge=0)
    professional_usd: int | None = Field(default=None, ge=0)
    rules: list[Rule] = Field(default_factory=list, max_length=60)
    # Only the office can declare a route fully covered after checking ALL rules.
    complete_for: list[Scope] = Field(default_factory=list, max_length=20)
    total_ects: int | None = Field(default=None, ge=1, le=1000)
    credits_evidence: Evidence | None = None
    mde_kzt: int | None = Field(default=None, ge=0, le=10000000)
    mde_usd: int | None = Field(default=None, ge=0, le=100000)
    mde_evidence: Evidence | None = None
    language_tariffs: list[LanguageTariff] = Field(default_factory=list, max_length=10)
    sources: dict[str, Evidence] = Field(default_factory=dict, max_length=60)
    gaps: list[str] = Field(default_factory=list, max_length=60)

    @model_validator(mode="after")
    def sourced_values(self):
        if self.total_ects is not None and self.credits_evidence is None:
            raise ValueError("Credit count needs evidence")
        if (
            self.mde_kzt is not None or self.mde_usd is not None
        ) and self.mde_evidence is None:
            raise ValueError("MDE tariff needs evidence")
        groups = [t.language_group.casefold() for t in self.language_tariffs]
        if len(groups) != len(set(groups)):
            raise ValueError("Language groups must be unique")
        return self


class Scores(StrictModel):
    phd_total: int | None = Field(default=None, ge=0, le=100)
    toefl_ibt: int | None = Field(default=None, ge=0, le=120)
    toefl_pbt: int | None = Field(default=None, ge=0, le=677)
    toeic: int | None = Field(default=None, ge=0, le=990)
    duolingo: int | None = Field(default=None, ge=0, le=160)
    work_months: int | None = Field(default=None, ge=0, le=1000)
    kaztest: bool | None = None
    unt_total: int | None = Field(default=None, ge=0, le=140)
    ct_total: int | None = Field(default=None, ge=0, le=150)
    gpa: float | None = Field(default=None, ge=0, le=4, allow_inf_nan=False)
    ielts_overall: float | None = Field(default=None, ge=0, le=9, allow_inf_nan=False)
    ielts_component_min: float | None = Field(
        default=None, ge=0, le=9, allow_inf_nan=False
    )
    sdu_english: bool | None = None
    interview: bool | None = None
    special_exam: bool | None = None
    creative_exam: bool | None = None
    subject_pair: str | None = Field(default=None, max_length=100)


class Profile(StrictModel):
    applicant_type: ApplicantType = "local"
    education_route: Route = "school"
    track: Literal["scientific", "profile"] | None = None
    admission_basis: Literal["paid", "grant"] = "paid"
    scores: Scores = Field(default_factory=Scores)
    language: Language = "en"


class EligibilityIn(Profile):
    program_id: str = Field(min_length=1, max_length=64)


class RuleResult(StrictModel):
    key: str
    status: Literal["pass", "fail", "unknown"]
    alternatives: list[list[Condition]]
    evidence: Evidence


class EligibilityOut(StrictModel):
    program_id: str
    status: Literal[
        "meets_published_requirements", "does_not_meet", "insufficient_data"
    ]
    checks: list[RuleResult]
    gaps: list[str]
    admission_guaranteed: bool = False


class CostIn(StrictModel):
    currency: Literal["KZT", "USD"] = "KZT"
    professional_ects: int = Field(ge=0, le=1000)
    mde_ects: int = Field(default=0, ge=0, le=1000)
    language_group: str | None = Field(default=None, max_length=50)
    language: Language = "en"

    @model_validator(mode="after")
    def credits(self):
        if not 1 <= self.professional_ects + self.mde_ects <= 1000:
            raise ValueError("Enter 1-1000 credits in total")
        return self


class RecommendationIn(Profile):
    degree_level: Literal["bachelor", "master", "phd"] = "bachelor"
    interests: list[str] = Field(min_length=1, max_length=8)
    teaching_language: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def valid_interests(self):
        allowed = {
            "computing",
            "business",
            "law",
            "education",
            "languages",
            "science",
            "media",
            "psychology",
        }
        if not set(self.interests) <= allowed:
            raise ValueError("Unknown interest")
        return self


class CostComponent(StrictModel):
    component: Literal["professional", "mde"]
    ects: int
    rate: int | None
    amount: int | None
    evidence: Evidence | None


class CostOut(StrictModel):
    program_id: str
    currency: Literal["KZT", "USD"]
    components: list[CostComponent]
    known_subtotal: int
    estimated_total: int | None
    gaps: list[str]
    assumptions: list[str]
    published_total_ects: int | None
    credits_evidence: Evidence | None
    is_binding_quote: bool = False


class RecommendationItem(StrictModel):
    program: ProgramOut
    eligibility: EligibilityOut
    reasons: list[str]
    gaps: list[str]


class RecommendationsOut(StrictModel):
    items: list[RecommendationItem]
    explanation_mode: Literal["template", "grounded_model"]
    admission_guaranteed: bool = False


class FundingItem(StrictModel):
    faq_id: str
    title: str
    text: str
    source_url: str
    last_checked: str
    content_language: Language
    translation_missing: bool
    status: Literal["historical", "verify_current_campaign"]
    degrees: list[str]
    applicant_types: list[str]


class FundingOut(StrictModel):
    items: list[FundingItem]
    award_guaranteed: bool = False
