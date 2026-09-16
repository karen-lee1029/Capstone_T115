"""Feature-003 (US-18) cross-cutting — boundary consistency and observability.

Feature-001's ``tests/test_api.py`` covers the briefing **write** outcomes at the REST boundary,
so those are tracked as re-verification in ``traceability.md`` § 2 rather than repeated. It does
**not** cover a storage outage during retrieval; that gap is covered here (FR-032, FR-033).

Covered in this file:

- FR-033: the three write-path outcomes uncovered at the tool interface — terminal failure,
  storage failure, configuration failure.
- FR-033 and the specification's edge case "Governed storage is unreachable while reading": a
  read outage must surface as an explicit failure, **distinct from the result meaning no briefing
  is available**, at the service, REST and tool boundaries.
- FR-034: failure-path log hygiene, checked against rendered output including any exception
  traceback, not against the message alone.

Offline: controlled generation and validation outcomes, and the existing in-memory files client.
"""

import logging

import pytest
from databricks.sdk.errors import NotFound

from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.student_service import BriefingStorageError
from workflow_doubles import (
    FLAGGED,
    HAS_EXISTING,
    NOT_FLAGGED,
    UNKNOWN,
    CountingStore,
    FakeFilesClient,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_mcp_server,
    build_rest_client,
    build_service,
    draft,
    failed,
    passed,
    rendered_log_output,
    validated_briefing,
    volume_store,
)

SECRET_TEXT = "SECRET BRIEFING BODY THAT MUST NEVER BE LOGGED"
SERVICE_LOGGER = "student_attrition_risk.student_service"


async def _call_tool(mcp, name, **arguments):
    tools = await mcp.get_tools()
    return tools[name].fn(**arguments)


def _service_with_unreadable_store(*, fail_on: str):
    """A service whose governed store fails while reading, with a briefing already stored."""
    fake = FakeFilesClient()
    governed, _ = volume_store(fake)
    governed.save_validated(validated_briefing(HAS_EXISTING, "a stored briefing"))
    setattr(fake, fail_on, RuntimeError("volume unreachable"))
    return build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=governed
    )


# --- FR-033: tool-boundary write outcomes with no existing coverage ----------


@pytest.mark.anyio
async def test_tool_boundary_terminal_failure_carries_the_category():
    """A terminal failure surfaces as a tool error naming the category (FR-033)."""
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
    """A storage write failure is not reported as success at this boundary (FR-033)."""
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


# --- Read outage must not be reported as absence -----------------------------
#
# Specification edge case: "Governed storage is unreachable while reading: the retrieval path
# surfaces an explicit error, distinct from the 'none available' result." Feature-002 verifies
# this at the store level only; the boundary mapping is unverified.


@pytest.mark.parametrize("fail_on", ["fail_list", "fail_download"], ids=["list", "download"])
def test_service_reports_a_read_outage_as_an_error_not_as_absence(fail_on):
    """At the service boundary an outage raises; absence returns ``None`` (FR-033)."""
    service = _service_with_unreadable_store(fail_on=fail_on)

    with pytest.raises(BriefingStorageError):
        service.get_stored_briefing(HAS_EXISTING)


def test_service_still_reports_genuine_absence_as_absence():
    """The contrast case: a reachable store with nothing stored returns ``None``, not an error."""
    governed, _ = volume_store()
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=governed
    )

    assert service.get_stored_briefing(HAS_EXISTING) is None


@pytest.mark.parametrize("fail_on", ["fail_list", "fail_download"], ids=["list", "download"])
def test_rest_boundary_distinguishes_a_read_outage_from_absence(fail_on):
    """An outage is 503 "store unavailable"; absence is 404 "none available" (FR-033).

    Collapsing the two would tell an advisor a briefing does not exist when the store is simply
    unreachable. No existing verification exercises a read failure at this boundary.
    """
    outage = build_rest_client(_service_with_unreadable_store(fail_on=fail_on))
    response = outage.get(f"/api/students/{HAS_EXISTING}/briefing")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()

    governed, _ = volume_store()
    absent = build_rest_client(
        build_service(
            generation=ScriptedGenerationProvider(),
            validation=ScriptedValidator(),
            store=governed,
        )
    )
    absent_response = absent.get(f"/api/students/{HAS_EXISTING}/briefing")

    assert absent_response.status_code == 404
    assert absent_response.status_code != response.status_code


@pytest.mark.anyio
async def test_tool_boundary_does_not_report_a_read_outage_as_absence():
    """The tool interface must not answer "not available" when the store is unreachable."""
    mcp = build_mcp_server(_service_with_unreadable_store(fail_on="fail_list"))

    with pytest.raises(BriefingStorageError):
        await _call_tool(mcp, "get_student_briefing", student_hash=HAS_EXISTING)


@pytest.mark.anyio
async def test_tool_boundary_still_reports_genuine_absence_as_absence():
    """The contrast case at the tool boundary."""
    governed, _ = volume_store()
    mcp = build_mcp_server(
        build_service(
            generation=ScriptedGenerationProvider(),
            validation=ScriptedValidator(),
            store=governed,
        )
    )

    result = await _call_tool(mcp, "get_student_briefing", student_hash=HAS_EXISTING)

    assert result == {"available": False, "student_hash": HAS_EXISTING}


def test_a_missing_directory_is_absence_not_an_outage():
    """A not-found from the files client means nothing stored, not a failure (FR-033)."""
    fake = FakeFilesClient()
    fake.fail_list = NotFound("directory not found")
    governed, _ = volume_store(fake)
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator(), store=governed
    )

    assert service.get_stored_briefing(HAS_EXISTING) is None


# --- FR-034: failure-path log hygiene, including exception tracebacks --------


def _assert_metadata_only(text: str, label: str) -> None:
    """No briefing text, prompt text, criteria content or secret (FR-034, SC-011)."""
    assert "briefing_workflow" in text, f"{label}: no workflow record emitted"
    assert SECRET_TEXT not in text, f"{label}: briefing text leaked"
    assert "PROFILE JSON" not in text, f"{label}: prompt text leaked"
    assert "APPROVED MODEL FEATURE VALUES" not in text, f"{label}: feature context leaked"
    assert "PLACEHOLDER_CRITERION" not in text, f"{label}: acceptance-criteria content leaked"
    assert "PLACEHOLDER_VALIDATION_FEEDBACK" not in text, f"{label}: validation feedback leaked"


def test_the_privacy_check_itself_detects_a_traceback_leak(caplog):
    """The check must inspect rendered output, not ``record.getMessage()`` alone.

    A privacy check built on the message alone approves a record whose visible traceback contains
    the briefing text, because the traceback is rendered from ``exc_info`` rather than being part
    of the message. This verifies the helper the scenarios below rely on would actually catch that.
    """
    logger = logging.getLogger(f"{SERVICE_LOGGER}.privacy_check_probe")
    with caplog.at_level(logging.INFO, logger=logger.name):
        try:
            raise RuntimeError(SECRET_TEXT)
        except RuntimeError:
            logger.exception("briefing_workflow outcome=probe")

    message_only = " ".join(record.getMessage() for record in caplog.records)
    rendered = rendered_log_output(caplog)

    assert SECRET_TEXT not in message_only, "precondition: the message itself carries no secret"
    assert SECRET_TEXT in rendered, "the helper must see exception information"
    with pytest.raises(AssertionError):
        _assert_metadata_only(rendered, "probe")


def test_failure_path_records_are_metadata_only(caplog):
    """Every failure-path record carries metadata only, tracebacks included (FR-034)."""
    cases = [
        (
            "terminal-generation",
            lambda: build_service(
                generation=ScriptedGenerationProvider(
                    RuntimeError(SECRET_TEXT), RuntimeError(SECRET_TEXT)
                ),
                validation=ScriptedValidator(),
            ),
            FLAGGED,
            False,
        ),
        (
            "terminal-validation",
            lambda: build_service(
                generation=ScriptedGenerationProvider(draft(SECRET_TEXT), draft(SECRET_TEXT)),
                validation=ScriptedValidator(
                    failed(criteria=["PLACEHOLDER_CRITERION_A"], feedback="PLACEHOLDER_VALIDATION_FEEDBACK"),
                    failed(criteria=["PLACEHOLDER_CRITERION_A"], feedback="PLACEHOLDER_VALIDATION_FEEDBACK"),
                ),
            ),
            FLAGGED,
            False,
        ),
        (
            "storage-error",
            lambda: build_service(
                generation=ScriptedGenerationProvider(draft(SECRET_TEXT)),
                validation=ScriptedValidator(passed()),
                store=CountingStore(raise_on_save=True),
            ),
            FLAGGED,
            False,
        ),
        (
            "not-at-risk",
            lambda: build_service(
                generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
            ),
            NOT_FLAGGED,
            False,
        ),
        (
            "not-found",
            lambda: build_service(
                generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
            ),
            UNKNOWN,
            False,
        ),
    ]

    for label, factory, student_hash, regenerate in cases:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
            try:
                factory().request_briefing(student_hash, regenerate=regenerate)
            except Exception:  # noqa: BLE001 - the failure is the point; the record is the subject
                pass
        _assert_metadata_only(rendered_log_output(caplog), label)


def test_none_available_retrieval_record_is_metadata_only(caplog):
    """The retrieval path's none-available record (FR-034)."""
    service = build_service(
        generation=ScriptedGenerationProvider(), validation=ScriptedValidator()
    )

    with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
        assert service.get_stored_briefing(FLAGGED) is None

    text = rendered_log_output(caplog)
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

    text = rendered_log_output(caplog)
    assert "outcome=returned_existing" in text
    _assert_metadata_only(text, "returned-existing")
