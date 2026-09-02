"""In-memory persistence seam contract (Feature-001 / US-08). Verifies the FR-025 / FR-030
seam behaviour that US-15's governed Unity Catalog Volume implementation must also satisfy."""

from datetime import UTC, datetime

from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.models import ValidatedBriefing


def _briefing(student_hash: str, text: str) -> ValidatedBriefing:
    return ValidatedBriefing(
        student_deidentified_hash=student_hash,
        text=text,
        source="generated",
        validator_id="interim-pass-through",
        generated_at=datetime.now(UTC),
        risk_percentage=64.0,
        at_risk_flag=True,
        prediction_threshold=0.5,
    )


def test_unknown_hash_has_nothing():
    store = InMemoryBriefingStore()
    assert store.has_validated("synthetic-student-003") is False
    assert store.get_latest_validated("synthetic-student-003") is None


def test_save_then_get_latest_returns_what_was_saved():
    store = InMemoryBriefingStore()
    saved = _briefing("synthetic-student-003", "first")
    store.save_validated(saved)
    assert store.has_validated("synthetic-student-003") is True
    assert store.get_latest_validated("synthetic-student-003") is saved


def test_multiple_saves_for_one_hash_expose_the_most_recent():
    store = InMemoryBriefingStore()
    first = _briefing("synthetic-student-003", "first")
    second = _briefing("synthetic-student-003", "second")
    store.save_validated(first)
    store.save_validated(second)
    assert store.get_latest_validated("synthetic-student-003") is second


def test_saves_are_isolated_per_hash():
    store = InMemoryBriefingStore()
    store.save_validated(_briefing("synthetic-student-001", "a"))
    assert store.has_validated("synthetic-student-003") is False
