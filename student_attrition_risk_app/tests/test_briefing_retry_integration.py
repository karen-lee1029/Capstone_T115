"""Feature-002 (US-15) — the single-retry workflow end to end through StudentService.

Real StudentService + SingleRetryWorkflow + InMemoryBriefingStore; generation and validation
are scripted doubles (a fixed sequence consumed across attempt 1 and attempt 2, since the same
instances back the service and the retry workflow). Offline.
"""

import logging
from datetime import UTC, datetime

import pytest

from doubles import ScriptedGenerationProvider, ScriptedValidator
from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.models import DraftBriefing, ValidatedBriefing, ValidationOutcome
from student_attrition_risk.retry_workflow import SingleRetryWorkflow
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentService,
)

FLAGGED = "synthetic-student-001"
HAS_EXISTING = "synthetic-student-003"


class _CountingStore(InMemoryBriefingStore):
    def __init__(self) -> None:
        super().__init__()
        self.saves = 0

    def save_validated(self, briefing: ValidatedBriefing) -> None:
        self.saves += 1
        super().save_validated(briefing)


class _RaisingStore(InMemoryBriefingStore):
    def save_validated(self, briefing: ValidatedBriefing) -> None:
        raise BriefingStorageError("volume unavailable")


def _draft(text: str, student_hash: str = FLAGGED) -> DraftBriefing:
    return DraftBriefing(student_deidentified_hash=student_hash, text=text)


def _passed(validator_id: str = "stub-validator") -> ValidationOutcome:
    return ValidationOutcome(passed=True, validator_id=validator_id)


def _failed() -> ValidationOutcome:
    return ValidationOutcome(passed=False, validator_id="stub-validator")


def _service(*, generation, validation, store=None, repository=None):
    store = store if store is not None else InMemoryBriefingStore()
    service = StudentService(
        repository=repository or MockStudentRepository(),
        generation_provider=generation,
        instructions=InterimInstructions(),
        validator=validation,
        retry_workflow=SingleRetryWorkflow(generation_provider=generation, validator=validation),
        store=store,
    )
    return service, store


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


# --- US1: retry recovers a failed first attempt --------------------------


def test_validation_fail_then_pass_returns_attempt_2_and_persists_via_service():
    gen = ScriptedGenerationProvider(_draft("first draft"), _draft("second draft"))
    val = ScriptedValidator(_failed(), _passed("real-validator"))
    service, store = _service(generation=gen, validation=val, store=_CountingStore())

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert briefing.text == "second draft"
    assert briefing.validator_id == "real-validator"
    assert store.get_latest_validated(FLAGGED).attempt_count == 2
    # Persisted exactly once, by StudentService._hand_off_to_retry -> _persist (FR-019).
    assert store.saves == 1
    assert not hasattr(service.retry_workflow, "store")
    assert not hasattr(service.retry_workflow, "_store")
    assert gen.calls == 2
    assert val.calls == 2


def test_generation_fail_then_pass_returns_attempt_2():
    gen = ScriptedGenerationProvider(RuntimeError("provider down"), _draft("second draft"))
    val = ScriptedValidator(_passed())
    service, store = _service(generation=gen, validation=val)

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert store.get_latest_validated(FLAGGED) is not None
    assert gen.calls == 2
    assert val.calls == 1


def test_successful_retry_log_line_is_metadata_only(caplog):
    gen = ScriptedGenerationProvider(_draft("SECRET FIRST BODY"), _draft("SECRET SECOND BODY"))
    val = ScriptedValidator(_failed(), _passed("real-validator"))
    service, _ = _service(generation=gen, validation=val)

    with caplog.at_level(logging.INFO, logger="student_attrition_risk.student_service"):
        service.request_briefing(FLAGGED)

    text = " ".join(record.getMessage() for record in caplog.records)
    assert "outcome=generated" in text
    assert "attempt_count=2" in text
    assert "validator_id=real-validator" in text
    assert "SECRET FIRST BODY" not in text
    assert "SECRET SECOND BODY" not in text


# --- US2: retry also fails ------------------------------------------------


def test_two_generation_failures_terminate_with_generation_category_and_store_nothing():
    gen = ScriptedGenerationProvider(RuntimeError("down 1"), RuntimeError("down 2"))
    val = ScriptedValidator()
    service, store = _service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError) as excinfo:
        service.request_briefing(FLAGGED)

    assert excinfo.value.category == "generation"
    assert store.has_validated(FLAGGED) is False
    assert service.get_stored_briefing(FLAGGED) is None
    assert gen.calls == 2


def test_two_validation_failures_terminate_with_validation_category_and_store_nothing():
    gen = ScriptedGenerationProvider(_draft("first"), _draft("second"))
    val = ScriptedValidator(_failed(), _failed())
    service, store = _service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError) as excinfo:
        service.request_briefing(FLAGGED)

    assert excinfo.value.category == "validation"
    assert store.has_validated(FLAGGED) is False
    assert gen.calls == 2
    assert val.calls == 2


def test_terminal_failure_on_regeneration_keeps_the_previous_briefing():
    store = InMemoryBriefingStore()
    _seed(store, HAS_EXISTING, "keep me")
    gen = ScriptedGenerationProvider(RuntimeError("down 1"), RuntimeError("down 2"))
    service, _ = _service(generation=gen, validation=ScriptedValidator(), store=store)

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(HAS_EXISTING, regenerate=True)

    assert store.get_latest_validated(HAS_EXISTING).text == "keep me"
    assert service.get_stored_briefing(HAS_EXISTING).text == "keep me"


def test_no_template_or_unvalidated_briefing_is_returned_or_stored_on_failure():
    gen = ScriptedGenerationProvider(_draft("first"), _draft("second"))
    val = ScriptedValidator(_failed(), _failed())
    service, store = _service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert store.has_validated(FLAGGED) is False


def test_successful_retry_with_failing_persistence_surfaces_storage_error_and_keeps_prior():
    store = _RaisingStore()
    _seed(store, HAS_EXISTING, "prior briefing")
    gen = ScriptedGenerationProvider(_draft("first", HAS_EXISTING), _draft("second", HAS_EXISTING))
    val = ScriptedValidator(_failed(), _passed())
    service, _ = _service(generation=gen, validation=val, store=store)

    with pytest.raises(BriefingStorageError):
        service.request_briefing(HAS_EXISTING, regenerate=True)

    assert store.get_latest_validated(HAS_EXISTING).text == "prior briefing"
