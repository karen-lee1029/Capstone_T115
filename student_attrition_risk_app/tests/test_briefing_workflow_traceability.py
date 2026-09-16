"""Feature-003 (US-18) User Story 4 — blank content, the timing criterion, and the record.

Three concerns:

- FR-035: blank generation content is a generation failure and is never stored. This is an
  **ordinary** verification. It began as a strict expected-fail recording a defect; the defect was
  resolved before Feature-003 reached implementation, so no expectation marker is used and these
  scenarios are expected to pass.
- FR-037: Feature-001 SC-006's time budget for non-generation requests, measured under the
  conditions that criterion names — the mock repository and the in-memory store.
- FR-040: every verification the traceability record cites still resolves, so the record cannot
  silently drift the way Feature-001's equivalent table did.

Offline: controlled generation and validation outcomes, no network or workspace.
"""

import ast
import pathlib
import re
import time

import pytest

from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    StudentNotAtRiskError,
    StudentNotFoundError,
)
from workflow_doubles import (
    FLAGGED,
    HAS_EXISTING,
    NOT_FLAGGED,
    UNKNOWN,
    CountingStore,
    PromptAwareGenerationProvider,
    ScriptedValidator,
    build_service,
    passed,
)

TESTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
TRACEABILITY = REPO_ROOT / "specs" / "003-briefing-workflow-testing" / "traceability.md"

# Feature-001 SC-006: non-generation requests complete in under one second, measured against the
# mock repository and the in-memory persistence seam.
SC006_BUDGET_SECONDS = 1.0


# --- FR-035: blank generation content ----------------------------------------


@pytest.mark.parametrize(
    ("label", "blank"),
    [("empty", ""), ("spaces", "   "), ("newline-and-tab", "\n\t ")],
    ids=["empty", "spaces", "newline-and-tab"],
)
def test_blank_generation_content_is_a_generation_failure(label, blank):
    """Content with no substance is a failure to produce a draft, not a draft (FR-035).

    Feature-002 specifies this treatment; the generation boundary now enforces it, so the retry
    runs and the terminal category is ``generation`` rather than ``validation``.
    """
    service = build_service(
        generation=PromptAwareGenerationProvider(blank_text=blank),
        validation=ScriptedValidator(),
    )

    with pytest.raises(BriefingNotProducedError) as exc:
        service.request_briefing(FLAGGED)

    assert exc.value.category == "generation", label


@pytest.mark.parametrize(
    ("label", "blank"),
    [("empty", ""), ("spaces", "   ")],
    ids=["empty", "spaces"],
)
def test_blank_generation_content_is_never_stored(label, blank):
    """Nothing is written, and any prior briefing survives (FR-035, FR-030)."""
    store = CountingStore()
    store.seed(HAS_EXISTING, "keep me")
    service = build_service(
        generation=PromptAwareGenerationProvider(blank_text=blank),
        validation=ScriptedValidator(),
        store=store,
    )

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(HAS_EXISTING, regenerate=True)

    assert store.saves == 0, label
    assert store.get_latest_validated(HAS_EXISTING).text == "keep me", label


def test_blank_content_never_reaches_validation():
    """The rejection happens at generation, so validation is never asked about it (FR-035)."""
    validator = ScriptedValidator()
    service = build_service(
        generation=PromptAwareGenerationProvider(blank_text=""), validation=validator
    )

    with pytest.raises(BriefingNotProducedError):
        service.request_briefing(FLAGGED)

    assert validator.calls == 0


# --- FR-037: Feature-001 SC-006 time budget ----------------------------------


def test_non_generation_requests_complete_within_the_time_budget():
    """Requests that do not invoke generation complete within SC-006's budget (FR-037).

    Measured under the conditions SC-006 names: the mock repository and the in-memory store. These
    paths do only in-memory work, so the margin against a one-second budget is several orders of
    magnitude and this is not a load-sensitive verification.
    """
    store = CountingStore()
    store.seed(HAS_EXISTING, "prior")
    service = build_service(
        generation=PromptAwareGenerationProvider(),
        validation=ScriptedValidator(passed()),
        store=store,
    )

    cases = [
        ("unknown-student", UNKNOWN, StudentNotFoundError),
        ("not-flagged", NOT_FLAGGED, StudentNotAtRiskError),
        ("returns-existing", HAS_EXISTING, None),
    ]

    for label, student_hash, error in cases:
        started = time.perf_counter()
        if error is None:
            service.request_briefing(student_hash)
        else:
            with pytest.raises(error):
                service.request_briefing(student_hash)
        elapsed = time.perf_counter() - started
        assert elapsed < SC006_BUDGET_SECONDS, f"{label} took {elapsed:.3f}s"


# --- FR-040: the traceability record cannot silently drift -------------------


def _defined_verification_names() -> set[str]:
    """Every verification name defined under tests/, read from the source syntax trees.

    Parsing the source keeps this independent of how the suite is invoked, and needs no runner
    internals (research R6).
    """
    names: set[str] = set()
    for path in TESTS_DIR.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                names.add(f"{path.name}::{node.name}")
                names.add(node.name)
    return names


def _cited_verification_names() -> set[str]:
    """Names the traceability record cites, from every section including tracked re-verification."""
    text = TRACEABILITY.read_text(encoding="utf-8")
    cited = set(re.findall(r"`?(test_[A-Za-z0-9_]+\.py::(?:test_[A-Za-z0-9_]+))`?", text))
    cited |= set(re.findall(r"`::(test_[A-Za-z0-9_]+)`", text))
    return cited


def test_traceability_record_exists_and_has_its_required_sections():
    """The record is a deliverable; its four sections are required by FR-038, FR-039 and FR-041."""
    assert TRACEABILITY.exists(), f"traceability record missing at {TRACEABILITY}"
    text = TRACEABILITY.read_text(encoding="utf-8")
    for heading in (
        "## 1. Scenario map",
        "## 2. Tracked re-verification",
        "## 3. Recorded defects",
        "## 4. Unverified criteria",
    ):
        assert heading in text, f"missing section: {heading}"


def test_every_cited_verification_resolves():
    """A cited verification that no longer exists fails here, by design (FR-040, SC-016).

    Feature-001's traceability table cites five verification names that no longer resolve. This
    check is what stops Feature-003's record going the same way — including the Feature-001 and
    Feature-002 verifications cited under tracked re-verification, whose disappearance would mean
    Feature-003's cross-boundary coverage had lapsed.
    """
    defined = _defined_verification_names()
    cited = _cited_verification_names()

    assert cited, "the traceability record cites no verifications — the record is not wired up"

    unresolved = sorted(name for name in cited if name not in defined)
    assert not unresolved, (
        "traceability record cites verifications that no longer resolve:\n  "
        + "\n  ".join(unresolved)
        + "\nUpdate specs/003-briefing-workflow-testing/traceability.md. Do not edit "
        "Feature-001 or Feature-002 verification files to make a citation resolve."
    )


def test_unverified_criteria_are_recorded_with_a_reason():
    """FR-041: 'out of scope' alone is insufficient; each entry carries a specific reason."""
    text = TRACEABILITY.read_text(encoding="utf-8")
    section = text.split("## 4. Unverified criteria", 1)[1]
    assert "SC-007" in section, "Feature-001 SC-007's deferral must be recorded (FR-038)"
    assert "outside the seam boundary" in section, "the deferral must carry its specific reason"
