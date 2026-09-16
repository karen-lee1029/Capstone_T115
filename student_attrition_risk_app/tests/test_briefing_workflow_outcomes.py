"""Feature-003 (US-18) User Story 1 — briefing outcome coverage.

Feature-001 and Feature-002 already verify most outcomes at the service boundary; under FR-005
those are complete and recorded as tracked re-verification in
``specs/003-briefing-workflow-testing/traceability.md``, not repeated here.

This file covers the two gaps that inventory found, plus the matrix-wide guarantee no existing
verification asserts:

- FR-016: a configuration failure is surfaced unchanged and never routed to retry.
- FR-019: an unknown student attempts no generation.
- FR-022: every request reaches exactly one explicit outcome.

Offline: controlled generation and validation outcomes, no network or workspace.
"""

import pytest

from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.models import ValidatedBriefing
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotAtRiskError,
    StudentNotFoundError,
)
from workflow_doubles import (
    FLAGGED,
    HAS_EXISTING,
    NOT_FLAGGED,
    PLACEHOLDER_CRITERION_A,
    PLACEHOLDER_FEEDBACK,
    UNKNOWN,
    CountingStore,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_service,
    draft,
    failed,
    passed,
)


class _ExplodingProvider:
    """Fails the verification if generation is reached at all."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, context):
        self.calls += 1
        raise AssertionError("generation must not be attempted for this outcome")


# --- FR-016: configuration failure ------------------------------------------


def test_configuration_failure_is_surfaced_unchanged_and_never_retried():
    """A configuration error is an operator problem, not a briefing failure.

    It must reach the caller as itself rather than as a terminal briefing failure, and must not
    consume the single retry (FR-016).
    """
    gen = ScriptedGenerationProvider(ConfigurationError("Briefing generation is not configured"))
    val = ScriptedValidator()
    store = CountingStore()
    service = build_service(generation=gen, validation=val, store=store)

    with pytest.raises(ConfigurationError):
        service.request_briefing(FLAGGED)

    assert gen.calls == 1, "the retry must not make a second attempt after a configuration error"
    assert val.calls == 0, "validation is not reached when no draft exists"
    assert store.saves == 0
    assert store.has_validated(FLAGGED) is False


# --- FR-019: unknown student -------------------------------------------------


def test_unknown_student_attempts_no_generation():
    """An unknown hash is refused before any boundary is engaged (FR-019)."""
    gen = _ExplodingProvider()
    val = ScriptedValidator()
    store = CountingStore()
    service = build_service(generation=gen, validation=val, store=store)

    with pytest.raises(StudentNotFoundError):
        service.request_briefing(UNKNOWN)

    assert gen.calls == 0
    assert val.calls == 0
    assert store.saves == 0


# --- FR-022: exactly one explicit outcome, across the whole matrix -----------


def _outcome_of(service, student_hash: str, *, regenerate: bool = False) -> str:
    """Reduce a request to the single explicit outcome it reached.

    Returns a validated-briefing marker or the name of the explicit failure. Any other end state
    — a returned ``None``, a briefing that never passed validation, an unexpected exception type —
    is reported as such so FR-022 can fail on it.
    """
    try:
        result = service.request_briefing(student_hash, regenerate=regenerate)
    except StudentNotFoundError:
        return "explicit-failure:not-found"
    except StudentNotAtRiskError:
        return "explicit-failure:not-at-risk"
    except BriefingNotProducedError as exc:
        return f"explicit-failure:terminal-{exc.category}"
    except BriefingStorageError:
        return "explicit-failure:storage"
    except ConfigurationError:
        return "explicit-failure:configuration"
    except Exception as exc:  # noqa: BLE001 - an unexpected type is itself the finding
        return f"UNEXPECTED-EXCEPTION:{type(exc).__name__}"
    if result is None:
        return "NO-RESULT"
    if not isinstance(result, ValidatedBriefing) or not result.validated:
        return "UNVALIDATED-RESULT"
    return "validated-briefing"


def _matrix():
    """Every outcome a briefing request can reach, as (label, service factory, hash, regenerate)."""

    def success():
        return build_service(
            generation=ScriptedGenerationProvider(draft("a briefing")),
            validation=ScriptedValidator(passed()),
        )

    def retry_success():
        gen = ScriptedGenerationProvider(draft("first"), draft("second"))
        val = ScriptedValidator(
            failed(criteria=[PLACEHOLDER_CRITERION_A], feedback=PLACEHOLDER_FEEDBACK), passed()
        )
        return build_service(generation=gen, validation=val)

    def terminal_generation():
        return build_service(
            generation=ScriptedGenerationProvider(
                RuntimeError("provider down"), RuntimeError("provider down")
            ),
            validation=ScriptedValidator(),
        )

    def terminal_validation():
        return build_service(
            generation=ScriptedGenerationProvider(draft("first"), draft("second")),
            validation=ScriptedValidator(failed(), failed()),
        )

    def configuration():
        return build_service(
            generation=ScriptedGenerationProvider(ConfigurationError("not configured")),
            validation=ScriptedValidator(),
        )

    def storage_failure():
        return build_service(
            generation=ScriptedGenerationProvider(draft("a briefing")),
            validation=ScriptedValidator(passed()),
            store=CountingStore(raise_on_save=True),
        )

    def existing():
        store = CountingStore()
        store.seed(HAS_EXISTING, "an existing briefing")
        return build_service(
            generation=_ExplodingProvider(), validation=ScriptedValidator(), store=store
        )

    def regenerate_success():
        store = CountingStore()
        store.seed(HAS_EXISTING, "an existing briefing")
        return build_service(
            generation=ScriptedGenerationProvider(draft("fresh", HAS_EXISTING)),
            validation=ScriptedValidator(passed()),
            store=store,
        )

    def regenerate_failure():
        store = CountingStore()
        store.seed(HAS_EXISTING, "an existing briefing")
        return build_service(
            generation=ScriptedGenerationProvider(
                RuntimeError("down"), RuntimeError("down")
            ),
            validation=ScriptedValidator(),
            store=store,
        )

    def not_at_risk():
        return build_service(
            generation=_ExplodingProvider(), validation=ScriptedValidator()
        )

    def unknown():
        return build_service(
            generation=_ExplodingProvider(), validation=ScriptedValidator()
        )

    return [
        ("attempt-1 success", success, FLAGGED, False, "validated-briefing"),
        ("retry success", retry_success, FLAGGED, False, "validated-briefing"),
        ("terminal generation", terminal_generation, FLAGGED, False, "explicit-failure:terminal-generation"),
        ("terminal validation", terminal_validation, FLAGGED, False, "explicit-failure:terminal-validation"),
        ("configuration failure", configuration, FLAGGED, False, "explicit-failure:configuration"),
        ("storage failure", storage_failure, FLAGGED, False, "explicit-failure:storage"),
        ("existing returned", existing, HAS_EXISTING, False, "validated-briefing"),
        ("regenerate success", regenerate_success, HAS_EXISTING, True, "validated-briefing"),
        (
            "regenerate failure",
            regenerate_failure,
            HAS_EXISTING,
            True,
            "explicit-failure:terminal-generation",
        ),
        ("not at risk", not_at_risk, NOT_FLAGGED, False, "explicit-failure:not-at-risk"),
        ("unknown student", unknown, UNKNOWN, False, "explicit-failure:not-found"),
    ]


@pytest.mark.parametrize(
    ("label", "factory", "student_hash", "regenerate", "expected"),
    [pytest.param(*row, id=row[0].replace(" ", "-")) for row in _matrix()],
)
def test_every_outcome_reaches_exactly_one_explicit_result(
    label, factory, student_hash, regenerate, expected
):
    """FR-022 / SC-002: no request ends with an absent or ambiguous result.

    Asserted as a matrix rather than as isolated cases, so a path that silently returns ``None``
    or an unvalidated briefing is caught wherever it appears.
    """
    outcome = _outcome_of(factory(), student_hash, regenerate=regenerate)
    assert outcome == expected, f"{label}: expected {expected}, reached {outcome}"
