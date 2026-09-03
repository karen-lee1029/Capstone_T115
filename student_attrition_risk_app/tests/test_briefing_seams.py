"""Foundational seam tests (Feature-001 / US-08): the placeholder implementations of the
generation, instructions, validation, and retry seams. Verifies FR-010, FR-014, FR-016,
FR-019, SC-012."""

import pytest

from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_validation import InterimValidator
from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.models import (
    UNAVAILABLE,
    ApprovedModelFeatureValues,
    BriefingGenerationContext,
    DraftBriefing,
    GenerationFailed,
    StudentPrediction,
    ValidationFailed,
    ValidationOutcome,
)
from student_attrition_risk.retry_workflow import RetryNotConfigured
from student_attrition_risk.student_repository import MODEL_FEATURE_COLUMNS


def _context(composed_prompt: str = "placeholder") -> BriefingGenerationContext:
    features = ApprovedModelFeatureValues(
        values={column: f"v-{column}" for column in MODEL_FEATURE_COLUMNS}
    )
    features.values["detailed_primary_field_of_education"] = UNAVAILABLE
    return BriefingGenerationContext(
        student_deidentified_hash="synthetic-student-001",
        prediction=StudentPrediction(
            student_deidentified_hash="synthetic-student-001",
            attrition_risk_percentage=78.5,
            attrition_risk_flag=True,
            prediction_threshold=0.5,
        ),
        features=features,
        instructions_id="interim-default",
        composed_prompt=composed_prompt,
    )


def test_interim_instructions_label_all_21_features_as_non_causal():
    context = _context()
    prompt = InterimInstructions().compose(context)
    for column in MODEL_FEATURE_COLUMNS:
        assert column in prompt
    assert "unavailable" in prompt  # the UNAVAILABLE marker rendered for the absent column
    lowered = prompt.lower()
    assert "not proven causes" in lowered or "not causes" in lowered or "background context" in lowered
    assert "do not claim raw values caused" in lowered


def test_interim_instructions_id_is_marked_interim():
    assert InterimInstructions().instructions_id == "interim-default"


def test_stub_generation_provider_raises_not_configured_by_default():
    with pytest.raises(ConfigurationError):
        StubGenerationProvider().generate(_context())


def test_stub_generation_provider_returns_supplied_draft():
    draft = DraftBriefing(student_deidentified_hash="synthetic-student-001", text="draft body")
    assert StubGenerationProvider(draft=draft).generate(_context()) is draft


def test_interim_validator_identifies_itself_and_passes():
    outcome = InterimValidator().validate(
        DraftBriefing(student_deidentified_hash="synthetic-student-001", text="draft"), _context()
    )
    assert outcome.passed is True
    assert outcome.validator_id == "interim-pass-through"
    assert outcome.failed_criteria == []
    assert outcome.feedback is None


def test_retry_not_configured_returns_terminal_failure_with_category():
    context = _context()
    assert RetryNotConfigured().run(context, GenerationFailed()).category == "generation"
    validation_failed = ValidationFailed(
        outcome=ValidationOutcome(passed=False, validator_id="stub")
    )
    assert RetryNotConfigured().run(context, validation_failed).category == "validation"
