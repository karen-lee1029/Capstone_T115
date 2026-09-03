"""Retry-workflow seam (Feature-001 / US-08) — the Feature-001 <-> Feature-002 boundary.

Feature-001 defines the ``RetryWorkflow`` seam and ships ``RetryNotConfigured``, a placeholder
that performs **no** retry. Feature-002 / US-15 supplies the concrete ``SingleRetryWorkflow``
through this same interface without changing the Feature-001 orchestration (FR-019, FR-033):
exactly one additional generation attempt after a first-attempt validation failure or a
retryable generation failure, re-validation of the result, and an explicit terminal outcome.
Persistence stays with ``StudentService`` — this workflow only returns the outcome (FR-019).
"""

from .config import ConfigurationError
from .models import (
    BriefingGenerationContext,
    BriefingOutcome,
    FirstAttemptOutcome,
    Produced,
    TerminalFailure,
    ValidationFailed,
    make_validated_briefing,
)
from .ports import BriefingValidator, GenerationProvider


class RetryNotConfigured:
    """Placeholder retry workflow. Performs no generation and reports terminal failure,
    carrying the first attempt's failure category (FR-021)."""

    def run(
        self, context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome
    ) -> TerminalFailure:
        return TerminalFailure(category=first_outcome.category)


# Minimal Feature-002 revision wrapper (approved planning decision 3). It only frames the
# failed criteria and Validation Feedback that validation already returned and points back to
# the instructions already in the prompt. It adds no briefing instructions of its own, does not
# duplicate the US-12 prompt design, and is a single constant meant to be superseded when the
# final US-12 instructions are integrated.
_RETRY_FEEDBACK_HEADER = (
    "\n\n---\n"
    "The previous attempt did not pass validation. Revise the briefing to resolve the points "
    "below, keeping every instruction above unchanged.\n"
)


def _retry_context(
    context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome
) -> BriefingGenerationContext:
    """Build the Attempt 2 request.

    For a validation failure that carried failed criteria or feedback, append the minimal
    revision block relaying exactly those (FR-007). For a generation failure, or a validation
    failure that carried neither, reuse the original composed prompt unchanged (FR-008, FR-010).
    Identity fields (hash, prediction, features, instructions provenance) are always preserved
    (FR-006).
    """
    prompt = context.composed_prompt
    if isinstance(first_outcome, ValidationFailed):
        outcome = first_outcome.outcome
        if outcome.failed_criteria or outcome.feedback:
            block = [_RETRY_FEEDBACK_HEADER]
            if outcome.failed_criteria:
                block.append("Failed acceptance criteria:")
                block.extend(f"- {criterion}" for criterion in outcome.failed_criteria)
            if outcome.feedback:
                block.append(f"Validation feedback: {outcome.feedback}")
            prompt = context.composed_prompt + "\n".join(block)
    return context.model_copy(update={"composed_prompt": prompt})


class SingleRetryWorkflow:
    """Feature-002 / US-15 concrete retry workflow (see module docstring).

    ``run`` performs the generation boundary **exactly once** and the validation boundary
    **at most once**. There is no loop or recursion, so a third generation attempt is
    structurally impossible (FR-002). It never raises except to let a ``ConfigurationError``
    from the retry generation propagate unchanged (FR-004).
    """

    def __init__(
        self, generation_provider: GenerationProvider, validator: BriefingValidator
    ) -> None:
        self.generation_provider = generation_provider
        self.validator = validator

    def run(
        self, context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome
    ) -> BriefingOutcome:
        retry_context = _retry_context(context, first_outcome)
        try:
            draft = self.generation_provider.generate(retry_context)
        except ConfigurationError:
            # Never retried, never templated — surfaced unchanged (FR-004, spec Edge Cases).
            raise
        except Exception:
            return TerminalFailure(category="generation")  # Attempt 2 generation failed (FR-012)

        outcome = self.validator.validate(draft, retry_context)
        if not outcome.passed:
            return TerminalFailure(category="validation")  # Attempt 2 briefing rejected (FR-013)

        briefing = make_validated_briefing(
            student_hash=context.student_deidentified_hash,
            prediction=context.prediction,
            text=draft.text,
            validator_id=outcome.validator_id,
            attempt_count=2,
        )
        # StudentService._hand_off_to_retry persists this; the workflow does not (FR-014, FR-019).
        return Produced(briefing=briefing)
