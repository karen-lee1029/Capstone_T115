"""Retry-workflow seam (Feature-001 / US-08) — the Feature-001 <-> Feature-002 boundary.

Feature-001 defines the ``RetryWorkflow`` seam and ships a placeholder that performs **no**
retry. The concrete single-retry behaviour (capturing failed criteria and feedback,
constructing the retry request, exactly one additional generation attempt, validating it,
and deciding terminal failure) is owned by **Feature-002 / US-15** and will be supplied
through this same interface without changing the Feature-001 orchestration (FR-019, FR-033).
"""

from .models import BriefingGenerationContext, FirstAttemptOutcome, TerminalFailure


class RetryNotConfigured:
    """Placeholder retry workflow. Performs no generation and reports terminal failure,
    carrying the first attempt's failure category (FR-021)."""

    def run(
        self, context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome
    ) -> TerminalFailure:
        return TerminalFailure(category=first_outcome.category)
