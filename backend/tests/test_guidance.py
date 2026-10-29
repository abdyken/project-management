import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.assistant.llm import Generation, LlmUnavailable
from app.catalogue.models import Program
from app.db import get_db_session
from app.faq.models import FaqRecord
from app.guidance.models import ProgramGuidance
from app.guidance.schemas import Guidance
from app.main import app
from app.staff.service import create_user

EVIDENCE = {
    "url": "https://sdu.edu.kz/en/admission-3-2/",
    "quote": "Test fixture: minimum 80",
    "academic_year": "2026-2027",
    "checked_on": "2026-10-29",
    "status": "confirmed",
}
RULE = {
    "key": "paid_unt",
    "applicant_type": "local",
    "education_route": "school",
    "admission_basis": "paid",
    "alternatives": [[{"metric": "unt_total", "minimum": 80}]],
    "evidence": EVIDENCE,
}


@pytest.fixture
def client(catalogue_session):
    session = catalogue_session
    session.add_all(
        [
            Program(
                program_id="cs",
                title="Computer Science",
                faculty="Computing",
                degree_level="bachelor",
                language="English",
                tuition_per_ects_kzt=1000,
                tuition_per_ects_usd=10,
            ),
            Program(
                program_id="law", title="Law", faculty="Law", degree_level="bachelor"
            ),
            Program(
                program_id="archive",
                title="Computer Science",
                faculty="Computing",
                degree_level="bachelor",
                is_active=False,
            ),
        ]
    )
    session.flush()
    session.add(
        ProgramGuidance(
            program_id="cs",
            payload=Guidance(
                professional_kzt=1000,
                professional_usd=10,
                rules=[RULE],
                complete_for=[
                    {
                        "applicant_type": "local",
                        "education_route": "school",
                        "admission_basis": "paid",
                    }
                ],
                mde_kzt=500,
                mde_usd=5,
                mde_evidence=EVIDENCE,
                sources={
                    "tuition_per_ects_kzt": EVIDENCE,
                    "tuition_per_ects_usd": EVIDENCE,
                },
            ).model_dump(mode="json"),
        )
    )
    session.flush()
    app.dependency_overrides[get_db_session] = lambda: session
    # No lifespan for the actual requests: avoid unrelated embedding workers.
    try:
        yield TestClient(app, base_url="https://localhost"), session
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "score,status",
    [
        (79, "does_not_meet"),
        (80, "meets_published_requirements"),
        (81, "meets_published_requirements"),
        (None, "insufficient_data"),
    ],
)
def test_threshold_boundaries(client, score, status):
    c, _ = client
    result = c.post(
        "/api/eligibility/check",
        json={"program_id": "cs", "scores": {"unt_total": score}},
    )
    assert result.status_code == 200, result.text
    assert result.json()["status"] == status
    assert result.json()["admission_guaranteed"] is False


def test_rule_scope_unknown_coverage_and_evidence(client):
    c, session = client
    for extra in (
        {"admission_basis": "grant"},
        {"applicant_type": "international"},
        {"education_route": "college"},
    ):
        result = c.post(
            "/api/eligibility/check",
            json={"program_id": "cs", "scores": {"unt_total": 0}, **extra},
        ).json()
        assert result["status"] == "insufficient_data" and result["checks"] == []
    row = session.get(ProgramGuidance, "cs")
    payload = dict(row.payload)
    payload["complete_for"] = []
    row.payload = payload
    session.flush()
    assert (
        c.post(
            "/api/eligibility/check",
            json={"program_id": "cs", "scores": {"unt_total": 90}},
        ).json()["status"]
        == "insufficient_data"
    )
    payload = {
        **payload,
        "rules": [{**RULE, "evidence": {**EVIDENCE, "status": "conflict"}}],
    }
    row.payload = payload
    session.flush()
    assert (
        c.post(
            "/api/eligibility/check",
            json={"program_id": "cs", "scores": {"unt_total": 0}},
        ).json()["checks"][0]["status"]
        == "unknown"
    )


@pytest.mark.parametrize(
    "scores,outcome",
    [
        ({"ielts_overall": 6, "ielts_component_min": 5}, "pass"),
        ({"ielts_overall": 5, "sdu_english": True}, "pass"),
        ({"ielts_overall": 6}, "unknown"),
        ({"ielts_overall": 4, "sdu_english": False}, "fail"),
    ],
)
def test_english_or_and_alternatives(client, scores, outcome):
    c, session = client
    row = session.get(ProgramGuidance, "cs")
    row.payload = Guidance(
        rules=[
            {
                **RULE,
                "alternatives": [
                    [
                        {"metric": "ielts_overall", "minimum": 5.5},
                        {"metric": "ielts_component_min", "minimum": 5},
                    ],
                    [{"metric": "sdu_english", "equals": True}],
                ],
            }
        ]
    ).model_dump(mode="json")
    session.flush()
    assert (
        c.post(
            "/api/eligibility/check", json={"program_id": "cs", "scores": scores}
        ).json()["checks"][0]["status"]
        == outcome
    )


@pytest.mark.parametrize(
    "scores",
    [
        {"unt_total": -1},
        {"unt_total": 141},
        {"gpa": 4.1},
        {"ielts_overall": 10},
        {"invented": 5},
    ],
)
def test_score_validation(client, scores):
    assert (
        client[0]
        .post("/api/eligibility/check", json={"program_id": "cs", "scores": scores})
        .status_code
        == 422
    )


def test_split_cost_currency_and_unknown_rates(client):
    c, session = client
    for currency, total in [("KZT", 25000), ("USD", 250)]:
        response = c.post(
            "/api/programs/cs/cost-estimate",
            json={"professional_ects": 20, "mde_ects": 10, "currency": currency},
        )
        assert response.status_code == 200
        assert response.json()["estimated_total"] == total
        assert response.json()["is_binding_quote"] is False
    payload = dict(session.get(ProgramGuidance, "cs").payload)
    payload["mde_kzt"] = None
    session.get(ProgramGuidance, "cs").payload = payload
    session.flush()
    result = c.post(
        "/api/programs/cs/cost-estimate", json={"professional_ects": 20, "mde_ects": 10}
    ).json()
    assert result["estimated_total"] is None and result["known_subtotal"] == 20000
    assert "mde_rate_missing" in result["gaps"]
    # An empty programme fee cannot become zero, including an MDE-only estimate.
    assert (
        c.post(
            "/api/programs/law/cost-estimate", json={"professional_ects": 30}
        ).json()["estimated_total"]
        is None
    )


def test_language_tariffs_do_not_fall_back_to_another_group(client):
    c, session = client
    row = session.get(ProgramGuidance, "cs")
    row.payload = {
        **row.payload,
        "language_tariffs": [
            {"language_group": "Kazakh", "kzt": 900, "usd": 8, "evidence": EVIDENCE},
            {"language_group": "English", "kzt": 1200, "usd": 12, "evidence": EVIDENCE},
        ],
    }
    session.flush()
    assert (
        c.post("/api/programs/cs/cost-estimate", json={"professional_ects": 10}).json()[
            "estimated_total"
        ]
        is None
    )
    for group, total in [("Kazakh", 9000), ("English", 12000)]:
        assert (
            c.post(
                "/api/programs/cs/cost-estimate",
                json={"professional_ects": 10, "language_group": group},
            ).json()["estimated_total"]
            == total
        )


def test_changed_catalogue_rate_requires_reconfirmed_evidence(client):
    c, session = client
    session.get(Program, "cs").tuition_per_ects_kzt = 1200
    session.flush()
    response = c.post(
        "/api/programs/cs/cost-estimate", json={"professional_ects": 10}
    ).json()
    assert response["estimated_total"] is None
    assert "professional_tariff_needs_confirmation" in response["gaps"]


@pytest.mark.parametrize(
    "body",
    [
        {"professional_ects": -1},
        {"professional_ects": 0},
        {"professional_ects": 1.5},
        {"professional_ects": 1001},
        {"professional_ects": 1, "currency": "EUR"},
    ],
)
def test_invalid_costs(client, body):
    assert (
        client[0].post("/api/programs/cs/cost-estimate", json=body).status_code == 422
    )


def test_missing_and_archived_programs(client):
    c, _ = client
    for code in ("missing", "archive"):
        assert (
            c.post("/api/eligibility/check", json={"program_id": code}).status_code
            == 404
        )
        assert (
            c.post(
                f"/api/programs/{code}/cost-estimate", json={"professional_ects": 10}
            ).status_code
            == 404
        )


def test_recommendations_exclude_failure_archive_and_language_mismatch(client):
    c, _ = client
    body = {"interests": ["computing"], "scores": {"unt_total": 90}}
    result = c.post("/api/recommendations", json=body).json()
    assert [i["program"]["program_id"] for i in result["items"]] == ["cs"]
    assert result["explanation_mode"] == "template"
    assert (
        c.post(
            "/api/recommendations", json={**body, "scores": {"unt_total": 70}}
        ).json()["items"]
        == []
    )
    assert (
        c.post(
            "/api/recommendations", json={**body, "teaching_language": "Kazakh"}
        ).json()["items"]
        == []
    )
    assert (
        c.post("/api/recommendations", json={"interests": ["made up"]}).status_code
        == 422
    )


def test_model_explanation_cannot_add_facts(client, monkeypatch):
    c, _ = client

    class Fake:
        text = '{"items":[{"program_id":"cs","reasons":["interest:computing"]}]}'

        def generate(self, *args):
            assert "unt_total" not in args[1] and "gpa" not in args[1]
            return Generation(self.text, "test", None, None, 0)

    fake = Fake()
    monkeypatch.setattr("app.guidance.service.get_llm", lambda _: fake)
    assert (
        c.post("/api/recommendations", json={"interests": ["computing"]}).json()[
            "explanation_mode"
        ]
        == "grounded_model"
    )
    fake.text = '{"items":[{"program_id":"cs","reasons":["guaranteed grant"]}]}'
    result = c.post("/api/recommendations", json={"interests": ["computing"]}).json()
    assert result["explanation_mode"] == "template" and "guaranteed grant" not in str(
        result
    )
    monkeypatch.setattr(
        fake, "generate", lambda *args: (_ for _ in ()).throw(LlmUnavailable())
    )
    assert (
        c.post("/api/recommendations", json={"interests": ["computing"]}).status_code
        == 200
    )


def test_funding_uses_published_database_content(client):
    c, session = client
    row = session.get(FaqRecord, "faq-045")
    row.answer = "Office updated discount information for 2026-2027"
    row.answer_ru = None
    session.flush()
    result = c.get("/api/funding?language=ru").json()
    item = next(i for i in result["items"] if i["faq_id"] == "faq-045")
    assert item["text"] == row.answer and item["translation_missing"] is True
    row.status = "retired"
    session.flush()
    assert "faq-045" not in [i["faq_id"] for i in c.get("/api/funding").json()["items"]]


def test_staff_guidance_requires_login_and_persists(client):
    c, session = client
    path = "/api/staff/programs/cs/guidance"
    assert c.get(path).status_code == c.put(path, json={}).status_code == 401
    create_user(
        session, "guide@sdu.edu.kz", "Officer", "officer", "a safe test password"
    )
    assert (
        c.post(
            "/api/staff/login",
            json={"email": "guide@sdu.edu.kz", "password": "a safe test password"},
        ).status_code
        == 200
    )
    payload = c.get(path).json()
    payload["mde_kzt"] = 700
    assert c.put(path, json=payload).status_code == 200
    assert c.get("/api/programs/cs/guidance").json()["mde_kzt"] == 700
    payload["mde_evidence"] = None
    assert c.put(path, json=payload).status_code == 422


def test_all_64_seed_rows_have_sources_and_seed_never_overwrites(catalogue_session):
    from scripts.import_catalogue import import_catalogue, load_source, DEFAULT_SOURCE
    from scripts.seed_guidance import seed_guidance, SOURCE

    session = catalogue_session
    source = json.loads(SOURCE.read_text())
    assert len(source["programs"]) == 64
    import_catalogue(session, load_source(DEFAULT_SOURCE))
    assert seed_guidance(session) == 64
    for row in session.scalars(select(ProgramGuidance)):
        guidance = Guidance.model_validate(row.payload)
        assert guidance.sources and guidance.gaps and not guidance.complete_for
    row = session.get(ProgramGuidance, "6B06102")
    row.payload = {**row.payload, "gaps": ["staff edit"]}
    session.flush()
    assert seed_guidance(session) == 0
    assert session.get(ProgramGuidance, "6B06102").payload["gaps"] == ["staff edit"]


@pytest.mark.parametrize(
    "score,status",
    [(74, "does_not_meet"), (75, "insufficient_data"), (76, "insufficient_data")],
)
def test_published_doctoral_threshold_and_alternative_certificate(score, status):
    from scripts.seed_guidance import SOURCE
    from app.guidance.schemas import Profile
    from app.guidance.service import eligibility

    data = json.loads(SOURCE.read_text())["programs"]["8D06102"]
    result = eligibility(
        Program(program_id="8D06102", degree_level="phd"),
        Guidance.model_validate(data),
        Profile(
            education_route="master",
            scores={
                "phd_total": score,
                "toefl_ibt": 35,
                "kaztest": True,
                "work_months": 9,
            },
        ),
    )
    assert result.status == status
    assert (
        next(c for c in result.checks if c.key == "doctoral_language").status == "pass"
    )


def test_unknown_master_track_applicability_cannot_disqualify():
    from scripts.seed_guidance import SOURCE
    from app.guidance.schemas import Profile
    from app.guidance.service import eligibility

    data = json.loads(SOURCE.read_text())["programs"]["7M06101"]
    result = eligibility(
        Program(program_id="7M06101", degree_level="master"),
        Guidance.model_validate(data),
        Profile(
            education_route="bachelor", track="scientific", scores={"ct_total": 60}
        ),
    )
    assert result.status == "insufficient_data"
    assert result.checks[0].status == "unknown"


@pytest.mark.parametrize(
    "pair,status",
    [("math_informatics", "insufficient_data"), ("math_geography", "does_not_meet")],
)
def test_published_subject_pairs_are_scoped_to_local_school_applicants(pair, status):
    from scripts.seed_guidance import SOURCE
    from app.guidance.schemas import Profile
    from app.guidance.service import eligibility

    data = json.loads(SOURCE.read_text())["programs"]["6B06102"]
    result = eligibility(
        Program(program_id="6B06102", degree_level="bachelor"),
        Guidance.model_validate(data),
        Profile(scores={"subject_pair": pair, "unt_total": 90, "sdu_english": True}),
    )
    assert result.status == status
