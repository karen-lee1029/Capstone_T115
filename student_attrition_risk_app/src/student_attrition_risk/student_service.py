"""Shared application business logic."""

from .models import HealthStatus, StudentBriefing, StudentPrediction, StudentRiskProfile
from .ports import BriefingProvider, StudentRepository


class StudentNotFoundError(LookupError):
    """Raised at the service boundary for an unknown hash."""


class StudentService:
    def __init__(self, repository: StudentRepository, briefing_provider: BriefingProvider) -> None:
        self.repository = repository
        self.briefing_provider = briefing_provider

    def get_student_profile(self, student_hash: str) -> StudentRiskProfile:
        prediction = self.repository.get_prediction(student_hash)
        if prediction is None:
            raise StudentNotFoundError(student_hash)
        return StudentRiskProfile(prediction=prediction, snapshot=self.repository.get_snapshot(student_hash))

    def get_high_risk_students(self, limit: int = 20) -> list[StudentPrediction]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return self.repository.get_high_risk_students(limit)

    def generate_briefing(self, student_hash: str) -> StudentBriefing:
        profile = self.get_student_profile(student_hash)
        try:
            return self.briefing_provider.generate(profile)
        except Exception:
            from .briefing_provider import TemplateBriefingProvider

            return TemplateBriefingProvider().generate(profile)

    def health_check(self) -> HealthStatus:
        healthy = self.repository.health_check()
        return HealthStatus(status="ok" if healthy else "degraded", data_source="mock_or_databricks_sql")
