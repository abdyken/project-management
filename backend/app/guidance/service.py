from __future__ import annotations

import json
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiProblem
from app.assistant.llm import LlmUnavailable, get_llm
from app.catalogue.models import Program
from app.catalogue.schemas import ProgramOut
from app.config import Settings
from app.faq.models import FaqRecord, PUBLISHED
from app.guidance.models import ProgramGuidance
from app.guidance.schemas import (
    CostIn,
    EligibilityOut,
    Guidance,
    Profile,
    RecommendationIn,
    RuleResult,
    Scope,
)


def active_program(session: Session, program_id: str) -> Program:
    program = session.get(Program, program_id)
    if not program or not program.is_active:
        raise ApiProblem(404, "PROGRAM_NOT_FOUND", "Program not found.")
    return program


def guidance_for(session: Session, program_id: str) -> Guidance:
    row = session.get(ProgramGuidance, program_id)
    return (
        Guidance.model_validate(row.payload)
        if row
        else Guidance(
            gaps=["requirements_incomplete", "credit_split_missing", "mde_rate_missing"]
        )
    )


def applies(scope: Scope, profile: Profile) -> bool:
    return all(
        getattr(scope, field) is None
        or getattr(scope, field) == getattr(profile, field)
        for field in ("applicant_type", "education_route", "track", "admission_basis")
    )


def eligibility(
    program: Program, guidance: Guidance, profile: Profile
) -> EligibilityOut:
    checks = []
    for rule in guidance.rules:
        if not applies(rule, profile):
            continue
        groups = []
        for group in rule.alternatives:
            outcomes = []
            for condition in group:
                value = getattr(profile.scores, condition.metric)
                if value is None:
                    outcomes.append("unknown")
                elif condition.minimum is not None:
                    outcomes.append("pass" if value >= condition.minimum else "fail")
                else:
                    match = (
                        value.casefold() == condition.equals.casefold()
                        if isinstance(value, str)
                        else value == condition.equals
                    )
                    outcomes.append("pass" if match else "fail")
            groups.append(
                "fail"
                if "fail" in outcomes
                else "unknown"
                if "unknown" in outcomes
                else "pass"
            )
        outcome = (
            "pass" if "pass" in groups else "unknown" if "unknown" in groups else "fail"
        )
        if rule.evidence.status != "confirmed":
            outcome = "unknown"
        checks.append(
            RuleResult(
                key=rule.key,
                status=outcome,
                alternatives=rule.alternatives,
                evidence=rule.evidence,
            )
        )
    # Credit/fee gaps do not affect eligibility; missing route coverage always does.
    covered = any(applies(scope, profile) for scope in guidance.complete_for)
    route_ok = profile.education_route in (
        {"school", "college"}
        if program.degree_level == "bachelor"
        else {"bachelor"}
        if program.degree_level == "master"
        else {"master"}
    )
    gaps = [] if covered and checks and route_ok else ["requirements_incomplete"]
    if not route_ok:
        gaps.append("education_route_mismatch")
    if program.degree_level == "master" and profile.track is None:
        gaps.append("program_track_unconfirmed")
    statuses = [check.status for check in checks]
    status = (
        "does_not_meet"
        if "fail" in statuses
        else "insufficient_data"
        if gaps or "unknown" in statuses
        else "meets_published_requirements"
    )
    return EligibilityOut(
        program_id=program.program_id, status=status, checks=checks, gaps=gaps
    )


def cost_estimate(program: Program, guidance: Guidance, body: CostIn) -> dict:
    currency = body.currency.lower()
    professional_rate = getattr(program, f"tuition_per_ects_{currency}")
    professional_source = guidance.sources.get(f"tuition_per_ects_{currency}")
    gaps = []
    if guidance.language_tariffs:
        tariff = next(
            (
                t
                for t in guidance.language_tariffs
                if body.language_group
                and t.language_group.casefold() == body.language_group.casefold()
            ),
            None,
        )
        professional_rate = (
            getattr(tariff, currency)
            if tariff and tariff.evidence.status == "confirmed"
            else None
        )
        professional_source = tariff.evidence if tariff else None
        if not tariff:
            gaps.append("language_group_required")
    elif body.language_group:
        # A language choice may not silently select an unrelated tariff.
        gaps.append("language_tariff_unconfirmed")
        professional_rate = None
    if not professional_source or professional_source.status != "confirmed":
        professional_rate = None
    if (
        not guidance.language_tariffs
        and getattr(guidance, f"professional_{currency}") != professional_rate
    ):
        professional_rate = None
        gaps.append("professional_tariff_needs_confirmation")
    mde_rate = getattr(guidance, f"mde_{currency}")
    if not guidance.mde_evidence or guidance.mde_evidence.status != "confirmed":
        mde_rate = None
    components = []
    for component, credits, rate, source in (
        (
            "professional",
            body.professional_ects,
            professional_rate,
            professional_source,
        ),
        ("mde", body.mde_ects, mde_rate, guidance.mde_evidence),
    ):
        if not credits:
            continue
        if rate is None:
            gaps.append(f"{component}_rate_missing")
        components.append(
            {
                "component": component,
                "ects": credits,
                "rate": rate,
                "amount": credits * rate if rate is not None else None,
                "evidence": source.model_dump(mode="json") if source else None,
            }
        )
    known = sum(c["amount"] for c in components if c["amount"] is not None)
    total = known if all(c["amount"] is not None for c in components) else None
    return {
        "program_id": program.program_id,
        "currency": body.currency,
        "components": components,
        "known_subtotal": known,
        "estimated_total": total,
        "gaps": list(dict.fromkeys(gaps)),
        "assumptions": [
            "current_rates_only",
            "user_supplied_credit_split",
            "discounts_not_applied",
            "not_full_degree_quote",
        ],
        "published_total_ects": guidance.total_ects
        if guidance.credits_evidence and guidance.credits_evidence.status == "confirmed"
        else None,
        "credits_evidence": guidance.credits_evidence,
        "is_binding_quote": False,
    }


# Per interest: core terms name the subject itself, related terms an adjacent field
# ("Multimedia and AI journalism" is media first, "Statistics and Data Science" is
# science first). See _interest_score for the weights.
INTEREST_TERMS = {
    "computing": (
        ("computer", "software", "information", "informatics", "computational"),
        ("data", "multimedia"),
    ),
    "business": (
        ("business", "finance", "account", "management", "econom", "marketing", "mba"),
        (),
    ),
    "law": (("law", "legal", "jurisprudence"), ()),
    "education": (("pedagog", "education", "teaching"), ()),
    "languages": (
        ("language", "philolog", "translation", "literature"),
        ("international relations",),
    ),
    "science": (
        ("mathemat", "physics", "chemistry", "biology", "statistics"),
        ("science",),
    ),
    "media": (("media", "journalism", "multimedia"), ()),
    "psychology": (("psycholog",), ()),
}


def _interest_score(interest: str, title: str, faculty: str) -> int:
    """Core title term 10, related title term 5; +1 when the title starts with a core
    term (the programme's main subject); +2 when the faculty matches. 0 = no match."""
    core, related = INTEREST_TERMS[interest]
    score = 0
    if any(term in title for term in core):
        score = 10 + (1 if title.startswith(core) else 0)
    elif any(term in title for term in related):
        score = 5
    if any(term in faculty for term in core + related):
        score += 2
    return score


def recommendations(
    session: Session, body: RecommendationIn, settings: Settings
) -> dict:
    ranked = []
    for program in session.scalars(
        select(Program)
        .where(Program.is_active.is_(True), Program.degree_level == body.degree_level)
        .order_by(Program.program_id)
    ):
        title, faculty = program.title.casefold(), program.faculty.casefold()
        interest_scores = {
            interest: _interest_score(interest, title, faculty)
            for interest in dict.fromkeys(body.interests)
        }
        matches = [interest for interest, score in interest_scores.items() if score]
        if not matches:
            continue
        result = eligibility(program, guidance_for(session, program.program_id), body)
        if result.status == "does_not_meet":
            continue
        if (
            body.teaching_language
            and program.language
            and body.teaching_language.casefold() not in program.language.casefold()
        ):
            continue
        gaps = list(result.gaps)
        if body.teaching_language and not program.language:
            gaps.append("language_missing")
        matches.sort(key=lambda interest: -interest_scores[interest])
        reasons = [f"interest:{interest}" for interest in matches]
        score = sum(interest_scores.values()) + (
            3 if result.status == "meets_published_requirements" else 0
        )
        ranked.append(
            (
                score,
                {
                    "program": ProgramOut.model_validate(program),
                    "eligibility": result,
                    "reasons": reasons,
                    "gaps": gaps,
                },
            )
        )
    ranked.sort(key=lambda pair: (-pair[0], pair[1]["program"].program_id))
    items = [item for _, item in ranked[:3]]
    mode = "template"
    llm = get_llm(settings)
    if llm and items:
        # The model selects existing fact labels ONLY. No generated rule, number or
        # free-text admission assertion can reach the applicant.
        facts = [
            {
                "program_id": item["program"].program_id,
                "title": item["program"].title,
                "reasons": item["reasons"],
            }
            for item in items
        ]
        try:
            generation = llm.generate(
                "Explain the program matches by selecting the most relevant supplied reason labels. Return exactly the given program ids; never add facts or change eligibility. No personal scores are supplied.",
                json.dumps({"language": body.language, "facts": facts}),
                {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "program_id": {"type": "string"},
                                    "reasons": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": ["program_id", "reasons"],
                            },
                        }
                    },
                    "required": ["items"],
                },
            )
            selected = json.loads(generation.text)["items"]
            by_id = {item["program_id"]: item["reasons"] for item in selected}
            if (
                len(selected) == len(items)
                and set(by_id) == {item["program"].program_id for item in items}
                and all(
                    by_id[item["program"].program_id]
                    and set(by_id[item["program"].program_id]) <= set(item["reasons"])
                    for item in items
                )
            ):
                for item in items:
                    item["reasons"] = list(
                        dict.fromkeys(by_id[item["program"].program_id])
                    )
                mode = "grounded_model"
        except (LlmUnavailable, ValueError, KeyError, TypeError):
            pass
    return {"items": items, "explanation_mode": mode, "admission_guaranteed": False}


FUNDING_IDS = {
    "faq-019",
    "faq-036",
    "faq-037",
    "faq-038",
    "faq-045",
    "faq-046",
    "faq-073",
}


def funding(
    session: Session,
    language: str,
    degree_level: str | None,
    applicant_type: str | None,
) -> dict:
    items = []
    for row in session.scalars(
        select(FaqRecord)
        .where(FaqRecord.status == PUBLISHED)
        .order_by(FaqRecord.faq_id)
    ):
        if row.faq_id not in FUNDING_IDS and row.category not in {
            "funding",
            "scholarships",
            "discounts",
            "grants",
        }:
            continue
        if degree_level and row.degrees and degree_level not in row.degrees:
            continue
        if (
            applicant_type
            and row.applicant_types
            and applicant_type not in row.applicant_types
        ):
            continue
        translated = language != "en" and all(
            getattr(row, f"{field}_{language}")
            for field in ("question", "answer", "source_link")
        )
        suffix = f"_{language}" if translated else ""
        years = re.findall(r"20\d\d", row.answer)
        outdated = bool(years) and max(map(int, years)) < date.today().year
        items.append(
            {
                "faq_id": row.faq_id,
                "title": getattr(row, "question" + suffix),
                "text": getattr(row, "answer" + suffix),
                "source_url": getattr(row, "source_link" + suffix),
                "last_checked": row.last_update,
                "content_language": language if translated else "en",
                "translation_missing": language != "en" and not translated,
                "status": "historical" if outdated else "verify_current_campaign",
                "degrees": row.degrees,
                "applicant_types": row.applicant_types,
            }
        )
    return {"items": items, "award_guaranteed": False}
