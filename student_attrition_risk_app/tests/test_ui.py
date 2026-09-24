"""UI interaction tests for the Streamlit Student Advisor Briefing interface.

Every user-facing interactive element is exercised — the search text input,
Retrieve button, Generate / Retrieve Saved / Regenerate briefing buttons,
review checkbox, download button, and the Dashboard link — across happy
paths and error states.  The real ``build_service`` is replaced by a
``FakeService`` backed by ``MockStudentRepository`` so no Databricks
connection is required.

NOTE: When running tests, Python environment must have Streamlit installed.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import pytest
from streamlit.testing.v1 import AppTest

from student_attrition_risk.models import (
    StudentRiskProfile,
    make_validated_briefing,
)
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotFoundError,
)

UI_PATH = str(
    Path(__file__).resolve().parent.parent
    / "src" / "student_attrition_risk" / "ui.py"
)

HASH_AT_RISK = "synthetic-student-001"
HASH_NOT_AT_RISK = "synthetic-student-002"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prediction(hash: str = HASH_AT_RISK):
    return MockStudentRepository().predictions[hash]


def _briefing(
    hash: str = HASH_AT_RISK,
    attempt: int = 1,
    source: str = "generated",
):
    """Build a ``ValidatedBriefing`` for use as a fake service return value."""
    b = make_validated_briefing(
        student_hash=hash,
        prediction=_prediction(hash),
        text=(
            "## Risk Summary\nThe student is at risk.\n\n"
            "## Recommended Advisor Actions\nReach out to the student."
        ),
        validator_id="test-validator",
        attempt_count=attempt,
    )
    if source != "generated":
        b = b.model_copy(update={"source": source})
    return b


class FakeService:
    """Configurable stand-in for ``StudentService``.

    Each method can either return a scripted value or raise a scripted
    exception, so every UI error branch can be exercised without touching
    the real generation / validation / persistence seams.
    """

    def __init__(
        self,
        *,
        briefing=None,
        stored_briefing=None,
        request_error=None,
        retrieve_error=None,
        profile_error=None,
        repository=None,
    ):
        self._repository = repository or MockStudentRepository()
        self._briefing = briefing
        self._stored_briefing = stored_briefing
        self._request_error = request_error
        self._retrieve_error = retrieve_error
        self._profile_error = profile_error

    def get_student_profile(self, student_hash):
        if self._profile_error:
            raise self._profile_error
        prediction = self._repository.get_prediction(student_hash)
        if prediction is None:
            raise StudentNotFoundError(student_hash)
        return StudentRiskProfile(
            prediction=prediction,
            snapshot=self._repository.get_snapshot(student_hash),
        )

    def request_briefing(self, student_hash, regenerate=False):
        if self._request_error:
            raise self._request_error
        if self._briefing is None:
            raise BriefingNotProducedError("generation")
        return self._briefing

    def get_stored_briefing(self, student_hash):
        if self._retrieve_error:
            raise self._retrieve_error
        return self._stored_briefing


@pytest.fixture
def app(monkeypatch):
    """Factory: patches ``build_service`` and returns a freshly-run ``AppTest``."""

    def _create(service):
        monkeypatch.setattr(
            "student_attrition_risk.main.build_service",
            lambda *_a, **_kw: service,
        )
        st.cache_resource.clear()
        at = AppTest.from_file(UI_PATH, default_timeout=10)
        at.run()
        return at

    return _create


def _set_input(at, value):
    at.text_input[0].set_value(value).run()
    return at


def _click(at, label):
    for btn in at.button:
        if btn.label == label:
            btn.click().run()
            return at
    raise AssertionError(
        f"No button '{label}'. Found: {[b.label for b in at.button]}"
    )


def _load_student(at, hash=HASH_AT_RISK):
    _set_input(at, hash)
    _click(at, "Retrieve")
    return at


def _has_text(at, text, attr="markdown"):
    return any(text in el.value for el in getattr(at, attr))


def _button_labels(at):
    return [b.label for b in at.button]


# ---------------------------------------------------------------------------
# Page load
# ---------------------------------------------------------------------------

def test_initial_load_shows_search_retrieve_and_dashboard_link(app):
    at = app(FakeService())
    assert at.text_input[0].label == "Deidentified student reference"
    assert "Retrieve" in _button_labels(at)
    # st.link_button is not a queryable AppTest attribute in streamlit 1.64;
    # the LinkButton proto lives in a column as an UnknownElement.
    assert any(
        getattr(child.proto, "label", None) == "View Dashboard"
        for col in at.columns
        for child in col.children.values()
    )


def test_initial_load_shows_empty_state(app):
    at = app(FakeService())
    assert _has_text(at, "Retrieve a deidentified student record")
    assert len(at.error) == 0


# ---------------------------------------------------------------------------
# Search / Retrieve
# ---------------------------------------------------------------------------

def test_retrieve_empty_input_shows_error(app):
    at = app(FakeService())
    _click(at, "Retrieve")
    assert _has_text(at, "Enter a deidentified student reference", attr="error")


def test_retrieve_unknown_student_shows_not_found_error(app):
    at = app(FakeService())
    _set_input(at, "nonexistent-hash")
    _click(at, "Retrieve")
    assert _has_text(at, "No prediction was found", attr="error")


def test_retrieve_service_error_shows_generic_error(app):
    at = app(FakeService(profile_error=RuntimeError("db down")))
    _set_input(at, "any-hash")
    _click(at, "Retrieve")
    assert _has_text(at, "currently unavailable", attr="error")


# ---------------------------------------------------------------------------
# Profile display
# ---------------------------------------------------------------------------

def test_at_risk_student_shows_profile_with_briefing_actions(app):
    at = app(FakeService())
    _load_student(at, HASH_AT_RISK)
    assert _has_text(at, "At Risk")
    assert _has_text(at, "78.5%")
    assert _has_text(at, "AI-Assisted Advisor Briefing")
    assert "Generate Advisor Briefing" in _button_labels(at)
    assert "Retrieve Saved" in _button_labels(at)
    assert "Regenerate" in _button_labels(at)


def test_at_risk_student_shows_snapshot_values(app):
    at = app(FakeService())
    _load_student(at, HASH_AT_RISK)
    assert _has_text(at, "Attendance mode")
    assert _has_text(at, "Synthetic online")
    assert _has_text(at, "Enrolment year")


def test_not_at_risk_student_shows_info_and_no_briefing_actions(app):
    at = app(FakeService())
    _load_student(at, HASH_NOT_AT_RISK)
    assert _has_text(at, "Not At Risk")
    assert _has_text(at, "not currently classified as at risk", attr="info")
    assert "Generate Advisor Briefing" not in _button_labels(at)


# ---------------------------------------------------------------------------
# Generate Advisor Briefing
# ---------------------------------------------------------------------------

def test_generate_briefing_displays_text_metadata_checkbox_and_download(app):
    at = app(FakeService(briefing=_briefing()))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Generate Advisor Briefing")
    # Briefing text
    assert _has_text(at, "The student is at risk.")
    # Metadata (source, validation, attempt)
    assert _has_text(at, "Source:")
    assert _has_text(at, "Validation:")
    assert _has_text(at, "Attempt:")
    # Review checkbox
    assert any(
        cb.label == "I have reviewed this AI-generated briefing"
        for cb in at.checkbox
    )
    # Download button
    assert any(
        b.label == "Download Briefing" for b in at.download_button
    )


def test_generate_briefing_not_produced_shows_error(app):
    at = app(FakeService(request_error=BriefingNotProducedError("generation")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Generate Advisor Briefing")
    assert _has_text(at, "could not be produced", attr="error")
    assert _has_text(at, "generation", attr="error")


def test_generate_briefing_storage_error_shows_error(app):
    at = app(FakeService(request_error=BriefingStorageError("disk full")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Generate Advisor Briefing")
    assert _has_text(at, "generated but could not be stored", attr="error")


def test_generate_briefing_generic_error_shows_error(app):
    at = app(FakeService(request_error=RuntimeError("boom")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Generate Advisor Briefing")
    assert _has_text(at, "briefing workflow is currently unavailable", attr="error")


# ---------------------------------------------------------------------------
# Retrieve Saved
# ---------------------------------------------------------------------------

def test_retrieve_saved_displays_stored_briefing(app):
    stored = _briefing(source="stored")
    at = app(FakeService(stored_briefing=stored))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Retrieve Saved")
    assert _has_text(at, "The student is at risk.")
    assert _has_text(at, "Stored")  # source shown in metadata


def test_retrieve_saved_no_briefing_shows_info(app):
    at = app(FakeService())  # stored_briefing defaults to None
    _load_student(at, HASH_AT_RISK)
    _click(at, "Retrieve Saved")
    assert _has_text(
        at, "No previously validated briefing is available", attr="info"
    )


def test_retrieve_saved_error_shows_error(app):
    at = app(FakeService(retrieve_error=RuntimeError("db down")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Retrieve Saved")
    assert _has_text(at, "saved briefing is currently unavailable", attr="error")


# ---------------------------------------------------------------------------
# Regenerate
# ---------------------------------------------------------------------------

def test_regenerate_displays_briefing(app):
    at = app(FakeService(briefing=_briefing()))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Regenerate")
    assert _has_text(at, "The student is at risk.")


def test_regenerate_not_produced_shows_error(app):
    at = app(FakeService(request_error=BriefingNotProducedError("validation")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Regenerate")
    assert _has_text(at, "could not be produced", attr="error")
    assert _has_text(at, "validation", attr="error")


def test_regenerate_generic_error_shows_error(app):
    at = app(FakeService(request_error=RuntimeError("oops")))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Regenerate")
    assert _has_text(at, "briefing workflow is currently unavailable", attr="error")


# ---------------------------------------------------------------------------
# Review checkbox
# ---------------------------------------------------------------------------

def test_review_checkbox_can_be_toggled(app):
    at = app(FakeService(briefing=_briefing()))
    _load_student(at, HASH_AT_RISK)
    _click(at, "Generate Advisor Briefing")
    cb = [
        c for c in at.checkbox
        if c.label == "I have reviewed this AI-generated briefing"
    ][0]
    assert not cb.value
    cb.set_value(True)
    at.run()
    cb = [
        c for c in at.checkbox
        if c.label == "I have reviewed this AI-generated briefing"
    ][0]
    assert cb.value
