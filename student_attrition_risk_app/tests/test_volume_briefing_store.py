"""Feature-002 (US-15) — VolumeBriefingStore behaviour against an in-memory fake Files client.

Includes parity with the Feature-001 ``tests/test_briefing_store.py`` store contract (SC-010).
Offline: no workspace, no network.
"""

from datetime import UTC, datetime

import pytest

from doubles import FakeFilesClient
from student_attrition_risk.briefing_store import VolumeBriefingStore
from student_attrition_risk.models import ValidatedBriefing
from student_attrition_risk.student_service import BriefingStorageError

VOLUME = "/Volumes/main/advising/briefings"
HASH = "synthetic-student-003"
OTHER = "synthetic-student-001"


class _Settings:
    briefing_volume = VOLUME


def _store(fake: FakeFilesClient | None = None) -> tuple[VolumeBriefingStore, FakeFilesClient]:
    fake = fake or FakeFilesClient()
    return VolumeBriefingStore(_Settings(), files=fake), fake


def _briefing(
    text: str,
    *,
    student_hash: str = HASH,
    when: datetime | None = None,
    attempt_count: int = 1,
) -> ValidatedBriefing:
    return ValidatedBriefing(
        student_deidentified_hash=student_hash,
        text=text,
        source="generated",
        validator_id="interim-pass-through",
        generated_at=when or datetime.now(UTC),
        attempt_count=attempt_count,
        risk_percentage=64.0,
        at_risk_flag=True,
        prediction_threshold=0.5,
    )


# --- construction --------------------------------------------------------


def test_requires_a_configured_volume():
    class _NoVolume:
        briefing_volume = None

    from student_attrition_risk.config import ConfigurationError

    with pytest.raises(ConfigurationError):
        VolumeBriefingStore(_NoVolume(), files=FakeFilesClient())


# --- store contract parity (mirrors tests/test_briefing_store.py) --------


def test_unknown_hash_has_nothing():
    store, _ = _store()
    assert store.has_validated(HASH) is False
    assert store.get_latest_validated(HASH) is None


def test_save_then_get_latest_returns_an_equal_briefing():
    store, _ = _store()
    saved = _briefing("first")
    store.save_validated(saved)
    assert store.has_validated(HASH) is True
    assert store.get_latest_validated(HASH) == saved  # round-tripped through JSON, so equal not identical


def test_multiple_saves_expose_the_most_recent_and_keep_the_earlier_file():
    store, fake = _store()
    first = _briefing("first", when=datetime(2026, 1, 1, tzinfo=UTC))
    second = _briefing("second", when=datetime(2026, 1, 2, tzinfo=UTC))
    store.save_validated(first)
    store.save_validated(second)
    assert store.get_latest_validated(HASH).text == "second"
    assert len(fake.files) == 2  # append-only: the earlier file is not removed


def test_saves_are_isolated_per_hash():
    store, _ = _store()
    store.save_validated(_briefing("a", student_hash=OTHER))
    assert store.has_validated(HASH) is False
    assert store.get_latest_validated(HASH) is None


# --- storage-failure surfacing (FR-024) --------------------------------


def test_upload_failure_is_surfaced_and_prior_latest_is_untouched():
    store, fake = _store()
    store.save_validated(_briefing("kept", when=datetime(2026, 1, 1, tzinfo=UTC)))
    fake.fail_upload = RuntimeError("volume write failed")
    with pytest.raises(BriefingStorageError):
        store.save_validated(_briefing("lost", when=datetime(2026, 1, 2, tzinfo=UTC)))
    assert store.get_latest_validated(HASH).text == "kept"


def test_list_failure_that_is_not_not_found_is_a_storage_error():
    store, fake = _store()
    fake.fail_list = RuntimeError("volume unavailable")
    with pytest.raises(BriefingStorageError):
        store.get_latest_validated(HASH)
    with pytest.raises(BriefingStorageError):
        store.has_validated(HASH)


def test_download_failure_is_a_storage_error():
    store, fake = _store()
    store.save_validated(_briefing("body"))
    fake.fail_download = RuntimeError("read failed")
    with pytest.raises(BriefingStorageError):
        store.get_latest_validated(HASH)


# --- privacy of the stored document (FR-026) --------------------------


def test_stored_body_is_validated_briefing_json_only():
    store, fake = _store()
    store.save_validated(_briefing("briefing body text", attempt_count=2))
    (body,) = fake.files.values()
    assert "composed_prompt" not in body
    assert "prompt" not in body
    restored = ValidatedBriefing.model_validate_json(body)
    assert restored.attempt_count == 2
    assert restored.text == "briefing body text"
