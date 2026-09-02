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
