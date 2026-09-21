"""Feature-002 (US-15) — SingleRetryWorkflow unit behaviour. Offline: scripted doubles only.

US1 (retry recovers): validation-failure / generation-failure retry success, retry-request
construction. US2 (fails safely): terminal generation / validation, no third attempt,
ConfigurationError propagation.
"""

import pytest

from doubles import ScriptedGenerationProvider, ScriptedValidator
from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.models import (
    ApprovedModelFeatureValues,
    BriefingGenerationContext,
    DraftBriefing,
    GenerationFailed,
    Produced,
    StudentPrediction,
    TerminalFailure,
    ValidationFailed,
    ValidationOutcome,
)
from student_attrition_risk.retry_workflow import SingleRetryWorkflow

HASH = "synthetic-student-001"


def _context(prompt: str = "ORIGINAL PROMPT") -> BriefingGenerationContext:
    return BriefingGenerationContext(
        student_deidentified_hash=HASH,
        prediction=StudentPrediction(
            student_deidentified_hash=HASH,
            attrition_risk_percentage=78.5,
            attrition_risk_flag=True,
            prediction_threshold=0.5,
            mlflow_run_id="run-1",
        ),
        features=ApprovedModelFeatureValues(values={"age_at_census": 21}),
        instructions_id="interim-default",
        composed_prompt=prompt,
    )


def _draft(text: str) -> DraftBriefing:
    return DraftBriefing(student_deidentified_hash=HASH, text=text)


def _passed(validator_id: str = "stub-validator") -> ValidationOutcome:
    return ValidationOutcome(passed=True, validator_id=validator_id)


def _failed(*, failed_criteria=None, feedback=None) -> ValidationOutcome:
    return ValidationOutcome(
        passed=False,
        failed_criteria=list(failed_criteria or []),
        feedback=feedback,
        validator_id="stub-validator",
    )


class _RecordingGeneration(ScriptedGenerationProvider):
    """Captures the context handed to the (single) retry generation call."""

    def __init__(self, *actions) -> None:
        super().__init__(*actions)
        self.seen_context: BriefingGenerationContext | None = None

    def generate(self, context):
        self.seen_context = context
        return super().generate(context)


# --- US1: the retry recovers -------------------------------------------------


def test_validation_failure_then_retry_success_produces_attempt_2():
    gen = ScriptedGenerationProvider(_draft("second briefing"))
    val = ScriptedValidator(_passed("real-validator"))
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=val)

    result = workflow.run(
        _context(), ValidationFailed(outcome=_failed(feedback="add the model-signal caveat"))
    )

    assert isinstance(result, Produced)
    assert result.briefing.attempt_count == 2
    assert result.briefing.text == "second briefing"
    assert result.briefing.validator_id == "real-validator"
    assert result.briefing.source == "generated"
    assert result.briefing.risk_percentage == 78.5
    assert gen.calls == 1
    assert val.calls == 1


def test_generation_failure_then_retry_success_produces_attempt_2():
    gen = ScriptedGenerationProvider(_draft("recovered briefing"))
    val = ScriptedValidator(_passed())
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=val)

    result = workflow.run(_context(), GenerationFailed())

    assert isinstance(result, Produced)
    assert result.briefing.attempt_count == 2
    assert gen.calls == 1
    assert val.calls == 1


def test_retry_request_for_validation_failure_carries_criteria_and_feedback():
    gen = _RecordingGeneration(_draft("x"))
    workflow = SingleRetryWorkflow(
        generation_provider=gen, validator=ScriptedValidator(_passed())
    )
    original = _context("ORIGINAL PROMPT")

    workflow.run(
        original,
        ValidationFailed(
            outcome=_failed(
                failed_criteria=["missing-risk-caveat", "advisor-tone"],
                feedback="soften the tone and add the caveat",
            )
        ),
    )

    retry_prompt = gen.seen_context.composed_prompt
    assert retry_prompt.startswith("ORIGINAL PROMPT")
    assert "missing-risk-caveat" in retry_prompt
    assert "advisor-tone" in retry_prompt
    assert "soften the tone and add the caveat" in retry_prompt
    # identity / factual content preserved (FR-006)
    assert gen.seen_context.student_deidentified_hash == original.student_deidentified_hash
    assert gen.seen_context.prediction == original.prediction
    assert gen.seen_context.features == original.features
    assert gen.seen_context.instructions_id == original.instructions_id


def test_retry_request_for_validation_failure_without_criteria_or_feedback_is_unchanged():
    gen = _RecordingGeneration(_draft("x"))
    workflow = SingleRetryWorkflow(
        generation_provider=gen, validator=ScriptedValidator(_passed())
    )

    # interim pass-through validator carries neither criteria nor feedback
    workflow.run(_context("ORIGINAL PROMPT"), ValidationFailed(outcome=_failed()))

    assert gen.seen_context.composed_prompt == "ORIGINAL PROMPT"


def test_retry_request_for_generation_failure_is_unchanged():
    gen = _RecordingGeneration(_draft("x"))
    workflow = SingleRetryWorkflow(
        generation_provider=gen, validator=ScriptedValidator(_passed())
    )

    workflow.run(_context("ORIGINAL PROMPT"), GenerationFailed())

    assert gen.seen_context.composed_prompt == "ORIGINAL PROMPT"


# --- US2: the retry also fails --------------------------------------------


def test_attempt_2_generation_failure_is_terminal_generation():
    gen = ScriptedGenerationProvider(RuntimeError("provider down"))
    val = ScriptedValidator()  # must not be reached
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=val)

    result = workflow.run(_context(), ValidationFailed(outcome=_failed()))

    assert isinstance(result, TerminalFailure)
    assert result.category == "generation"
    assert gen.calls == 1
    assert val.calls == 0


def test_attempt_2_validation_failure_is_terminal_validation():
    gen = ScriptedGenerationProvider(_draft("still not good enough"))
    val = ScriptedValidator(_failed(feedback="still missing the caveat"))
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=val)

    result = workflow.run(_context(), GenerationFailed())

    assert isinstance(result, TerminalFailure)
    assert result.category == "validation"
    assert gen.calls == 1
    assert val.calls == 1


def test_run_performs_exactly_one_generation_and_no_third_attempt():
    gen = ScriptedGenerationProvider(_draft("second"))
    val = ScriptedValidator(_passed())
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=val)

    workflow.run(_context(), ValidationFailed(outcome=_failed()))

    # Exactly one retry generation + one revalidation; the scripts are now exhausted so any
    # further call into the doubles would raise AssertionError.
    assert gen.calls == 1
    assert val.calls == 1


def test_configuration_error_on_retry_generation_is_re_raised_not_terminal():
    gen = ScriptedGenerationProvider(
        ConfigurationError("Briefing generation is not configured")
    )
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=ScriptedValidator())

    with pytest.raises(ConfigurationError):
        workflow.run(_context(), GenerationFailed())
