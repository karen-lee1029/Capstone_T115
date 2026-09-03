from datetime import UTC, datetime

from fastapi.testclient import TestClient

from student_attrition_risk.api import create_api
from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.models import DraftBriefing, ValidatedBriefing, ValidationOutcome
from student_attrition_risk.retry_workflow import RetryNotConfigured
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import BriefingStorageError, StudentService

FLAGGED = "synthetic-student-001"
NOT_FLAGGED = "synthetic-student-002"
HAS_EXISTING = "synthetic-student-003"


class _PassValidator:
    def validate(self, draft, context) -> ValidationOutcome:
        return ValidationOutcome(passed=True, validator_id="stub")


class _FailValidator:
    def validate(self, draft, context) -> ValidationOutcome:
        return ValidationOutcome(passed=False, failed_criteria=["x"], feedback="y", validator_id="stub")


class _RaisingStore(InMemoryBriefingStore):
    def save_validated(self, briefing) -> None:
        raise BriefingStorageError("volume unavailable")


def _client(*, generation_provider=None, validator=None, store=None) -> TestClient:
    service = StudentService(
        repository=MockStudentRepository(),
        generation_provider=generation_provider or StubGenerationProvider(),
        instructions=InterimInstructions(),
        validator=validator or _PassValidator(),
        retry_workflow=RetryNotConfigured(),
        store=store if store is not None else InMemoryBriefingStore(),
    )
    return TestClient(create_api(service))


def _seed(store: InMemoryBriefingStore, student_hash: str, text: str) -> None:
    InMemoryBriefingStore.save_validated(
        store,
        ValidatedBriefing(
            student_deidentified_hash=student_hash,
            text=text,
            source="generated",
            validator_id="interim-pass-through",
            generated_at=datetime.now(UTC),
            risk_percentage=64.0,
            at_risk_flag=True,
            prediction_threshold=0.5,
        ),
    )


def test_unchanged_read_endpoints():
    client = _client()
    assert client.get("/api/health").status_code == 200
    assert client.get(f"/api/students/{FLAGGED}").status_code == 200
    assert client.get("/api/students/missing").status_code == 404
    assert client.get("/api/students/high-risk?limit=0").status_code == 422


def test_post_briefing_unconfigured_generation_returns_503_not_a_template():
    response = _client().post(f"/api/students/{FLAGGED}/briefing")
    assert response.status_code == 503
    assert response.json()["detail"] == "Briefing generation is not configured"


def test_post_briefing_generates_and_returns_validated_briefing():
    client = _client(generation_provider=StubGenerationProvider(
        draft=DraftBriefing(student_deidentified_hash=FLAGGED, text="fresh briefing")))
    response = client.post(f"/api/students/{FLAGGED}/briefing")
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "fresh briefing"
    assert body["source"] == "generated"
    assert body["validated"] is True


def test_post_briefing_not_flagged_returns_409():
    response = _client().post(f"/api/students/{NOT_FLAGGED}/briefing")
    assert response.status_code == 409
    assert response.json()["detail"] == "Student is not flagged at risk"


def test_post_briefing_unknown_hash_returns_404():
    assert _client().post("/api/students/missing/briefing").status_code == 404


def test_post_briefing_returns_existing_then_regenerates_on_flag():
    store = InMemoryBriefingStore()
    _seed(store, HAS_EXISTING, "stored body")
    client = _client(
        generation_provider=StubGenerationProvider(
            draft=DraftBriefing(student_deidentified_hash=HAS_EXISTING, text="regenerated")),
        store=store,
    )
    first = client.post(f"/api/students/{HAS_EXISTING}/briefing")
    assert first.status_code == 200
    assert first.json()["source"] == "stored"
    assert first.json()["text"] == "stored body"

    second = client.post(f"/api/students/{HAS_EXISTING}/briefing?regenerate=true")
    assert second.status_code == 200
    assert second.json()["text"] == "regenerated"


def test_post_briefing_retry_terminal_maps_to_502_with_category_in_detail():
    gen_fail = _client(generation_provider=StubGenerationProvider(raises=RuntimeError("down")))
    r1 = gen_fail.post(f"/api/students/{FLAGGED}/briefing")
    assert r1.status_code == 502
    assert r1.json()["detail"] == "Briefing could not be produced (generation)"

    val_fail = _client(
        generation_provider=StubGenerationProvider(
            draft=DraftBriefing(student_deidentified_hash=FLAGGED, text="d")),
        validator=_FailValidator(),
    )
    r2 = val_fail.post(f"/api/students/{FLAGGED}/briefing")
    assert r2.status_code == 502
    assert r2.json()["detail"] == "Briefing could not be produced (validation)"


def test_post_briefing_storage_failure_maps_to_503():
    client = _client(
        generation_provider=StubGenerationProvider(
            draft=DraftBriefing(student_deidentified_hash=FLAGGED, text="d")),
        store=_RaisingStore(),
    )
    response = client.post(f"/api/students/{FLAGGED}/briefing")
    assert response.status_code == 503
    assert response.json()["detail"] == "Validated briefing could not be stored"


def test_get_stored_briefing_returns_it_or_404_none_available():
    store = InMemoryBriefingStore()
    _seed(store, HAS_EXISTING, "kept")
    client = _client(store=store)
    ok = client.get(f"/api/students/{HAS_EXISTING}/briefing")
    assert ok.status_code == 200
    assert ok.json()["source"] == "stored"
    assert ok.json()["text"] == "kept"

    none = client.get(f"/api/students/{FLAGGED}/briefing")
    assert none.status_code == 404
    assert none.json()["detail"] == "No validated briefing available"

    assert client.get("/api/students/missing/briefing").status_code == 404
