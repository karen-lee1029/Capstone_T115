"""Feature-003 (US-18) controlled outcomes and recorders.

Extends the Feature-002 ``tests/doubles.py`` convention; that module is read-only here and is
imported rather than modified. This module adds only what does not already exist: a prompt-aware
generation double, a seam-call recorder, a write-counting store wrapper, and the composition
helper the scenarios assemble services with.

Everything here is offline: no network, no workspace, no credentials.
See ``specs/003-briefing-workflow-testing/contracts/workflow-doubles.md``.
"""

from __future__ import annotations

from typing import Any

from doubles import FakeFilesClient, ScriptedGenerationProvider, ScriptedValidator  # noqa: F401
from student_attrition_risk.api import create_api
from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_store import InMemoryBriefingStore, VolumeBriefingStore
from student_attrition_risk.models import (
    BriefingGenerationContext,
    DraftBriefing,
    ValidatedBriefing,
    ValidationOutcome,
)
from student_attrition_risk.retry_workflow import SingleRetryWorkflow
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import BriefingStorageError, StudentService

# Mock-repository fixtures (student_repository.MockStudentRepository).
FLAGGED = "synthetic-student-001"  # at risk, 78.5%
NOT_FLAGGED = "synthetic-student-002"  # not at risk, 18.0%
HAS_EXISTING = "synthetic-student-003"  # at risk, 64.0%; used with a seeded stored briefing
UNKNOWN = "synthetic-student-missing"

# Visibly synthetic acceptance-criteria values (FR-010). Feature-003 invents no US-14 criteria,
# so nothing here may read as approved criterion text.
PLACEHOLDER_CRITERION_A = "PLACEHOLDER_CRITERION_A"
PLACEHOLDER_CRITERION_B = "PLACEHOLDER_CRITERION_B"
PLACEHOLDER_FEEDBACK = "PLACEHOLDER_VALIDATION_FEEDBACK"

# Marker the prompt-aware provider emits only when the retry revision block reached it, so an
# attempt-2 pass is conditional on feedback having propagated rather than on call order.
REVISED_MARKER = "MOCK-DRAFT-REVISED"
INITIAL_MARKER = "MOCK-DRAFT-INITIAL"

# The revision block Feature-002's retry workflow appends. Used to detect a retry request.
RETRY_BLOCK_MARKER = "The previous attempt did not pass validation."


class VolumeSettings:
    """Minimal settings stand-in carrying only what ``VolumeBriefingStore`` reads.

    Mirrors the ``_Settings`` helper in the Feature-002 volume-store verifications rather than
    constructing a full ``Settings`` dataclass, which would require a dozen unrelated fields.
    """

    def __init__(self, briefing_volume: str = "/Volumes/main/advising/briefings") -> None:
        self.briefing_volume = briefing_volume


def draft(text: str, student_hash: str = FLAGGED) -> DraftBriefing:
    """A draft with visibly synthetic text, so a fixture briefing is never mistaken for a real one."""
    return DraftBriefing(student_deidentified_hash=student_hash, text=text)


def passed(validator_id: str = "f003-validator") -> ValidationOutcome:
    return ValidationOutcome(passed=True, validator_id=validator_id)


def failed(
    *,
    criteria: list[str] | None = None,
    feedback: str | None = None,
    validator_id: str = "f003-validator",
) -> ValidationOutcome:
    return ValidationOutcome(
        passed=False,
        failed_criteria=list(criteria or []),
        feedback=feedback,
        validator_id=validator_id,
    )


class PromptAwareGenerationProvider:
    """``GenerationProvider`` whose draft depends on the values present in the prompt it received.

    ``revise_when`` is the list of reported values — failed criteria and Validation Feedback —
    that must **all** appear in the composed prompt before this provider emits revised text. It
    keys on the reported values themselves, not on the wrapper wording, so an attempt-2 pass
    proves those specific values reached the generation boundary. Keying on a fixed header would
    instead pass even if the payload were dropped entirely.

    Every received context is recorded so identity-field preservation and exact payload
    relay can be asserted (FR-024, FR-025).
    """

    def __init__(
        self, *, revise_when: list[str] | None = None, blank_text: str | None = None
    ) -> None:
        self.contexts: list[BriefingGenerationContext] = []
        self.calls = 0
        self._blank_text = blank_text
        self._revise_when = list(revise_when or [])

    def generate(self, context: BriefingGenerationContext) -> DraftBriefing:
        self.calls += 1
        self.contexts.append(context)
        if self._blank_text is not None:
            # Exercises the generation boundary's rejection of content with no substance.
            return draft(self._blank_text, context.student_deidentified_hash)
        revised = bool(self._revise_when) and all(
            value in context.composed_prompt for value in self._revise_when
        )
        marker = REVISED_MARKER if revised else INITIAL_MARKER
        return draft(f"{marker} attempt={self.calls}", context.student_deidentified_hash)

    def retry_payload(self) -> str:
        """The text the retry appended to the original prompt, with the original removed.

        Isolating the delta lets a scenario assert on the relayed payload without asserting the
        wrapper wording, which belongs to US-12 and is not an acceptance criterion here.
        """
        assert len(self.contexts) >= 2, "no retry attempt was made"
        original = self.contexts[0].composed_prompt
        retried = self.contexts[1].composed_prompt
        assert retried.startswith(original), "the retry request did not preserve the original prompt"
        return retried[len(original) :]


class MarkerValidator:
    """``BriefingValidator`` that passes only a draft carrying ``REVISED_MARKER``.

    Paired with ``PromptAwareGenerationProvider`` this makes attempt-2 success conditional on
    propagation rather than on attempt number.
    """

    def __init__(
        self,
        *,
        criteria: list[str] | None = None,
        feedback: str | None = None,
        validator_id: str = "f003-marker-validator",
    ) -> None:
        self.calls = 0
        self._criteria = list(criteria or [PLACEHOLDER_CRITERION_A])
        self._feedback = feedback if feedback is not None else PLACEHOLDER_FEEDBACK
        self._validator_id = validator_id

    def validate(
        self, draft_briefing: DraftBriefing, context: BriefingGenerationContext
    ) -> ValidationOutcome:
        self.calls += 1
        if REVISED_MARKER in draft_briefing.text:
            return passed(self._validator_id)
        return failed(
            criteria=self._criteria, feedback=self._feedback, validator_id=self._validator_id
        )


class SeamCallRecorder:
    """Records the order in which the workflow engages its boundaries (FR-023).

    All wrappers append to one shared list, so relative order across boundaries is preserved —
    the property counters alone cannot express. Wrappers delegate unchanged and alter nothing.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def generation_calls(self) -> int:
        return self.calls.count("generate")

    def wrap_generation(self, provider: Any) -> Any:
        recorder = self

        class _Recorded:
            def generate(self, context: BriefingGenerationContext) -> DraftBriefing:
                recorder.calls.append("generate")
                return provider.generate(context)

        return _Recorded()

    def wrap_validator(self, validator: Any) -> Any:
        recorder = self

        class _Recorded:
            def validate(self, draft_briefing, context) -> ValidationOutcome:
                recorder.calls.append("validate")
                return validator.validate(draft_briefing, context)

        return _Recorded()

    def wrap_retry(self, workflow: Any) -> Any:
        recorder = self

        class _Recorded:
            def run(self, context, first_outcome):
                recorder.calls.append("retry")
                return workflow.run(context, first_outcome)

        return _Recorded()

    def wrap_store(self, store: Any) -> Any:
        recorder = self

        class _Recorded:
            def has_validated(self, student_hash: str) -> bool:
                recorder.calls.append("store.has_validated")
                return store.has_validated(student_hash)

            def get_latest_validated(self, student_hash: str) -> ValidatedBriefing | None:
                recorder.calls.append("store.get_latest_validated")
                return store.get_latest_validated(student_hash)

            def save_validated(self, briefing: ValidatedBriefing) -> None:
                recorder.calls.append("store.save_validated")
                store.save_validated(briefing)

        return _Recorded()


class CountingStore:
    """``BriefingStore`` wrapper counting validated-briefing writes (FR-028).

    Feature-002 has a file-local equivalent; that file is read-only under approved decision H3,
    so an equivalent is provided here rather than imported across.
    """

    def __init__(self, inner: Any | None = None, *, raise_on_save: bool = False) -> None:
        self.inner = inner if inner is not None else InMemoryBriefingStore()
        self.saves = 0
        self._raise_on_save = raise_on_save

    def has_validated(self, student_hash: str) -> bool:
        return self.inner.has_validated(student_hash)

    def get_latest_validated(self, student_hash: str) -> ValidatedBriefing | None:
        return self.inner.get_latest_validated(student_hash)

    def save_validated(self, briefing: ValidatedBriefing) -> None:
        if self._raise_on_save:
            raise BriefingStorageError("volume unavailable")
        self.saves += 1
        self.inner.save_validated(briefing)

    def seed(self, student_hash: str, text: str) -> ValidatedBriefing:
        """Place an existing validated briefing without counting it as a workflow write."""
        briefing = validated_briefing(student_hash, text)
        self.inner.save_validated(briefing)
        return briefing


def rendered_log_output(caplog: Any) -> str:
    """Every captured record as an operator would see it, **including exception information**.

    ``record.getMessage()`` alone omits the traceback a formatter renders from ``exc_info``, so a
    privacy check built on it can approve a record whose visible output contains briefing text.
    This renders each record through a formatter and appends any structured extras, so the check
    sees what is actually emitted (FR-034, SC-011).
    """
    import logging

    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    parts: list[str] = []
    for record in caplog.records:
        parts.append(formatter.format(record))
        # Structured fields are not rendered by the formatter but are emitted by structured
        # handlers, so they are inspected too.
        for key, value in vars(record).items():
            if key not in _STANDARD_LOG_RECORD_FIELDS:
                parts.append(f"{key}={value!r}")
    return "\n".join(parts)


_STANDARD_LOG_RECORD_FIELDS = frozenset(
    vars(__import__("logging").LogRecord("n", 0, "p", 0, "m", None, None)).keys()
) | {"message", "asctime"}


def validated_briefing(student_hash: str, text: str) -> ValidatedBriefing:
    from datetime import UTC, datetime

    return ValidatedBriefing(
        student_deidentified_hash=student_hash,
        text=text,
        source="generated",
        validator_id="interim-pass-through",
        generated_at=datetime.now(UTC),
        risk_percentage=64.0,
        at_risk_flag=True,
        prediction_threshold=0.5,
    )


def volume_store(fake: FakeFilesClient | None = None) -> tuple[VolumeBriefingStore, FakeFilesClient]:
    """The governed store backed by the existing in-memory files client (FR-031)."""
    fake = fake or FakeFilesClient()
    return VolumeBriefingStore(VolumeSettings(), files=fake), fake


def build_service(
    *,
    generation: Any,
    validation: Any,
    store: Any | None = None,
    repository: Any | None = None,
    recorder: SeamCallRecorder | None = None,
) -> StudentService:
    """Assemble a ``StudentService`` from a scenario's controlled outcomes.

    Uses existing public constructors only. The same generation and validation instances are
    passed to the service and to the retry workflow, matching ``main.build_service``, so a
    scripted sequence is consumed across both attempts exactly as the application consumes it.
    """
    store = store if store is not None else InMemoryBriefingStore()
    if recorder is not None:
        # Wrap before constructing the retry workflow, so the attempt-2 calls it makes are
        # recorded too - the workflow must receive the same instances the service does.
        generation = recorder.wrap_generation(generation)
        validation = recorder.wrap_validator(validation)
        store = recorder.wrap_store(store)
    retry = SingleRetryWorkflow(generation_provider=generation, validator=validation)
    if recorder is not None:
        retry = recorder.wrap_retry(retry)
    return StudentService(
        repository=repository or MockStudentRepository(),
        generation_provider=generation,
        instructions=InterimInstructions(),
        validator=validation,
        retry_workflow=retry,
        store=store,
    )


def build_rest_client(service: StudentService) -> Any:
    from fastapi.testclient import TestClient

    return TestClient(create_api(service))


def build_mcp_server(service: StudentService) -> Any:
    from student_attrition_risk.mcp_server import create_mcp_server

    return create_mcp_server(service)
