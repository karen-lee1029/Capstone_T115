"""Feature-003 (US-18) User Story 3 — storage decisions.

Feature-001 and Feature-002 verify storage *outcomes*; under FR-005 those are complete. This file
covers what they do not assert:

- FR-028: how many times a validated briefing is written, for every outcome.
- FR-029: nothing unvalidated is ever stored or surfaced as validated.
- FR-030: a previously stored briefing survives every failing outcome.
- FR-031: the six storage-decision outcomes behave identically against governed storage.

Per the approved clarification, FR-031 re-runs **only** those six outcomes — outcomes that
neither read nor write storage cannot vary by store and are deliberately not re-run.

Offline: controlled generation and validation outcomes, and the existing in-memory files client.
"""

import pytest

from student_attrition_risk.config import ConfigurationError
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
    UNKNOWN,
    CountingStore,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_service,
    draft,
    failed,
    passed,
    volume_store,
)

# --- FR-028: write counts -----------------------------------------------------


def test_write_count_is_one_for_every_successful_outcome():
    """A briefing validated on either attempt is written exactly once (FR-028, SC-007)."""
    # Attempt 1.
    store = CountingStore()
    build_service(
        generation=ScriptedGenerationProvider(draft("a briefing")),
        validation=ScriptedValidator(passed()),
        store=store,
    ).request_briefing(FLAGGED)
    assert store.saves == 1

    # Attempt 2.
    store = CountingStore()
    build_service(
        generation=ScriptedGenerationProvider(draft("first"), draft("second")),
        validation=ScriptedValidator(failed(), passed()),
        store=store,
    ).request_briefing(FLAGGED)
    assert store.saves == 1

    # Explicit regeneration over an existing briefing.
    store = CountingStore()
    store.seed(HAS_EXISTING, "prior")
    build_service(
        generation=ScriptedGenerationProvider(draft("fresh", HAS_EXISTING)),
        validation=ScriptedValidator(passed()),
        store=store,
    ).request_briefing(HAS_EXISTING, regenerate=True)
    assert store.saves == 1


def _non_successful_cases():
    def terminal_generation():
        store = CountingStore()
        service = build_service(
            generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
            validation=ScriptedValidator(),
            store=store,
        )
        return service, store, FLAGGED, False, BriefingNotProducedError

    def terminal_validation():
        store = CountingStore()
        service = build_service(
            generation=ScriptedGenerationProvider(draft("first"), draft("second")),
            validation=ScriptedValidator(failed(), failed()),
            store=store,
        )
        return service, store, FLAGGED, False, BriefingNotProducedError

    def configuration():
        store = CountingStore()
        service = build_service(
            generation=ScriptedGenerationProvider(ConfigurationError("not configured")),
            validation=ScriptedValidator(),
            store=store,
        )
        return service, store, FLAGGED, False, ConfigurationError

    def not_at_risk():
        store = CountingStore()
        service = build_service(
            generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=store
        )
        return service, store, NOT_FLAGGED, False, StudentNotAtRiskError

    def unknown():
        store = CountingStore()
        service = build_service(
            generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=store
        )
        return service, store, UNKNOWN, False, StudentNotFoundError

    return [
        ("terminal-generation", terminal_generation),
        ("terminal-validation", terminal_validation),
        ("configuration-failure", configuration),
        ("not-at-risk", not_at_risk),
        ("unknown-student", unknown),
    ]


@pytest.mark.parametrize(
    ("label", "factory"), _non_successful_cases(), ids=[c[0] for c in _non_successful_cases()]
)
def test_write_count_is_zero_for_every_non_successful_outcome(label, factory):
    """No failing or refused outcome writes anything (FR-028, SC-007)."""
    service, store, student_hash, regenerate, error = factory()

    with pytest.raises(error):
        service.request_briefing(student_hash, regenerate=regenerate)

    assert store.saves == 0, label
    assert store.has_validated(student_hash) is False, label


def test_returning_an_existing_briefing_writes_nothing():
    """The get-or-create path re-reads; it must not re-write (FR-028)."""
    store = CountingStore()
    store.seed(HAS_EXISTING, "prior")
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=store
    )

    briefing = service.request_briefing(HAS_EXISTING)

    assert briefing.source == "stored"
    assert store.saves == 0


# --- FR-029: only validated briefings are stored ------------------------------


def test_nothing_unvalidated_is_stored_or_surfaced_as_validated():
    """A draft that never passed validation reaches neither the caller nor the store (FR-029)."""
    store = CountingStore()
    service = build_service(
        generation=ScriptedGenerationProvider(draft("rejected one"), draft("rejected two")),
        validation=ScriptedValidator(failed(), failed()),
        store=store,
    )

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert store.saves == 0
    assert store.get_latest_validated(FLAGGED) is None
    assert service.get_stored_briefing(FLAGGED) is None


# --- FR-030: a prior briefing survives every failure --------------------------


@pytest.mark.parametrize(
    ("label", "generation", "validation", "error"),
    [
        (
            "terminal-generation",
            lambda: ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
            lambda: ScriptedValidator(),
            BriefingNotProducedError,
        ),
        (
            "terminal-validation",
            lambda: ScriptedGenerationProvider(draft("a", HAS_EXISTING), draft("b", HAS_EXISTING)),
            lambda: ScriptedValidator(failed(), failed()),
            BriefingNotProducedError,
        ),
        (
            "configuration-failure",
            lambda: ScriptedGenerationProvider(ConfigurationError("not configured")),
            lambda: ScriptedValidator(),
            ConfigurationError,
        ),
    ],
    ids=["terminal-generation", "terminal-validation", "configuration-failure"],
)
def test_previously_stored_briefing_survives_every_failing_outcome(
    label, generation, validation, error
):
    """A failed regeneration never destroys what the advisor already had (FR-030, SC-008)."""
    store = CountingStore()
    store.seed(HAS_EXISTING, "keep me")
    service = build_service(generation=generation(), validation=validation(), store=store)

    with pytest.raises(error):
        service.request_briefing(HAS_EXISTING, regenerate=True)

    assert store.saves == 0, label
    assert store.get_latest_validated(HAS_EXISTING).text == "keep me", label
    assert service.get_stored_briefing(HAS_EXISTING).text == "keep me", label


def test_storage_failure_surfaces_and_leaves_the_prior_briefing_intact():
    """The write failed, so the request is not reported successful and the prior stands (FR-030)."""
    inner = CountingStore()
    inner.seed(HAS_EXISTING, "keep me")
    failing = CountingStore(inner=inner, raise_on_save=True)
    service = build_service(
        generation=ScriptedGenerationProvider(draft("fresh", HAS_EXISTING)),
        validation=ScriptedValidator(passed()),
        store=failing,
    )

    with pytest.raises(BriefingStorageError):
        service.request_briefing(HAS_EXISTING, regenerate=True)

    assert failing.saves == 0
    assert inner.get_latest_validated(HAS_EXISTING).text == "keep me"


# --- FR-031: governed-storage parity, the six storage-decision outcomes -------


def _storage_decision_outcomes():
    """The six outcomes of User Story 3, as (label, runner) pairs.

    Each runner takes a store and returns the observed write count plus what retrieval surfaces.
    Only these six are re-run against governed storage: an outcome that never reads or writes
    storage cannot vary by store (approved clarification).
    """

    def validated_on_attempt_1(store):
        build_service(
            generation=ScriptedGenerationProvider(draft("a briefing")),
            validation=ScriptedValidator(passed()),
            store=store,
        ).request_briefing(FLAGGED)
        return store.saves, store.get_latest_validated(FLAGGED) is not None

    def validated_on_attempt_2(store):
        build_service(
            generation=ScriptedGenerationProvider(draft("first"), draft("second")),
            validation=ScriptedValidator(failed(), passed()),
            store=store,
        ).request_briefing(FLAGGED)
        return store.saves, store.get_latest_validated(FLAGGED) is not None

    def terminal_failure_writes_nothing(store):
        service = build_service(
            generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
            validation=ScriptedValidator(),
            store=store,
        )
        with pytest.raises(BriefingNotProducedError):
            service.request_briefing(FLAGGED)
        return store.saves, store.get_latest_validated(FLAGGED) is not None

    def existing_returned_writes_nothing(store):
        store.seed(HAS_EXISTING, "prior")
        service = build_service(
            generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=store
        )
        briefing = service.request_briefing(HAS_EXISTING)
        return store.saves, briefing.source == "stored"

    def prior_survives_a_failed_regeneration(store):
        store.seed(HAS_EXISTING, "keep me")
        service = build_service(
            generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
            validation=ScriptedValidator(),
            store=store,
        )
        with pytest.raises(BriefingNotProducedError):
            service.request_briefing(HAS_EXISTING, regenerate=True)
        return store.saves, store.get_latest_validated(HAS_EXISTING).text == "keep me"

    def unvalidated_is_never_stored(store):
        service = build_service(
            generation=ScriptedGenerationProvider(draft("a"), draft("b")),
            validation=ScriptedValidator(failed(), failed()),
            store=store,
        )
        with pytest.raises(BriefingNotProducedError):
            service.request_briefing(FLAGGED)
        return store.saves, store.get_latest_validated(FLAGGED) is None

    return [
        ("validated-on-attempt-1", validated_on_attempt_1, (1, True)),
        ("validated-on-attempt-2", validated_on_attempt_2, (1, True)),
        ("terminal-failure-writes-nothing", terminal_failure_writes_nothing, (0, False)),
        ("existing-returned-writes-nothing", existing_returned_writes_nothing, (0, True)),
        ("prior-survives-failed-regeneration", prior_survives_a_failed_regeneration, (0, True)),
        ("unvalidated-is-never-stored", unvalidated_is_never_stored, (0, True)),
    ]


@pytest.mark.parametrize(
    ("label", "runner", "expected"),
    _storage_decision_outcomes(),
    ids=[c[0] for c in _storage_decision_outcomes()],
)
def test_storage_decision_outcomes_behave_identically_on_governed_storage(label, runner, expected):
    """Each of the six behaves the same on the default store and on governed storage (FR-031).

    Governed storage is the real ``VolumeBriefingStore`` backed by the existing in-memory files
    client, so this exercises the store's own read and write paths without a workspace.
    """
    in_memory = CountingStore()
    governed, _fake = volume_store()
    on_volume = CountingStore(inner=governed)

    assert runner(in_memory) == expected, f"{label}: default store"
    assert runner(on_volume) == expected, f"{label}: governed store"
