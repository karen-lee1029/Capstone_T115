"""Feature-003 (US-18) User Story 2 — the exceptional retry path.

Feature-002 already verifies the retry **outcome** matrix, the generation-failure prompt being
unchanged, the store-once property, and the two-attempt call counts. Under FR-005 those are
complete and cited individually in ``traceability.md`` § 2, not repeated here.

What remains, and is covered below:

- FR-023: the order in which the workflow engages its boundaries. No existing verification
  asserts a sequence.
- FR-024: the reported criteria and feedback reach the second attempt **exactly**, with nothing
  added. Substring presence alone cannot reject a fabricated addition, so the relayed payload is
  compared as a set.
- FR-025: identity fields survive the retry request, and a validation failure reporting nothing
  changes nothing.

Offline: controlled generation and validation outcomes, no network or workspace.
"""

import pytest

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

# Every synthetic payload value this module can relay. The exact-relay assertions compare what
# appears in the retry request against what was reported, drawn from this set, so a fabricated
# addition is rejected rather than merely unnoticed.
ALL_SYNTHETIC_VALUES = (
    PLACEHOLDER_CRITERION_A,
    PLACEHOLDER_CRITERION_B,
    PLACEHOLDER_FEEDBACK,
    "PLACEHOLDER_CRITERION_INVENTED",
    "PLACEHOLDER_FEEDBACK_INVENTED",
)


def _relayed_values(payload: str) -> set[str]:
    """Which synthetic values appear in the text the retry appended."""
    return {value for value in ALL_SYNTHETIC_VALUES if value in payload}


# --- FR-023: boundary engagement order --------------------------------------


def test_first_attempt_success_engages_boundaries_in_specified_order():
    """The happy path follows the order in Feature-001 contracts/internal-seams.md.

    Asserts the sequence. Existing verifications assert counts and outcomes only.
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


def test_validation_is_never_engaged_when_generation_produced_no_draft():
    """With no draft there is nothing to validate, on either attempt (FR-023).

    The call counts on this path are already asserted by Feature-002; the sequence is not.
    """
    recorder = SeamCallRecorder()
    service = build_service(
        generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
        validation=ScriptedValidator(),
        recorder=recorder,
    )

    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)

    assert exc.value.category == "generation"
    assert recorder.calls == [
        "store.has_validated",
        "generate",
        "retry",
        "generate",
    ], "validation must never appear on a path where no draft was produced"


# --- FR-024: the payload is relayed exactly, with nothing added --------------


@pytest.mark.parametrize(
    ("label", "criteria", "feedback", "expected"),
    [
        (
            "criteria-and-feedback",
            [PLACEHOLDER_CRITERION_A, PLACEHOLDER_CRITERION_B],
            PLACEHOLDER_FEEDBACK,
            {PLACEHOLDER_CRITERION_A, PLACEHOLDER_CRITERION_B, PLACEHOLDER_FEEDBACK},
        ),
        ("criteria-only", [PLACEHOLDER_CRITERION_A], None, {PLACEHOLDER_CRITERION_A}),
        ("feedback-only", [], PLACEHOLDER_FEEDBACK, {PLACEHOLDER_FEEDBACK}),
    ],
    ids=["criteria-and-feedback", "criteria-only", "feedback-only"],
)
def test_retry_relays_exactly_what_validation_reported(label, criteria, feedback, expected):
    """Exactly the reported values reach attempt 2 — no omission, no fabrication (FR-024).

    Set equality is what makes this reject an invented criterion. A substring check confirms only
    that the reported values are present, and would accept additional fabricated ones alongside.
    """
    gen = PromptAwareGenerationProvider()
    val = ScriptedValidator(
        failed(criteria=criteria, feedback=feedback), failed(criteria=criteria, feedback=feedback)
    )
    service = build_service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert gen.calls == 2, label
    relayed = _relayed_values(gen.retry_payload())
    assert relayed == expected, (
        f"{label}: retry relayed {sorted(relayed)}, validation reported {sorted(expected)}"
    )


def test_second_attempt_succeeds_only_when_the_reported_values_propagated():
    """The pass is caused by the reported values arriving, not by the attempt number (FR-024).

    The provider emits revised text only when **every reported value** is present in the prompt it
    received, and the validator passes only revised text. Keying on the wrapper header instead
    would let this pass even if the payload were dropped.
    """
    gen = PromptAwareGenerationProvider(
        revise_when=[PLACEHOLDER_CRITERION_A, PLACEHOLDER_FEEDBACK]
    )
    val = MarkerValidator(criteria=[PLACEHOLDER_CRITERION_A], feedback=PLACEHOLDER_FEEDBACK)
    service = build_service(generation=gen, validation=val)

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert REVISED_MARKER in briefing.text
    assert briefing.validator_id == "f003-marker-validator"


def test_retry_does_not_succeed_when_the_reported_values_are_absent():
    """The converse: if the reported values do not arrive, the second attempt does not pass.

    Without this, the preceding scenario could pass for reasons unrelated to propagation.
    """
    gen = PromptAwareGenerationProvider(revise_when=["PLACEHOLDER_VALUE_NEVER_REPORTED"])
    val = MarkerValidator(criteria=[PLACEHOLDER_CRITERION_A], feedback=PLACEHOLDER_FEEDBACK)
    service = build_service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)

    assert exc.value.category == "validation"
    assert gen.calls == 2


# --- FR-025: nothing fabricated when nothing was reported --------------------


def test_retry_request_unchanged_when_nothing_was_reported():
    """A validation failure reporting neither criteria nor feedback changes nothing (FR-025)."""
    gen = PromptAwareGenerationProvider()
    val = ScriptedValidator(failed(criteria=[], feedback=None), failed(criteria=[], feedback=None))
    service = build_service(generation=gen, validation=val)

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert gen.calls == 2
    assert gen.contexts[1].composed_prompt == gen.contexts[0].composed_prompt
    assert _relayed_values(gen.retry_payload()) == set()


def test_identity_fields_are_preserved_across_the_retry_request():
    """Hash, prediction, features and instructions provenance survive the retry (FR-025)."""
    gen = PromptAwareGenerationProvider(
        revise_when=[PLACEHOLDER_CRITERION_A, PLACEHOLDER_FEEDBACK]
    )
    val = MarkerValidator(criteria=[PLACEHOLDER_CRITERION_A], feedback=PLACEHOLDER_FEEDBACK)
    service = build_service(generation=gen, validation=val)

    service.request_briefing(FLAGGED)

    first, second = gen.contexts
    assert second.student_deidentified_hash == first.student_deidentified_hash
    assert second.prediction == first.prediction
    assert second.features == first.features
    assert second.instructions_id == first.instructions_id
