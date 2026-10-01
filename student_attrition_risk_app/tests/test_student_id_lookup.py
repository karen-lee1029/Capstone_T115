"""Feature-005 (US-28) — advisors retrieve a student by the dashboard's 16-character Student ID.

The dashboard shows ``LEFT(student_deidentified_hash, 16)`` as the Student ID (FR-026). The
advisor app accepts that ID as well as the full hash (FR-027), and shows the Student ID rather than
the full hash on the student summary. Offline: ``MockStudentRepository`` only.
"""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from student_attrition_risk.models import StudentPrediction, StudentRiskProfile
from student_attrition_risk.student_repository import STUDENT_ID_LENGTH, MockStudentRepository
from student_attrition_risk.student_service import StudentNotFoundError, StudentService

FULL_HASH = "0123456789abcdef" + "f" * 48  # synthetic, hash-shaped
STUDENT_ID = FULL_HASH[:STUDENT_ID_LENGTH]


def _repository() -> MockStudentRepository:
    repository = MockStudentRepository()
    repository.predictions[FULL_HASH] = StudentPrediction(
        student_deidentified_hash=FULL_HASH,
        attrition_risk_percentage=50.5,
        attrition_risk_flag=True,
        prediction_threshold=0.5,
        mlflow_run_id="synthetic-run",
        scored_at="2026-08-20T04:21:32Z",
    )
    return repository


def _service(repository: MockStudentRepository) -> StudentService:
    # Profile lookup touches only the repository; the briefing collaborators are not used.
    return StudentService(repository, None, None, None, None, None)


def test_student_id_matches_dashboard_length():
    assert STUDENT_ID_LENGTH == 16


def test_profile_found_by_dashboard_student_id():
    profile = _service(_repository()).get_student_profile(STUDENT_ID)

    assert profile.prediction.student_deidentified_hash == FULL_HASH
    assert profile.snapshot is not None


def test_profile_still_found_by_full_hash():
    profile = _service(_repository()).get_student_profile(FULL_HASH)

    assert profile.prediction.student_deidentified_hash == FULL_HASH


def test_student_id_shared_by_two_students_is_not_found():
    # The synthetic mock hashes share their first 16 characters ("synthetic-studen").
    service = _service(MockStudentRepository())

    with pytest.raises(StudentNotFoundError):
        service.get_student_profile("synthetic-student-001"[:STUDENT_ID_LENGTH])


def test_unknown_student_id_is_not_found():
    with pytest.raises(StudentNotFoundError):
        _service(_repository()).get_student_profile("0" * STUDENT_ID_LENGTH)


UI_PATH = str(Path(__file__).resolve().parent.parent / "src" / "student_attrition_risk" / "ui.py")


class _ProfileOnlyService:
    """Minimal service fake: profiles from ``MockStudentRepository``; no stored briefing."""

    def __init__(self) -> None:
        self._repository = MockStudentRepository()

    def get_student_profile(self, student_hash):
        return StudentRiskProfile(
            prediction=self._repository.get_prediction(student_hash),
            snapshot=self._repository.get_snapshot(student_hash),
        )

    def has_stored_briefing(self, student_hash):
        return False

    def get_stored_briefing(self, student_hash):
        return None


def test_summary_shows_student_id_not_full_hash(monkeypatch):
    service = _ProfileOnlyService()
    monkeypatch.setattr("student_attrition_risk.main.build_service", lambda *_a, **_kw: service)
    st.cache_resource.clear()
    at = AppTest.from_file(UI_PATH, default_timeout=10)
    at.run()
    at.text_input[0].set_value("synthetic-student-001").run()
    next(b for b in at.button if b.label == "Retrieve").click().run()

    assert not at.exception
    summary = next(el.value for el in at.markdown if "Student summary" in el.value)
    assert "Student ID:" in summary
    assert "synthetic-studen" in summary
    assert "synthetic-student-001" not in summary
    assert "Reference:" not in summary
