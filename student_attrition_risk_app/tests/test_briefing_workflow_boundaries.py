"""Feature-003 (US-18) cross-cutting — boundary consistency and observability.

**No REST verification is written here.** Feature-001's ``tests/test_api.py`` already covers every
briefing outcome at that boundary, so under FR-032 it is tracked as re-verification in
``specs/003-briefing-workflow-testing/traceability.md`` rather than repeated.

The tool interface had three uncovered outcomes; FR-033 covers them here:

- terminal failure carrying its category
- storage failure
- configuration failure

FR-034 covers failure-path log hygiene: the two existing hygiene verifications assert only the
success-path record, leaving every failure-path record unasserted.

Offline: controlled generation and validation outcomes, no network or workspace.
"""

import logging

import pytest

from student_attrition_risk.config import ConfigurationError
from workflow_doubles import (
    FLAGGED,
    HAS_EXISTING,
    NOT_FLAGGED,
    UNKNOWN,
    CountingStore,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_mcp_server,
    build_service,
    draft,
    failed,
    passed,
)

SECRET_TEXT = "SECRET BRIEFING BODY THAT MUST NEVER BE LOGGED"
SERVICE_LOGGER = "student_attrition_risk.student_service"


async def _call_tool(mcp, name, **arguments):
    tools = await mcp.get_tools()
    return tools[name].fn(**arguments)


# --- FR-033: tool-boundary outcomes with no existing coverage ----------------


@pytest.mark.anyio
async def test_tool_boundary_terminal_failure_carries_the_category():
    """A terminal failure surfaces as a tool error naming the category (FR-033).

    ``tests/test_mcp_tools.py`` covers not-at-risk and not-found only; this outcome is uncovered
    at this boundary.
    """
    from fastmcp.exceptions import ToolError

    mcp = build_mcp_server(
        build_service(
            generation=ScriptedGenerationProvider(RuntimeError("down"), RuntimeError("down")),
            validation=ScriptedValidator(),
        )
    )

    with pytest.raises(ToolError, match="generation"):
        await _call_tool(mcp, "generate_student_briefing", student_hash=FLAGGED)


@pytest.mark.anyio
async def test_tool_boundary_terminal_validation_failure_carries_its_own_category():
    """The validation category is distinguishable from the generation one (FR-033)."""
    from fastmcp.exceptions import ToolError

    mcp = build_mcp_server(
        build_service(
            generation=ScriptedGenerationProvider(draft("first"), draft("second")),
            validation=ScriptedValidator(failed(), failed()),
        )
    )

    with pytest.raises(ToolError, match="validation"):
        await _call_tool(mcp, "generate_student_briefing", student_hash=FLAGGED)


@pytest.mark.anyio
async def test_tool_boundary_storage_failure_is_surfaced():
    """A storage failure is not reported as success at this boundary (FR-033)."""
    from fastmcp.exceptions import ToolError

    mcp = build_mcp_server(
        build_service(
            generation=ScriptedGenerationProvider(draft("a briefing")),
            validation=ScriptedValidator(passed()),
            store=CountingStore(raise_on_save=True),
        )
    )

    with pytest.raises(ToolError, match="stored"):
        await _call_tool(mcp, "generate_student_briefing", student_hash=FLAGGED)


@pytest.mark.anyio
async def test_tool_boundary_configuration_failure_is_surfaced():
    """A configuration failure surfaces as itself, never as a briefing failure (FR-033)."""
    from fastmcp.exceptions import ToolError

    mcp = build_mcp_server(
        build_service(
            generation=ScriptedGenerationProvider(
                ConfigurationError("Briefing generation is not configured")
            ),
            validation=ScriptedValidator(),
        )
    )

    with pytest.raises(ToolError, match="not configured"):
        await _call_tool(mcp, "generate_student_briefing", student_hash=FLAGGED)


# --- FR-034: failure-path log hygiene ----------------------------------------


def _records(caplog) -> str:
    return " ".join(record.getMessage() for record in caplog.records)


def _assert_metadata_only(text: str, label: str) -> None:
    """No briefing text, prompt text, acceptance-criteria content or secret (FR-034, SC-011)."""
    assert "briefing_workflow" in text, f"{label}: no workflow record emitted"
    assert SECRET_TEXT not in text, f"{label}: briefing text leaked"
    assert "PROFILE JSON" not in text, f"{label}: prompt text leaked"
    assert "APPROVED MODEL FEATURE VALUES" not in text, f"{label}: feature context leaked"
    assert "PLACEHOLDER_CRITERION" not in text, f"{label}: acceptance-criteria content leaked"
    assert "PLACEHOLDER_VALIDATION_FEEDBACK" not in text, f"{label}: validation feedback leaked"


def test_failure_path_records_are_metadata_only(caplog):
    """Every failure-path record carries metadata only (FR-034).

    The existing hygiene verifications assert ``outcome=generated`` only, so each record below is
    otherwise unasserted.
    """
    cases = []

    # terminal generation
    cases.append(
        (
            "terminal-generation",
            build_service(
                generation=ScriptedGenerationProvider(
                    RuntimeError(SECRET_TEXT), RuntimeError(SECRET_TEXT)
                ),
                validation=ScriptedValidator(),
            ),
            FLAGGED,
            False,
        )
    )
    # terminal validation, with criteria and feedback that must not appear
    cases.append(
        (
            "terminal-validation",
            build_service(
                generation=ScriptedGenerationProvider(
                    draft(SECRET_TEXT), draft(SECRET_TEXT)
                ),
                validation=ScriptedValidator(
                    failed(criteria=["PLACEHOLDER_CRITERION_A"], feedback="PLACEHOLDER_VALIDATION_FEEDBACK"),
                    failed(criteria=["PLACEHOLDER_CRITERION_A"], feedback="PLACEHOLDER_VALIDATION_FEEDBACK"),
                ),
            ),
            FLAGGED,
            False,
        )
    )
    # storage error
    cases.append(
        (
            "storage-error",
            build_service(
                generation=ScriptedGenerationProvider(draft(SECRET_TEXT)),
                validation=ScriptedValidator(passed()),
                store=CountingStore(raise_on_save=True),
            ),
            FLAGGED,
            False,
        )
    )
    # not at risk
    cases.append(
        (
            "not-at-risk",
            build_service(
                generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
            ),
            NOT_FLAGGED,
            False,
        )
    )
    # not found
    cases.append(
        (
            "not-found",
            build_service(
                generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
            ),
            UNKNOWN,
            False,
        )
    )

    for label, service, student_hash, regenerate in cases:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
            try:
                service.request_briefing(student_hash, regenerate=regenerate)
            except Exception:  # noqa: BLE001 - the failure is the point; the record is the subject
                pass
        _assert_metadata_only(_records(caplog), label)


def test_none_available_retrieval_record_is_metadata_only(caplog):
    """The retrieval path's none-available record is also unasserted by existing verifications."""
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
    )

    with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
        assert service.get_stored_briefing(FLAGGED) is None

    text = _records(caplog)
    assert "outcome=none_available" in text
    _assert_metadata_only(text, "none-available")


def test_returned_existing_record_is_metadata_only(caplog):
    """The get-or-create record carries the stored briefing's metadata, not its text."""
    store = CountingStore()
    store.seed(HAS_EXISTING, SECRET_TEXT)
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=store
    )

    with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
        service.request_briefing(HAS_EXISTING)

    text = _records(caplog)
    assert "outcome=returned_existing" in text
    _assert_metadata_only(text, "returned-existing")
