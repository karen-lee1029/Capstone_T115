"""Briefing generation adapters and the deterministic fallback."""

from typing import Any

from .config import ConfigurationError
from .models import BriefingGenerationContext, DraftBriefing, StudentBriefing, StudentRiskProfile


def _prompt(profile: StudentRiskProfile) -> str:
    return (
        "Write a concise, neutral, supportive briefing for a human reviewer about this synthetic record. "
        "Use only the supplied structured values. State that the risk is a model-generated signal, "
        "make no historical claims, and do not infer health, disability, finances, family circumstances, "
        "motivation, behaviour, or personal causes. Do not claim raw values caused the prediction. "
        "Suggest a non-punitive, human-reviewed check-in.\n\n"
        f"PROFILE JSON: {profile.model_dump_json()}"
    )


class TemplateBriefingProvider:
    def generate(self, profile: StudentRiskProfile) -> StudentBriefing:
        prediction = profile.prediction
        flag = "At Risk" if prediction.attrition_risk_flag else "Not At Risk"
        text = (
            f"Template-generated briefing for synthetic record {prediction.student_deidentified_hash}. "
            f"The model-generated risk signal is {prediction.attrition_risk_percentage:.1f}% ({flag}), "
            f"with a prediction threshold of {prediction.prediction_threshold:.2f}. "
            "This is a cross-sectional signal, not a longitudinal assessment or explanation of cause. "
            "Consider a supportive, human-reviewed check-in without assuming personal circumstances."
        )
        return StudentBriefing(
            student_deidentified_hash=prediction.student_deidentified_hash,
            source="template",
            text=text,
        )


class DatabricksModelBriefingProvider:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def generate(self, profile: StudentRiskProfile) -> StudentBriefing:
        from databricks.sdk import WorkspaceClient

        client = WorkspaceClient()
        response: Any = client.serving_endpoints.query(
            name=self.model_name,
            messages=[{"role": "user", "content": _prompt(profile)}],
            temperature=0.2,
            max_tokens=250,
        )
        choices = getattr(response, "choices", None) or response.get("choices", [])
        content = choices[0].message.content if choices else ""
        if not content:
            raise RuntimeError("Managed model returned no briefing text.")
        return StudentBriefing(
            student_deidentified_hash=profile.prediction.student_deidentified_hash,
            source="databricks_model",
            text=content,
        )


class StubGenerationProvider:
    """Feature-001 (US-08) placeholder for the ``GenerationProvider`` seam.

    The concrete generative integration (the OpenAI API) is owned by **US-13**. Until then,
    the default behaviour is to raise ``ConfigurationError`` so an unconfigured backend fails
    fast and explicitly — never a template briefing masquerading as success (FR-014, FR-020).

    Tests pass ``draft=`` to return a fixed ``DraftBriefing`` or ``raises=`` to raise a chosen
    error, exercising the orchestration without any external service.
    """

    def __init__(
        self,
        draft: DraftBriefing | None = None,
        raises: BaseException | None = None,
    ) -> None:
        self._draft = draft
        self._raises = raises

    def generate(self, context: BriefingGenerationContext) -> DraftBriefing:
        if self._raises is not None:
            raise self._raises
        if self._draft is not None:
            return self._draft
        raise ConfigurationError("Briefing generation is not configured")
