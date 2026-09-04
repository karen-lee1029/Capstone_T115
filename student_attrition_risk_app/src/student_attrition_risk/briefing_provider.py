"""Briefing generation adapters and deterministic fallback."""

from typing import Any

from .models import StudentBriefing, StudentRiskProfile

SYSTEM_PROMPT = """
You create concise briefings for university advisors from synthetic,
cross-sectional student risk profiles.

Use only the supplied values. Do not invent facts, personal circumstances,
causes or historical trends. Snapshot values are observations, not causes or
individual prediction drivers. Do not make punitive or automatic decisions.
Treat similarly named fields as separate measurements unless the supplied data
explicitly says they conflict. Do not infer a conflict merely because values differ.
Use only the overall commencing/continuing status in the briefing; ignore
teaching-period status. If age is available, report only the supplied age band,
never the exact age. International/domestic status may be included as neutral context.
Do not describe it as a cause, risk factor, or reason for different treatment.

Return exactly three sections:

Risk Overview
State the supplied risk percentage and stored At Risk or Not At Risk
classification. Explain that it is a model-generated signal.

Relevant Academic Snapshot
Summarise the most useful supplied academic information in natural language.
Prioritise enrolled, passed, failed and withdrawn credit points, followed by
study load, student stage and attendance mode.

If withdrawn credit points exceed passed credit points, state that comparison
as a notable point for review, without calling it excessive or abnormal.

Points for Advisor Review
Provide exactly three practical, non-repeating suggestions selected from:

- Review failed outcomes and whether academic-skills or course advice may help.
- Review withdrawals and whether the enrolment plan remains appropriate.
- Confirm whether a part-time study load remains suitable.
- Offer transition or orientation information to a commencing student.
- Check online-learning access for an online student.
- Verify conflicting source information.

Present suggestions as options for a human advisor, not conclusions about the
student.

Finish with: "The signal supports but does not replace professional human
judgement."

Write approximately 130 to 190 words. Do not refer to the student's circumstances
unless circumstances are explicitly included in the supplied profile. Do not
include the student hash, MLflow run ID, JSON or technical field names.
""".strip()


def _profile_prompt(profile: StudentRiskProfile) -> str:
    """Build the user message containing the verified profile."""

    return (
        "Create the advisor briefing using the following verified student "
        "risk profile.\n\n"
        f"{profile.model_dump_json(exclude_none=True)}"
    )


def _extract_response_text(content: Any) -> str:
    """Extract final answer text while excluding model reasoning."""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []

        for part in content:
            if not isinstance(part, dict):
                continue

            # GPT OSS may return both reasoning and final text blocks.
            # Only expose the final text to the application.
            if part.get("type") != "text":
                continue

            text = part.get("text")
            if isinstance(text, str):
                text_parts.append(text)

        return "\n".join(text_parts).strip()

    return ""


class TemplateBriefingProvider:
    """Generate a deterministic briefing without calling an AI model."""

    def generate(
        self,
        profile: StudentRiskProfile,
    ) -> StudentBriefing:
        prediction = profile.prediction
        flag = "At Risk" if prediction.attrition_risk_flag else "Not At Risk"

        text = (
            "Template-generated briefing for synthetic record "
            f"{prediction.student_deidentified_hash}. "
            "The model-generated risk signal is "
            f"{prediction.attrition_risk_percentage:.1f}% ({flag}), "
            "with a prediction threshold of "
            f"{prediction.prediction_threshold:.2f}. "
            "This is a cross-sectional signal, not a longitudinal "
            "assessment or explanation of cause. Consider a supportive, "
            "human-reviewed check-in without assuming personal circumstances."
        )

        return StudentBriefing(
            student_deidentified_hash=(prediction.student_deidentified_hash),
            source="template",
            text=text,
        )


class DatabricksModelBriefingProvider:
    """Generate a briefing through a Databricks model endpoint."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def generate(
        self,
        profile: StudentRiskProfile,
    ) -> StudentBriefing:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.serving import (
            ChatMessage,
            ChatMessageRole,
        )

        client = WorkspaceClient()

        response: Any = client.serving_endpoints.query(
            name=self.model_name,
            messages=[
                ChatMessage(
                    role=ChatMessageRole.SYSTEM,
                    content=SYSTEM_PROMPT,
                ),
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content=_profile_prompt(profile),
                ),
            ],
            temperature=0.2,
            max_tokens=1600,
        )

        choices = response.choices or []

        if not choices or not choices[0].message:
            raise RuntimeError("Managed model returned no briefing response.")

        content = _extract_response_text(choices[0].message.content)

        if not content:
            raise RuntimeError("Managed model returned no briefing text.")

        return StudentBriefing(
            student_deidentified_hash=(profile.prediction.student_deidentified_hash),
            source="databricks_model",
            text=content,
        )
