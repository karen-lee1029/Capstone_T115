"""Small interfaces shared by adapters and business logic."""

from typing import Protocol

from .models import (
    ApprovedModelFeatureValues,
    BriefingGenerationContext,
    BriefingOutcome,
    DraftBriefing,
    FirstAttemptOutcome,
    StudentBriefing,
    StudentPrediction,
    StudentRiskProfile,
    StudentSnapshot,
    ValidatedBriefing,
    ValidationOutcome,
)


class StudentRepository(Protocol):
    def get_prediction(self, student_hash: str) -> StudentPrediction | None: ...

    def get_snapshot(self, student_hash: str) -> StudentSnapshot | None: ...

    def get_model_features(self, student_hash: str) -> ApprovedModelFeatureValues | None: ...

    def get_high_risk_students(self, limit: int) -> list[StudentPrediction]: ...

    def health_check(self) -> bool: ...


class BriefingProvider(Protocol):
    def generate(self, profile: StudentRiskProfile) -> StudentBriefing: ...


# ---------------------------------------------------------------------------
# Feature-001 (US-08) briefing-workflow seams.
#
# Feature-001 defines each interface and ships a placeholder / in-memory
# implementation. Concrete implementations are later backlog stories:
#   GenerationProvider   -> US-13
#   BriefingInstructions -> US-12
#   BriefingValidator    -> US-14
#   RetryWorkflow        -> Feature-002 / US-15
#   BriefingStore        -> US-15
# ---------------------------------------------------------------------------


class GenerationProvider(Protocol):
    def generate(self, context: BriefingGenerationContext) -> DraftBriefing:
        """Return a draft briefing, or raise on a failure before a draft exists."""
        ...


class BriefingInstructions(Protocol):
    instructions_id: str

    def compose(self, context: BriefingGenerationContext) -> str: ...


class BriefingValidator(Protocol):
    def validate(
        self, draft: DraftBriefing, context: BriefingGenerationContext
    ) -> ValidationOutcome: ...


class RetryWorkflow(Protocol):
    def run(
        self, context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome
    ) -> BriefingOutcome: ...


class BriefingStore(Protocol):
    def has_validated(self, student_hash: str) -> bool: ...

    def get_latest_validated(self, student_hash: str) -> ValidatedBriefing | None: ...

    def save_validated(self, briefing: ValidatedBriefing) -> None: ...
