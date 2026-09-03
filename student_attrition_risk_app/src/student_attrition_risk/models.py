"""API and domain models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StudentPrediction(BaseModel):
    student_deidentified_hash: str
    attrition_risk_percentage: float = Field(ge=0, le=100)
    attrition_risk_flag: bool
    prediction_threshold: float = Field(ge=0, le=1)
    mlflow_run_id: str | None = None
    scored_at: datetime | None = None


class StudentSnapshot(BaseModel):
    attributes: dict[str, Any]


class StudentRiskProfile(BaseModel):
    prediction: StudentPrediction
    snapshot: StudentSnapshot | None = None


class StudentBriefing(BaseModel):
    student_deidentified_hash: str
    source: str
    text: str


class HealthStatus(BaseModel):
    status: str
    data_source: str
    details: str | None = None


# ---------------------------------------------------------------------------
# Feature-001 (US-08) briefing-workflow types.
#
# These are the objects that cross the generation / instructions / validation /
# retry / persistence seams. Feature-001 defines them once here so US-12/13/14/15
# and Feature-002 import rather than redefine them.
# ---------------------------------------------------------------------------

# Marker placed in ApprovedModelFeatureValues when a source column is absent from
# the Delta schema. Distinct from a SQL NULL value, which is preserved as None.
UNAVAILABLE = "__unavailable__"


class ApprovedModelFeatureValues(BaseModel):
    """The 21 approved model feature values for one deidentified student.

    Ordered mapping ``feature_name -> value | UNAVAILABLE``. Carried as background
    context only, never as a per-student causal explanation (FR-011).
    """

    values: dict[str, Any]


class DraftBriefing(BaseModel):
    """A briefing returned by the generation seam, not yet validated (FR-026)."""

    student_deidentified_hash: str
    text: str


class BriefingGenerationContext(BaseModel):
    """The assembled input handed to the generation seam (FR-009)."""

    student_deidentified_hash: str
    prediction: StudentPrediction
    features: ApprovedModelFeatureValues
    instructions_id: str
    composed_prompt: str


class ValidationOutcome(BaseModel):
    """Returned by the validation seam (FR-015)."""

    passed: bool
    failed_criteria: list[str] = Field(default_factory=list)
    feedback: str | None = None
    validator_id: str


class ValidatedBriefing(BaseModel):
    """A briefing the validation seam passed; the only briefing form returned to a
    caller or handed to the persistence seam (FR-018, FR-025, FR-029)."""

    student_deidentified_hash: str
    text: str
    source: str
    validated: bool = True
    validator_id: str
    generated_at: datetime
    attempt_count: int = 1
    mlflow_run_id: str | None = None
    risk_percentage: float
    at_risk_flag: bool
    prediction_threshold: float
    scored_at: datetime | None = None


class GenerationFailed(BaseModel):
    """First-attempt outcome: the generation seam failed before a draft (FR-019)."""

    category: str = "generation"


class ValidationFailed(BaseModel):
    """First-attempt outcome: a draft was produced but did not pass validation."""

    outcome: ValidationOutcome
    category: str = "validation"


# The payload the backend hands to the retry seam.
FirstAttemptOutcome = GenerationFailed | ValidationFailed


class Produced(BaseModel):
    """Retry-seam outcome: a validated briefing (attempt 1, or Feature-002 attempt 2)."""

    briefing: ValidatedBriefing


class TerminalFailure(BaseModel):
    """Retry-seam outcome: no validated briefing; the backend returns an explicit error (FR-021)."""

    category: str


# The value the retry seam returns.
BriefingOutcome = Produced | TerminalFailure
