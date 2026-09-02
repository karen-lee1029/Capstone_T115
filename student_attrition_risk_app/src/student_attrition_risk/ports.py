"""Small interfaces shared by adapters and business logic."""

from typing import Protocol

from .models import StudentBriefing, StudentPrediction, StudentRiskProfile, StudentSnapshot


class StudentRepository(Protocol):
    def get_prediction(self, student_hash: str) -> StudentPrediction | None: ...

    def get_snapshot(self, student_hash: str) -> StudentSnapshot | None: ...

    def get_high_risk_students(self, limit: int) -> list[StudentPrediction]: ...

    def health_check(self) -> bool: ...


class BriefingProvider(Protocol):
    def generate(self, profile: StudentRiskProfile) -> StudentBriefing: ...
