"""Feature-004 (US-20) — regression groups for the teammate-owned High defects.

Karen and GuaGuaGua88 approved resolving these after Feature-004 logged them. One section per
defect, named after its ID in ``specs/004-final-defect-resolution/defect-register.md``: D1, D2
and D3 (the structured validator), A5 and D7 (application startup). A1–A4 are closed by the
corrected ``tests/test_ui.py`` itself, so they have no group here.

Offline only: the validator is called directly with a mock-repository context, and the app is
built from explicit ``Settings`` with mock data.
"""

import math
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_validation import StructuredBriefingValidator
from student_attrition_risk.config import ConfigurationError, Settings
from student_attrition_risk.main import build_service, create_configuration_error_app
from student_attrition_risk.models import (
    ApprovedModelFeatureValues,
    BriefingGenerationContext,
    DraftBriefing,
)
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import BriefingNotProducedError
from workflow_doubles import FLAGGED, NOT_FLAGGED


def _context(student_hash: str = FLAGGED, **feature_overrides) -> BriefingGenerationContext:
    repository = MockStudentRepository()
    values = dict(repository.get_model_features(student_hash).values)
    values.update(feature_overrides)
    return BriefingGenerationContext(
        student_deidentified_hash=student_hash,
        prediction=repository.get_prediction(student_hash),
        features=ApprovedModelFeatureValues(values=values),
        instructions_id="teammate-highs-test",
        composed_prompt="",
    )


def _briefing_text(
    level: str = "At Risk",
    score: str = "78.5%",
    context_line: str = "The student has passed 72 of 96 enrolled credit points.",
) -> str:
    return (
        "## Risk Summary\n"
        f"The model classifies this student as {level}, with a relative risk score of {score}.\n\n"
        "## Relevant Student Context\n"
        f"{context_line}\n\n"
        "## Recommended Advisor Actions\n"
        "The advisor may consider reaching out to discuss study load.\n\n"
        "## Suggested Next Steps\n"
        "Arrange a check-in and review available support services.\n"
    )


def _validate(text: str, context: BriefingGenerationContext | None = None):
    context = context or _context()
    draft = DraftBriefing(student_deidentified_hash=context.student_deidentified_hash, text=text)
    return StructuredBriefingValidator().validate(draft, context)


def test_baseline_briefing_passes_every_checked_criterion():
    outcome = _validate(_briefing_text())

    assert outcome.passed, outcome.feedback


# ---- D1: risk-level check accepts the opposite classification (register D1) ----


def test_d1_not_at_risk_briefing_fails_for_a_flagged_student():
    outcome = _validate(_briefing_text(level="Not At Risk"))

    assert not outcome.passed
    assert "AC1" in outcome.failed_criteria


def test_d1_hyphenated_at_risk_is_accepted_for_a_flagged_student():
    outcome = _validate(_briefing_text(level="at-risk"))

    assert "AC1" not in outcome.failed_criteria


def test_d1_not_at_risk_is_required_for_a_student_who_is_not_flagged():
    context = _context(NOT_FLAGGED)

    wrong = _validate(_briefing_text(level="At Risk", score="18.0%"), context)
    right = _validate(_briefing_text(level="Not At Risk", score="18.0%"), context)

    assert "AC1" in wrong.failed_criteria
    assert "AC1" not in right.failed_criteria


# ---- D2: risk-score check accepts the whole number anywhere (register D2) ----


def test_d2_wrong_score_with_an_unrelated_78_fails():
    outcome = _validate(
        _briefing_text(score="12.0%", context_line="Ranked 78 of 200. Passed 72 credit points.")
    )

    assert not outcome.passed
    assert "AC1" in outcome.failed_criteria


def test_d2_score_without_its_decimal_place_fails():
    outcome = _validate(_briefing_text(score="78%"))

    assert "AC1" in outcome.failed_criteria


def test_d2_score_inside_a_larger_number_fails():
    outcome = _validate(_briefing_text(score="178.5%"))

    assert "AC1" in outcome.failed_criteria


def test_d2_score_with_a_space_before_the_percent_sign_passes():
    outcome = _validate(_briefing_text(score="78.5 %"))

    assert "AC1" not in outcome.failed_criteria


# ---- D3: "mentions this student's data" check cannot fail (register D3) ----


def test_d3_generic_context_fails_traceability():
    outcome = _validate(
        _briefing_text(context_line="Generic information about students and their study.")
    )

    assert not outcome.passed
    assert "AC8" in outcome.failed_criteria


def test_d3_digits_inside_other_numbers_do_not_count_as_a_mention():
    # 2026 contains "20" and "26"; 7.25 contains "72"-like digits but not the value 72.
    outcome = _validate(
        _briefing_text(context_line="Reviewed in 2026 against a 7.25 benchmark."),
        _context(enrolment_year=1999),
    )

    assert "AC8" in outcome.failed_criteria


def test_d3_zero_and_one_values_do_not_count_as_a_mention():
    context = _context(**{column: 0 for column in (
        "age_at_census", "eftsl", "enrolment_year", "cumulative_credit_points_enrolled",
        "cumulative_credit_points_passed", "cumulative_credit_points_failed",
        "cumulative_credit_points_withdrawn",
    )})

    outcome = _validate(_briefing_text(context_line="Score 1 of 10, level 0."), context)

    assert "AC8" in outcome.failed_criteria


def test_d3_common_words_from_text_values_do_not_count_as_a_mention():
    context = _context(attendance_mode="Full_time", socioeconomic_status="Low")

    outcome = _validate(
        _briefing_text(context_line="The student should follow up in time."), context
    )

    assert "AC8" in outcome.failed_criteria


def test_d3_a_whole_text_value_counts_as_a_mention():
    context = _context(attendance_mode="Full_time")

    outcome = _validate(_briefing_text(context_line="The student studies full time."), context)

    assert "AC8" not in outcome.failed_criteria


def test_d3_non_finite_values_are_skipped_rather_than_crashing():
    context = _context(eftsl=math.nan, age_at_census=math.inf)

    outcome = _validate(_briefing_text(), context)

    assert outcome.passed, outcome.feedback


# ---- A5: configuration errors hidden behind app = None (register A5) ----


def test_a5_configuration_error_app_names_the_problem_with_503():
    client = TestClient(
        create_configuration_error_app(ConfigurationError("DATABRICKS_WAREHOUSE_ID is required."))
    )

    for method, path in (("get", "/api/health"), ("post", "/api/students/x/briefing"), ("get", "/")):
        response = getattr(client, method)(path)
        assert response.status_code == 503
        assert "DATABRICKS_WAREHOUSE_ID is required." in response.json()["detail"]


def test_a5_configuration_error_is_logged(caplog):
    with caplog.at_level("ERROR", logger="student_attrition_risk.main"):
        create_configuration_error_app(ConfigurationError("BRIEFING_VOLUME must be a Volume path."))

    assert "BRIEFING_VOLUME must be a Volume path." in caplog.text


# ---- D7: mock mode requires DATABRICKS_MODEL_NAME (register D7) ----


def _mock_settings(model_name: str | None) -> Settings:
    return replace(
        Settings.from_env(), use_mock_data=True, model_name=model_name, briefing_volume=None
    )


@pytest.mark.parametrize("model_name", [None, ""])
def test_d7_mock_mode_builds_without_a_model_name(model_name):
    service = build_service(_mock_settings(model_name))

    assert service.get_student_profile(FLAGGED).prediction.student_deidentified_hash == FLAGGED
    assert isinstance(service.generation_provider, StubGenerationProvider)


def test_d7_briefing_request_without_a_model_name_fails_only_at_request_time():
    service = build_service(_mock_settings(None))

    with pytest.raises((ConfigurationError, BriefingNotProducedError)):
        service.request_briefing(FLAGGED)
