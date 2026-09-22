"""Feature-002 (US-15) User Story 4 — the persistence confirmation (amendment 2026-09-22).

Covers spec FR-035-FR-041 and the FR-032 correction, per
``specs/002-briefing-retry-and-storage/contracts/persistence-confirmation.md``.

Scope: this file adds only what the amendment introduced. The retry and storage *behaviour* it
reports on is already proven by Feature-001, Feature-002 and Feature-003; none of that is
re-tested here, and no existing test file is modified. Offline: scripted generation and
validation doubles over the in-memory store.
"""

import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest

import student_attrition_risk
from doubles import ScriptedGenerationProvider, ScriptedValidator
from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_messages import (
    existing_briefing_message,
    retrieved_briefing_message,
    storage_confirmation_message,
)
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.models import DraftBriefing, ValidatedBriefing, ValidationOutcome
from student_attrition_risk.retry_workflow import SingleRetryWorkflow
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import BriefingStorageError, StudentService

FLAGGED = "synthetic-student-001"

# Located by path rather than imported: ``ui.py`` executes Streamlit calls at import time, which
# is also why the confirmation copy lives in ``briefing_messages.py``.
UI_SOURCE = Path(student_attrition_risk.__file__).parent / "ui.py"


def _draft(text: str) -> DraftBriefing:
    return DraftBriefing(student_deidentified_hash=FLAGGED, text=text)


def _passed() -> ValidationOutcome:
    return ValidationOutcome(passed=True, validator_id="stub-validator")


def _failed() -> ValidationOutcome:
    return ValidationOutcome(passed=False, validator_id="stub-validator")


class _RecordingStore(InMemoryBriefingStore):
    """Keeps what ``save_validated`` was actually handed, before any confirmation stamping."""

    def __init__(self) -> None:
        super().__init__()
        self.received: list[ValidatedBriefing] = []

    def save_validated(self, briefing: ValidatedBriefing) -> None:
        self.received.append(briefing)
        super().save_validated(briefing)


class _RaisingStore(InMemoryBriefingStore):
    def save_validated(self, briefing: ValidatedBriefing) -> None:
        raise BriefingStorageError("store unavailable")


def _service(*, generation, validation, store=None):
    store = store if store is not None else InMemoryBriefingStore()
    return (
        StudentService(
            repository=MockStudentRepository(),
            generation_provider=generation,
            instructions=InterimInstructions(),
            validator=validation,
            retry_workflow=SingleRetryWorkflow(
                generation_provider=generation, validator=validation
            ),
            store=store,
        ),
        store,
    )


# --- FR-035 / FR-036: the confirmation is reported, and only on a confirmed save -------------


def test_first_attempt_success_reports_the_briefing_as_stored():
    """FR-035: a successful result carries the persistence confirmation."""
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("first attempt briefing")),
        validation=ScriptedValidator(_passed()),
    )

    briefing = service.request_briefing(FLAGGED, regenerate=True)

    assert briefing.storage_confirmed is True


def test_the_confirmation_is_stamped_after_the_save_not_before_it():
    """FR-036: the store is handed the pre-confirmation briefing.

    If the flag were set optimistically at construction, the object reaching ``save_validated``
    would already carry ``True``. Asserting on what the store received is what distinguishes
    "confirmed because the save returned" from "assumed".
    """
    store = _RecordingStore()
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("briefing text")),
        validation=ScriptedValidator(_passed()),
        store=store,
    )

    returned = service.request_briefing(FLAGGED, regenerate=True)

    assert len(store.received) == 1
    assert store.received[0].storage_confirmed is False
    assert returned.storage_confirmed is True


def test_a_storage_failure_yields_no_confirmed_briefing():
    """FR-036: a run that cannot store the briefing reports no confirmation at all."""
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("briefing text")),
        validation=ScriptedValidator(_passed()),
        store=_RaisingStore(),
    )

    with pytest.raises(BriefingStorageError):
        service.request_briefing(FLAGGED, regenerate=True)


# --- FR-040 / FR-032: identical across attempts ----------------------------------------------


def test_a_retry_success_reports_exactly_what_a_first_attempt_success_reports():
    """FR-040: the confirmation describes storage, not the attempt that produced the briefing."""
    first_service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("attempt one briefing")),
        validation=ScriptedValidator(_passed()),
    )
    retry_service, _ = _service(
        generation=ScriptedGenerationProvider(
            _draft("rejected briefing"), _draft("attempt two briefing")
        ),
        validation=ScriptedValidator(_failed(), _passed()),
    )

    first = first_service.request_briefing(FLAGGED, regenerate=True)
    retried = retry_service.request_briefing(FLAGGED, regenerate=True)

    assert retried.attempt_count == 2, "guard: this must be the retry path"
    assert first.storage_confirmed is True
    assert retried.storage_confirmed == first.storage_confirmed


# --- FR-037: a briefing read back from the store also reports as stored ----------------------


def test_the_retrieval_path_reports_the_briefing_as_stored():
    """FR-037: it was read out of the store, so it is in the store."""
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("briefing text")),
        validation=ScriptedValidator(_passed()),
    )
    service.request_briefing(FLAGGED, regenerate=True)

    retrieved = service.get_stored_briefing(FLAGGED)

    assert retrieved is not None
    assert retrieved.source == "stored"
    assert retrieved.storage_confirmed is True


def test_a_non_regenerate_request_for_an_existing_briefing_reports_it_as_stored():
    """FR-037 on the get-or-create path: nothing is generated, and it still reports as stored."""
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("briefing text")),
        validation=ScriptedValidator(_passed()),
    )
    service.request_briefing(FLAGGED, regenerate=True)

    existing = service.request_briefing(FLAGGED, regenerate=False)

    assert existing.source == "stored"
    assert existing.storage_confirmed is True


def test_has_stored_briefing_reports_whether_a_regeneration_would_supersede_one():
    """FR-039: the signal the advisor surface uses to tell a first save from a replacement."""
    service, _ = _service(
        generation=ScriptedGenerationProvider(_draft("briefing text")),
        validation=ScriptedValidator(_passed()),
    )

    assert service.has_stored_briefing(FLAGGED) is False
    service.request_briefing(FLAGGED, regenerate=True)
    assert service.has_stored_briefing(FLAGGED) is True


# --- FR-038 / FR-039 / FR-041: the advisor-facing copy ---------------------------------------


def test_the_confirmation_says_the_briefing_was_validated_and_saved():
    """FR-038: both halves of the claim the advisor is being given."""
    message = storage_confirmation_message(replaced=False).lower()

    assert "validation" in message or "validated" in message
    assert "saved" in message


def test_only_the_replacement_confirmation_mentions_superseding_an_earlier_briefing():
    """FR-039: a first save must not claim to have replaced anything."""
    first_save = storage_confirmation_message(replaced=False)
    replacement = storage_confirmation_message(replaced=True)

    assert "supersedes" in replacement.lower()
    assert "supersede" not in first_save.lower()
    # Storage is append-only: the earlier briefing is retained in the store, it simply stops
    # being the most recent. Wording that implied deletion would misdescribe what happened.
    for destructive in ("replaces", "deletes", "overwrites", "removes"):
        assert destructive not in replacement.lower(), f"wording implies destruction: {destructive}"
    assert replacement.startswith(first_save)


def test_the_existing_briefing_message_does_not_claim_a_save():
    """A request that generated nothing must not report that anything was saved."""
    assert "has been saved" not in existing_briefing_message().lower()


def test_the_existing_notice_is_not_mistakable_for_a_save_confirmation():
    """The two say different things, so the advisor can tell a save from a no-op.

    They previously shared the confirmation channel, which made a request that generated and
    saved nothing look like a successful save.
    """
    existing = existing_briefing_message()

    assert existing != storage_confirmation_message(replaced=False)
    assert existing != storage_confirmation_message(replaced=True)


def test_the_existing_notice_names_the_action_that_would_generate_one():
    """Explaining why nothing happened is only useful with the way to make it happen."""
    assert "regenerate" in existing_briefing_message().lower()


def test_every_advisor_message_is_distinct():
    """Three outcomes, three sentences. Identical copy would make the buttons
    indistinguishable, which is what an earlier revision got wrong."""
    messages = [
        storage_confirmation_message(replaced=False),
        storage_confirmation_message(replaced=True),
        existing_briefing_message(),
        retrieved_briefing_message(),
    ]

    assert len(set(messages)) == len(messages)


def test_the_retrieved_message_reports_a_read_not_a_write():
    """Retrieve Saved writes nothing, so it must not claim a save (FR-038)."""
    message = retrieved_briefing_message().lower()

    assert "retrieved" in message
    assert "has been saved" not in message


@pytest.mark.parametrize(
    "message",
    [
        storage_confirmation_message(replaced=False),
        storage_confirmation_message(replaced=True),
        existing_briefing_message(),
    ],
)
def test_advisor_copy_names_no_storage_technology(message: str):
    """FR-041: the in-memory store is still the local and test implementation."""
    lowered = message.lower()
    for technology in ("volume", "unity catalog", "databricks", "in-memory", "in memory"):
        assert technology not in lowered, f"copy names a storage technology: {technology}"


@pytest.mark.parametrize(
    "message",
    [
        storage_confirmation_message(replaced=False),
        storage_confirmation_message(replaced=True),
        existing_briefing_message(),
    ],
)
def test_advisor_copy_never_mentions_attempts_or_retries(message: str):
    """FR-032 / FR-040: the confirmation reports storage, never the retry."""
    lowered = message.lower()
    for term in ("attempt", "retry", "retried", "second try"):
        assert term not in lowered, f"copy leaks the retry: {term}"


# --- FR-032 correction: the attempt count is no longer advisor-facing ------------------------


def test_notices_never_rely_on_colour_alone():
    """Each notice leads with a bold label, so meaning survives monochrome and any colour
    vision deficiency. The renderer is what guarantees it, so assert on the renderer."""
    source = UI_SOURCE.read_text(encoding="utf-8")

    assert "notice-label" in source
    assert 'def render_notice(' in source
    # Every notice goes through the renderer; none is hand-built without a label.
    assert '<div class="page-notice">' not in source
    assert '<div class="save-confirmation">' not in source


def test_notice_colours_avoid_the_red_green_pair():
    """Green is not used for the confirmation: under the common red-green deficiencies it
    converges with the red used for errors. Teal keeps a blue component and stays distinct."""
    source = UI_SOURCE.read_text(encoding="utf-8")
    confirmation = source[source.index(".save-confirmation {") :][:400]

    for green in ("#067647", "#dcfae6", "#12b76a"):
        assert green not in confirmation, f"confirmation uses a success green: {green}"


def test_the_advisor_surface_does_not_render_the_attempt_count():
    """SC-016: the metadata line shipped rendering it, contrary to FR-032."""
    assert "attempt_count" not in UI_SOURCE.read_text(encoding="utf-8")


def test_the_attempt_count_is_still_carried_as_workflow_metadata():
    """SC-016, the other half: removing it from the UI must not remove it from the record."""
    briefing = ValidatedBriefing(
        student_deidentified_hash=FLAGGED,
        text="briefing text",
        source="generated",
        validator_id="stub-validator",
        generated_at=datetime.now(UTC),
        attempt_count=2,
        risk_percentage=64.0,
        at_risk_flag=True,
        prediction_threshold=0.5,
    )

    payload = briefing.model_dump(mode="json")

    assert payload["attempt_count"] == 2
    assert payload["storage_confirmed"] is False


def test_the_confirmation_helpers_need_no_streamlit_runtime():
    """The copy lives outside ui.py so FR-038/FR-039/FR-041 stay directly testable."""
    source_file = Path(inspect.getfile(storage_confirmation_message))
    source = source_file.read_text(encoding="utf-8")

    assert source_file.name == "briefing_messages.py"
    assert "import streamlit" not in source
    assert "from streamlit" not in source
