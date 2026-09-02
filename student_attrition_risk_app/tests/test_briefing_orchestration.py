"""Feature-001 (US-08) orchestration tests. Drives ``StudentService.request_briefing`` and
``get_stored_briefing`` through every branch with stub seams — no network, no workspace.

US1 (success / precondition / return-existing / regenerate): T020.
US2 (retrieval): T027.
US3 (failure handling): T033, T034.
"""

import logging
from datetime import UTC, datetime

import pytest

from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.models import (
    BriefingGenerationContext,
    DraftBriefing,
    ValidatedBriefing,
    ValidationOutcome,
)
from student_attrition_risk.retry_workflow import RetryNotConfigured
from student_attrition_risk.student_repository import MODEL_FEATURE_COLUMNS, MockStudentRepository
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotAtRiskError,
    StudentNotFoundError,
    StudentService,
)

FLAGGED = "synthetic-student-001"
NOT_FLAGGED = "synthetic-student-002"
HAS_EXISTING = "synthetic-student-003"


class StubValidator:
    def __init__(self, passed: bool = True, failed_criteria=None, feedback=None) -> None:
        self._outcome = ValidationOutcome(
            passed=passed,
            failed_criteria=list(failed_criteria or []),
            feedback=feedback,
            validator_id="stub-validator",
        )
        self.calls = 0

    def validate(self, draft, context) -> ValidationOutcome:
        self.calls += 1
        return self._outcome


class CountingRetry:
    """Records invocations; delegates the outcome to RetryNotConfigured (terminal failure)."""

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = RetryNotConfigured()

    def run(self, context, first_outcome):
        self.calls += 1
        return self._delegate.run(context, first_outcome)


class RaisingStore(InMemoryBriefingStore):
    def save_validated(self, briefing) -> None:
        raise BriefingStorageError("volume unavailable")


def _draft(text: str = "draft body") -> DraftBriefing:
    return DraftBriefing(student_deidentified_hash=FLAGGED, text=text)


def _service(
    *,
    generation_provider=None,
    validator=None,
    retry_workflow=None,
    store=None,
    repository=None,
) -> StudentService:
    return StudentService(
        repository=repository or MockStudentRepository(),
        generation_provider=generation_provider or StubGenerationProvider(draft=_draft()),
        instructions=InterimInstructions(),
        validator=validator or StubValidator(passed=True),
        retry_workflow=retry_workflow or CountingRetry(),
        store=store if store is not None else InMemoryBriefingStore(),
    )


def _seed_existing(store: InMemoryBriefingStore, student_hash: str, text: str = "existing") -> None:
    store.save_validated(
        ValidatedBriefing(
            student_deidentified_hash=student_hash,
            text=text,
            source="generated",
            validator_id="interim-pass-through",
            generated_at=datetime.now(UTC),
            risk_percentage=64.0,
            at_risk_flag=True,
            prediction_threshold=0.5,
        )
    )


# --- US1 ------------------------------------------------------------------


def test_happy_path_assembles_context_calls_seams_in_order_and_stores():
    seen = {}

    class RecordingInstructions(InterimInstructions):
        def compose(self, context: BriefingGenerationContext) -> str:
            seen["features"] = dict(context.features.values)
            seen["risk"] = context.prediction.attrition_risk_percentage
            return super().compose(context)

    store = InMemoryBriefingStore()
    validator = StubValidator(passed=True)
    retry = CountingRetry()
    service = StudentService(
        repository=MockStudentRepository(),
        generation_provider=StubGenerationProvider(draft=_draft("generated text")),
        instructions=RecordingInstructions(),
        validator=validator,
        retry_workflow=retry,
        store=store,
    )

    briefing = service.request_briefing(FLAGGED)

    assert set(seen["features"]) == set(MODEL_FEATURE_COLUMNS)  # all 21 (SC-001)
    assert seen["risk"] == 78.5
    assert briefing.text == "generated text"
    assert briefing.source == "generated"
    assert briefing.validated is True
    assert briefing.attempt_count == 1
    assert validator.calls == 1
    assert retry.calls == 0  # retry seam never touched on the happy path (SC-009)
    assert store.get_latest_validated(FLAGGED) is not None
    assert service.get_stored_briefing(FLAGGED).source == "stored"


def test_risk_percentage_is_carried_through_verbatim():
    briefing = _service().request_briefing(FLAGGED)
    assert briefing.risk_percentage == 78.5
    assert briefing.at_risk_flag is True
    assert briefing.prediction_threshold == 0.5


def test_at_risk_decision_uses_the_model_flag_not_a_second_threshold():
    # NOT_FLAGGED has an 18% score and flag False -> refused; FLAGGED (78.5%, flag True) proceeds.
    with pytest.raises(StudentNotAtRiskError):
        _service().request_briefing(NOT_FLAGGED)
    assert _service().request_briefing(FLAGGED).validated is True


def test_not_flagged_request_makes_no_generation_seam_call():
    gen = StubGenerationProvider(draft=_draft())
    retry = CountingRetry()
    service = _service(generation_provider=gen, retry_workflow=retry)
    with pytest.raises(StudentNotAtRiskError):
        service.request_briefing(NOT_FLAGGED)
    assert retry.calls == 0


def test_unknown_hash_is_not_found():
    with pytest.raises(StudentNotFoundError):
        _service().request_briefing("missing")


def test_existing_briefing_is_returned_without_calling_generation():
    store = InMemoryBriefingStore()
    _seed_existing(store, HAS_EXISTING, "seeded body")

    class ExplodingGen(StubGenerationProvider):
        def generate(self, context):
            raise AssertionError("generation seam must not be called (FR-035)")

    service = _service(generation_provider=ExplodingGen(), store=store)
    briefing = service.request_briefing(HAS_EXISTING)
    assert briefing.text == "seeded body"
    assert briefing.source == "stored"


def test_explicit_regenerate_supersedes_on_success():
    store = InMemoryBriefingStore()
    _seed_existing(store, HAS_EXISTING, "old")
    service = _service(
        generation_provider=StubGenerationProvider(draft=DraftBriefing(
            student_deidentified_hash=HAS_EXISTING, text="fresh")),
        store=store,
    )
    briefing = service.request_briefing(HAS_EXISTING, regenerate=True)
    assert briefing.text == "fresh"
    assert store.get_latest_validated(HAS_EXISTING).text == "fresh"


def test_regenerate_terminal_failure_retains_the_previous_briefing():
    store = InMemoryBriefingStore()
    _seed_existing(store, HAS_EXISTING, "keep me")
    service = _service(
        generation_provider=StubGenerationProvider(raises=RuntimeError("provider down")),
        store=store,
    )
    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(HAS_EXISTING, regenerate=True)
    assert store.get_latest_validated(HAS_EXISTING).text == "keep me"
    assert service.get_stored_briefing(HAS_EXISTING).text == "keep me"


# --- US2: retrieval ----------------------------------------------------------


def test_get_stored_briefing_returns_latest_when_present():
    store = InMemoryBriefingStore()
    _seed_existing(store, HAS_EXISTING, "first")
    _seed_existing(store, HAS_EXISTING, "second")
    briefing = _service(store=store).get_stored_briefing(HAS_EXISTING)
    assert briefing is not None
    assert briefing.text == "second"
    assert briefing.source == "stored"
    assert briefing.validated is True


def test_get_stored_briefing_returns_none_when_absent():
    assert _service().get_stored_briefing(FLAGGED) is None


def test_get_stored_briefing_unknown_hash_is_not_found():
    with pytest.raises(StudentNotFoundError):
        _service().get_stored_briefing("missing")


def test_retrieval_only_ever_sees_validated_briefings():
    # The store only accepts ValidatedBriefing; a draft/failed briefing can never reach it.
    store = InMemoryBriefingStore()
    service = _service(
        generation_provider=StubGenerationProvider(raises=RuntimeError("down")), store=store
    )
    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)
    assert service.get_stored_briefing(FLAGGED) is None


# --- US3: failure handling -------------------------------------------------


def test_generation_failure_hands_off_to_retry_seam_once_then_terminal_generation():
    retry = CountingRetry()
    service = _service(
        generation_provider=StubGenerationProvider(raises=RuntimeError("provider down")),
        retry_workflow=retry,
    )
    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)
    assert exc.value.category == "generation"
    assert retry.calls == 1
    assert service.get_stored_briefing(FLAGGED) is None  # nothing stored


def test_validation_failure_hands_off_to_retry_seam_once_then_terminal_validation():
    retry = CountingRetry()
    service = _service(
        validator=StubValidator(passed=False, failed_criteria=["missing-section"], feedback="add x"),
        retry_workflow=retry,
    )
    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)
    assert exc.value.category == "validation"
    assert retry.calls == 1
    assert service.get_stored_briefing(FLAGGED) is None


def test_no_deterministic_or_template_briefing_is_returned_or_stored_on_failure():
    store = InMemoryBriefingStore()
    service = _service(
        generation_provider=StubGenerationProvider(raises=RuntimeError("down")), store=store
    )
    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)
    assert store.has_validated(FLAGGED) is False


def test_persistence_failure_is_surfaced_and_previous_briefing_is_intact():
    store = RaisingStore()
    _seed_existing_via_parent(store, HAS_EXISTING, "prior")
    service = _service(
        generation_provider=StubGenerationProvider(draft=DraftBriefing(
            student_deidentified_hash=HAS_EXISTING, text="new")),
        store=store,
    )
    with pytest.raises(BriefingStorageError):
        service.request_briefing(HAS_EXISTING, regenerate=True)
    assert store.get_latest_validated(HAS_EXISTING).text == "prior"


def test_retry_seam_is_never_invoked_by_the_normal_success_path():
    retry = CountingRetry()
    _service(retry_workflow=retry).request_briefing(FLAGGED)
    assert retry.calls == 0


def test_logs_are_metadata_only_no_prompt_no_briefing_text_no_secret(caplog):
    with caplog.at_level(logging.INFO, logger="student_attrition_risk.student_service"):
        _service(generation_provider=StubGenerationProvider(draft=_draft("SECRET BRIEFING BODY"))) \
            .request_briefing(FLAGGED)
    records = " ".join(r.getMessage() for r in caplog.records)
    assert "briefing_workflow" in records
    assert FLAGGED in records
    assert "outcome=generated" in records
    assert "validator_id=" in records
    assert "SECRET BRIEFING BODY" not in records
    assert "PROFILE JSON" not in records
    assert "APPROVED MODEL FEATURE VALUES" not in records


def _seed_existing_via_parent(store: RaisingStore, student_hash: str, text: str) -> None:
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
