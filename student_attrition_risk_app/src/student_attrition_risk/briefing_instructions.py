"""Briefing-instructions seam (Feature-001 / US-08).

Feature-001 provides only the ``BriefingInstructions`` seam plus a minimal interim
placeholder. The final Default Structured Briefing Prompt Instructions — the required
sections, language guidance, and acceptance-criteria content — are owned by **US-12**
and will be supplied through this same seam without changing the orchestration (FR-010).
"""

from typing import Any

from .briefing_provider import _prompt
from .models import UNAVAILABLE, BriefingGenerationContext, StudentRiskProfile


def _render(value: Any) -> str:
    if value == UNAVAILABLE:
        return "unavailable"
    if value is None:
        return "null"
    return str(value)


class InterimInstructions:
    """Interim placeholder. Reuses the existing safe proof-of-concept prompt wording
    (neutral, no historical or causal claims, no sensitive inferences) and lists the 21
    approved feature values as labelled, explicitly non-causal context (FR-011)."""

    instructions_id = "interim-default"

    def compose(self, context: BriefingGenerationContext) -> str:
        profile = StudentRiskProfile(prediction=context.prediction)
        labelled = "\n".join(
            f"- {name}: {_render(value)}" for name, value in context.features.values.items()
        )
        return (
            f"{_prompt(profile)}\n\n"
            "APPROVED MODEL FEATURE VALUES "
            "(background context only; not proven causes or per-student explanations of the "
            "risk result):\n"
            f"{labelled}"
        )
