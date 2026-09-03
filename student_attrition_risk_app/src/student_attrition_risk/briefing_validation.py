"""Briefing-validation seam (Feature-001 / US-08).

Feature-001 provides only the ``BriefingValidator`` seam plus an interim pass-through
placeholder. It invents **no** acceptance criteria. The real Structured Advisor Briefing
acceptance-criteria validation is owned by **US-14** and will be supplied through this same
seam without changing the orchestration (FR-016).
"""

from .models import BriefingGenerationContext, DraftBriefing, ValidationOutcome


class InterimValidator:
    """Interim development behaviour only — always passes. The ``validator_id`` on every
    ``ValidationOutcome`` marks results produced by this placeholder so they are never
    mistaken for final validation (FR-016)."""

    validator_id = "interim-pass-through"

    def validate(
        self, draft: DraftBriefing, context: BriefingGenerationContext
    ) -> ValidationOutcome:
        return ValidationOutcome(
            passed=True,
            failed_criteria=[],
            feedback=None,
            validator_id=self.validator_id,
        )
