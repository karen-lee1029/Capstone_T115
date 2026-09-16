"""Feature-003 (US-18) User Story 2 — the exceptional retry path.

Feature-002 already verifies the retry **outcome** matrix comprehensively; under FR-005 that is
complete and recorded as tracked re-verification, not repeated here. This file covers the
properties outcome testing cannot show:

- FR-023: the order in which the workflow engages its boundaries, not only how many times.
- FR-024: reported criteria and feedback reach the second attempt.
- FR-025: the retry request is unchanged when nothing was reported, and identity fields survive.
- FR-026: generation is attempted at most twice, across the whole matrix.
- FR-027: the retry path stores nothing itself; a retry result is written exactly once.

Offline: controlled generation and validation outcomes, no network or workspace.
"""

import pytest

from student_attrition_risk.models import GenerationFailed
from student_attrition_risk.retry_workflow import SingleRetryWorkflow
from student_attrition_risk.student_service import BriefingNotProducedError
from workflow_doubles import (
    FLAGGED,
    PLACEHOLDER_CRITERION_A,
    PLACEHOLDER_CRITERION_B,
    PLACEHOLDER_FEEDBACK,
    REVISED_MARKER,
    CountingStore,
    MarkerValidator,
    PromptAwareGenerationProvider,
    ScriptedGenerationProvider,
    ScriptedValidator,
    SeamCallRecorder,
    build_service,
    draft,
    failed,
    passed,
)

# --- FR-023: boundary engagement order --------------------------------------


def test_first_attempt_success_engages_boundaries_in_specified_order():
    """The happy path follows the order in Feature-001 contracts/internal-seams.md.

    Asserts the sequence, which no existing verification does — the Feature-001 happy-path
    scenario asserts counts and outcomes only.
    """
    recorder = SeamCallRecorder()
    service = build_service(
        generation=ScriptedGenerationProvider(draft("a briefing")),
        validation=ScriptedValidator(passed()),
        store=CountingStore(),
        recorder=recorder,
    )

    service.request_briefing(FLAGGED)

    assert recorder.calls == [
        "store.has_validated",  # get-or-create check precedes generation
        "generate",
        "validate",
        "store.save_validated",
    ]


def test_retry_path_engages_boundaries_in_specified_order():
    """A validation failure routes to the retry seam before the second generation attempt."""
    recorder = SeamCallRecorder()
    service = build_service(
        generation=ScriptedGenerationProvider(draft("first"), draft("second")),
        validation=ScriptedValidator(
            failed(criteria=[PLACEHOLDER_CRITERION_A], feedback=PLACEHOLDER_FEEDBACK), passed()
        ),
        store=CountingStore(),
        recorder=recorder,
    )

    service.request_briefing(FLAGGED)

    assert recorder.calls == [
        "store.has_validated",
        "generate",  # attempt 1
        "validate",  # fails
        "retry",  # handed to the retry seam
        "generate",  # attempt 2
        "validate",  # passes
        "store.save_validated",  # persisted by the service, after the retry returned
    ]
    assert recorder.calls.index("retry") < recorder.calls.index("store.save_validated")


# --- FR-024: feedback propagation -------------------------------------------


def test_reported_criteria_and_feedback_reach_the_second_attempt():
    """Exactly what validation reported is carried into the attempt-2 request, verbatim."""
    gen = PromptAwareGenerationProvider()
    val = MarkerValidator(
        criteria=[PLACEHOLDER_CRITERION_A, PLACEHOLDER_CRITERION_B], feedback=PLACEHOLDER_FEEDBACK
    )
    service = build_service(generation=gen, validation=val)

    service.request_briefing(FLAGGED)

    assert gen.calls == 2
    second_prompt = gen.contexts[1].composed_prompt
    assert PLACEHOLDER_CRITERION_A in second_prompt
    assert PLACEHOLDER_CRITERION_B in second_prompt
    assert PLACEHOLDER_FEEDBACK in second_prompt


def test_second_attempt_succeeds_only_when_feedback_propagated():
    """Stronger than a substring check: the pass is *caused* by propagation.

    The provider emits the revised marker only when the retry block reached it, and the validator
    passes only a draft carrying that marker. A second attempt that succeeds therefore proves the
    feedback travelled, not merely that text was appended somewhere.
    """
    gen = PromptAwareGenerationProvider()
    val = MarkerValidator()
    service = build_service(generation=gen, validation=val)

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert REVISED_MARKER in briefing.text
    assert briefing.validator_id == "f003-marker-validator"


# --- FR-025: nothing fabricated ----------------------------------------------


def test_retry_request_unchanged_when_nothing_was_reported():
    """A validation failure reporting neither criteria nor feedback changes nothing (FR-025)."""
    gen = PromptAwareGenerationProvider()
    val = ScriptedValidator(failed(criteria=[], feedback=None), failed(criteria=[], feedback=None))
    service = build_service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert gen.calls == 2
    assert gen.contexts[1].composed_prompt == gen.contexts[0].composed_prompt


def test_retry_request_unchanged_for_a_generation_failure():
    """A generation-failure retry has no validation feedback to carry, so the prompt is reused."""
    gen = PromptAwareGenerationProvider()
    workflow = SingleRetryWorkflow(generation_provider=gen, validator=ScriptedValidator(passed()))
    service = build_service(generation=gen, validation=ScriptedValidator(passed()))
    context = service._build_context(FLAGGED, service.repository.get_prediction(FLAGGED))

    workflow.run(context, GenerationFailed())

    assert gen.calls == 1
    assert gen.contexts[0].composed_prompt == context.composed_prompt


def test_identity_fields_are_preserved_across_the_retry_request():
    """Hash, prediction, features and instructions provenance survive the retry (FR-025)."""
    gen = PromptAwareGenerationProvider()
    val = MarkerValidator()
    service = build_service(generation=gen, validation=val)

    service.request_briefing(FLAGGED)

    first, second = gen.contexts
    assert second.student_deidentified_hash == first.student_deidentified_hash
    assert second.prediction == first.prediction
    assert second.features == first.features
    assert second.instructions_id == first.instructions_id


# --- FR-026: bounded attempts -------------------------------------------------


@pytest.mark.parametrize(
    ("label", "first", "second"),
    [
        ("validation-then-validation", failed(), failed()),
        ("validation-then-pass", failed(), passed()),
    ],
    ids=["two-validation-failures", "validation-then-pass"],
)
def test_generation_is_attempted_at_most_twice_across_the_matrix(label, first, second):
    """No path reaches a third generation attempt (FR-026, SC-009).

    The scripted provider raises if called more than scripted, so a third attempt would surface
    as an error rather than pass silently.
    """
    recorder = SeamCallRecorder()
    service = build_service(
        generation=ScriptedGenerationProvider(draft("first"), draft("second")),
        validation=ScriptedValidator(first, second),
        recorder=recorder,
    )

    try:
        service.request_briefing(FLAGGED)
    except BriefingNotProducedError:
        pass

    assert recorder.generation_calls == 2, label


def test_generation_failure_path_also_stops_at_two_attempts():
    recorder = SeamCallRecorder()
    service = build_service(
        generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
        validation=ScriptedValidator(),
        recorder=recorder,
    )

    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)

    assert exc.value.category == "generation"
    assert recorder.generation_calls == 2
    assert "validate" not in recorder.calls, "validation is never reached without a draft"


# --- FR-027: the retry path persists nothing ---------------------------------


def test_retry_result_is_stored_exactly_once_and_not_by_the_workflow():
    """The workflow returns an outcome; StudentService writes it, exactly once (FR-027)."""
    gen = PromptAwareGenerationProvider()
    val = MarkerValidator()
    store = CountingStore()
    service = build_service(generation=gen, validation=val, store=store)

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert store.saves == 1
    assert not hasattr(service.retry_workflow, "store")
    assert not hasattr(service.retry_workflow, "_store")
