"""Shared application business logic."""

import logging

from .config import ConfigurationError
from .models import (
    UNAVAILABLE,
    ApprovedModelFeatureValues,
    BriefingGenerationContext,
    GenerationFailed,
    HealthStatus,
    Produced,
    StudentPrediction,
    StudentRiskProfile,
    ValidatedBriefing,
    ValidationFailed,
    ValidationOutcome,
    make_validated_briefing,
)
from .ports import (
    BriefingInstructions,
    BriefingStore,
    BriefingValidator,
    GenerationProvider,
    RetryWorkflow,
    StudentRepository,
)
from .student_repository import MODEL_FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class StudentNotFoundError(LookupError):
    """Raised at the service boundary for an unknown hash."""


class StudentNotAtRiskError(Exception):
    """The student exists but the model at-risk flag is not set; briefing generation is
    refused and no seam is invoked for generation (FR-034)."""


class BriefingNotProducedError(Exception):
    """The retry seam concluded without a validated briefing (FR-021).

    ``category`` is ``"generation"`` or ``"validation"`` for the last failure.
    """

    def __init__(self, category: str) -> None:
        super().__init__(f"briefing could not be produced ({category})")
        self.category = category


class BriefingStorageError(Exception):
    """The persistence seam reported that a validated briefing could not be stored (FR-024)."""


def _log_outcome(
    *,
    student_deidentified_hash: str,
    outcome: str,
    attempt_count: int | None = None,
    validator_id: str | None = None,
    exception: BaseException | None = None,
) -> None:
    """Emit a metadata-only workflow log line.

    Never receives or emits prompt text, briefing text, or secrets (FR-031, FR-032).
    """
    logger.info(
        "briefing_workflow outcome=%s hash=%s attempt_count=%s validator_id=%s error=%s",
        outcome,
        student_deidentified_hash,
        attempt_count,
        validator_id,
        type(exception).__name__ if exception is not None else None,
    )


class StudentService:
    def __init__(
        self,
        repository: StudentRepository,
        generation_provider: GenerationProvider,
        instructions: BriefingInstructions,
        validator: BriefingValidator,
        retry_workflow: RetryWorkflow,
        store: BriefingStore,
    ) -> None:
        self.repository = repository
        self.generation_provider = generation_provider
        self.instructions = instructions
        self.validator = validator
        self.retry_workflow = retry_workflow
        self.store = store

    def get_student_profile(self, student_hash: str) -> StudentRiskProfile:
        prediction = self.repository.get_prediction(student_hash)
        if prediction is None:
            raise StudentNotFoundError(student_hash)
        return StudentRiskProfile(prediction=prediction, snapshot=self.repository.get_snapshot(student_hash))

    def get_high_risk_students(self, limit: int = 20) -> list[StudentPrediction]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return self.repository.get_high_risk_students(limit)

    def request_briefing(self, student_hash: str, regenerate: bool = False) -> ValidatedBriefing:
        """Coordinate a Structured Advisor Briefing request end to end through the seams
        (contracts/internal-seams.md "Orchestration call order")."""
        prediction = self.repository.get_prediction(student_hash)
        if prediction is None:
            _log_outcome(student_deidentified_hash=student_hash, outcome="not_found")
            raise StudentNotFoundError(student_hash)

        if not prediction.attrition_risk_flag:
            _log_outcome(student_deidentified_hash=student_hash, outcome="not_at_risk")
            raise StudentNotAtRiskError(student_hash)

        if not regenerate and self.store.has_validated(student_hash):
            existing = self.store.get_latest_validated(student_hash)
            assert existing is not None  # has_validated guarantees this
            _log_outcome(
                student_deidentified_hash=student_hash,
                outcome="returned_existing",
                attempt_count=existing.attempt_count,
                validator_id=existing.validator_id,
            )
            return existing.model_copy(update={"source": "stored"})

        context = self._build_context(student_hash, prediction)

        try:
            draft = self.generation_provider.generate(context)
        except ConfigurationError:
            # Generation is not configured, or a policy/platform constraint forbids a feature
            # (FR-008/FR-014). Surface as-is; never routed to the retry seam, never templated.
            raise
        except Exception as exc:  # a genuine generative-provider failure before a draft (FR-019)
            return self._hand_off_to_retry(
                student_hash, context, GenerationFailed(), generation_exc=exc
            )

        outcome = self.validator.validate(draft, context)
        if outcome.passed:
            briefing = self._build_validated(student_hash, prediction, draft.text, outcome, 1)
            self._persist(student_hash, briefing)
            _log_outcome(
                student_deidentified_hash=student_hash,
                outcome="generated",
                attempt_count=1,
                validator_id=outcome.validator_id,
            )
            return briefing

        return self._hand_off_to_retry(student_hash, context, ValidationFailed(outcome=outcome))

    def get_stored_briefing(self, student_hash: str) -> ValidatedBriefing | None:
        """Return the most recent stored validated briefing, or ``None`` for "none available".
        No at-risk check, no generation (FR-028/FR-030)."""
        prediction = self.repository.get_prediction(student_hash)
        if prediction is None:
            _log_outcome(student_deidentified_hash=student_hash, outcome="not_found")
            raise StudentNotFoundError(student_hash)
        existing = self.store.get_latest_validated(student_hash)
        if existing is None:
            _log_outcome(student_deidentified_hash=student_hash, outcome="none_available")
            return None
        _log_outcome(
            student_deidentified_hash=student_hash,
            outcome="returned_existing",
            attempt_count=existing.attempt_count,
            validator_id=existing.validator_id,
        )
        return existing.model_copy(update={"source": "stored"})

    def health_check(self) -> HealthStatus:
        healthy = self.repository.health_check()
        return HealthStatus(status="ok" if healthy else "degraded", data_source="mock_or_databricks_sql")

    # -- internal helpers ---------------------------------------------------

    def _build_context(
        self, student_hash: str, prediction: StudentPrediction
    ) -> BriefingGenerationContext:
        features = self.repository.get_model_features(student_hash) or ApprovedModelFeatureValues(
            values={column: UNAVAILABLE for column in MODEL_FEATURE_COLUMNS}
        )
        context = BriefingGenerationContext(
            student_deidentified_hash=student_hash,
            prediction=prediction,
            features=features,
            instructions_id=self.instructions.instructions_id,
            composed_prompt="",
        )
        return context.model_copy(
            update={"composed_prompt": self.instructions.compose(context)}
        )

    def _build_validated(
        self,
        student_hash: str,
        prediction: StudentPrediction,
        text: str,
        outcome: ValidationOutcome,
        attempt_count: int,
    ) -> ValidatedBriefing:
        return make_validated_briefing(
            student_hash=student_hash,
            prediction=prediction,
            text=text,
            validator_id=outcome.validator_id,
            attempt_count=attempt_count,
        )

    def _persist(self, student_hash: str, briefing: ValidatedBriefing) -> None:
        try:
            self.store.save_validated(briefing)
        except BriefingStorageError as exc:
            _log_outcome(
                student_deidentified_hash=student_hash, outcome="storage_error", exception=exc
            )
            raise

    def _hand_off_to_retry(
        self,
        student_hash: str,
        context: BriefingGenerationContext,
        first_outcome: GenerationFailed | ValidationFailed,
        generation_exc: BaseException | None = None,
    ) -> ValidatedBriefing:
        result = self.retry_workflow.run(context, first_outcome)
        if isinstance(result, Produced):
            # Only reachable once Feature-002 supplies a real retry workflow. Its briefing has
            # not been stored by this request, so persist it here (FR-018).
            self._persist(student_hash, result.briefing)
            _log_outcome(
                student_deidentified_hash=student_hash,
                outcome="generated",
                attempt_count=result.briefing.attempt_count,
                validator_id=result.briefing.validator_id,
            )
            return result.briefing
        category = result.category
        _log_outcome(
            student_deidentified_hash=student_hash,
            outcome=f"terminal_{category}",
            exception=generation_exc,
        )
        raise BriefingNotProducedError(category)
