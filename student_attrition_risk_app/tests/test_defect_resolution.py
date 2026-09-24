"""Feature-004 (US-20) — Final Defect Resolution regression groups.

One section per defect fixed by Feature-004, named after its ID in
``specs/004-final-defect-resolution/defect-register.md``, in the order B2, B4, C3, B1.
Each group fails against the sweep commit ``3181882`` and passes once its fix lands
(spec FR-023, FR-024).

Offline: controlled generation, validation and storage outcomes only. The Feature-002
``doubles.py`` and Feature-003 ``workflow_doubles.py`` modules are imported read-only; any extra
double a group needs is defined locally in its own section. No merged test file is edited.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import BriefingStorageError
from workflow_doubles import (
    FLAGGED,
    NOT_FLAGGED,
    UNKNOWN,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_mcp_server,
    build_service,
)

# ---- B2: validator exception escapes the retry workflow (register B2) ----








# ---- B4: unrelated files in a student's Volume folder hide the briefing (register B4) ----








# ---- C3: briefing tools leak raw backend error text (register C3, Renny half) ----


class _UnreadableStore:
    """C3: a store whose every read fails with a message naming an internal Volume path."""

    def has_validated(self, student_hash):
        raise BriefingStorageError("could not list stored briefings for /Volumes/secret/path")

    def get_latest_validated(self, student_hash):
        raise BriefingStorageError("could not list stored briefings for /Volumes/secret/path")

    def save_validated(self, briefing):
        raise AssertionError("C3 never writes")


class _BrokenStore(_UnreadableStore):
    """C3: a store read failing with an unexpected, non-storage exception."""

    def get_latest_validated(self, student_hash):
        raise RuntimeError("warehouse xyz exploded")


class _ExplodingFeaturesRepository(MockStudentRepository):
    """C3: a repository that fails outside the generation workflow with warehouse text."""

    def get_model_features(self, student_hash):
        raise RuntimeError("warehouse xyz exploded")


async def _c3_call(mcp, name, **arguments):
    tools = await mcp.get_tools()
    return tools[name].fn(**arguments)


def _c3_mcp(*, generation=None, store=None, repository=None):
    return build_mcp_server(
        build_service(
            generation=generation or ScriptedGenerationProvider(),
            validation=ScriptedValidator(),
            store=store,
            repository=repository,
        )
    )


@pytest.mark.anyio
async def test_c3_get_student_briefing_store_read_failure_is_safe():
    """DEC-12: re-raised as BriefingStorageError with safe text and no chained cause."""
    mcp = _c3_mcp(store=_UnreadableStore())

    with pytest.raises(BriefingStorageError) as caught:
        await _c3_call(mcp, "get_student_briefing", student_hash=FLAGGED)

    assert str(caught.value) == "validated briefing store unavailable"
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


@pytest.mark.anyio
async def test_c3_get_student_briefing_other_failure_is_safe():
    mcp = _c3_mcp(store=_BrokenStore())

    with pytest.raises(ToolError) as caught:
        await _c3_call(mcp, "get_student_briefing", student_hash=FLAGGED)

    assert str(caught.value) == "validated briefing store unavailable"
    assert "warehouse" not in str(caught.value)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tool", "mcp_kwargs", "expected", "leak"),
    [
        (
            "get_student_briefing",
            {"store": _UnreadableStore()},
            "validated briefing store unavailable",
            "/Volumes",
        ),
        (
            "generate_student_briefing",
            {"repository": _ExplodingFeaturesRepository()},
            "databricks data source unavailable",
            "warehouse",
        ),
    ],
)
async def test_c3_mcp_client_receives_only_the_safe_message(tool, mcp_kwargs, expected, leak):
    """What FastMCP actually forwards to a client over the protocol."""
    async with Client(_c3_mcp(**mcp_kwargs)) as client:
        result = await client.call_tool(tool, {"student_hash": FLAGGED}, raise_on_error=False)

    text = " ".join(block.text for block in result.content)
    assert result.is_error
    assert expected in text
    assert leak not in text


@pytest.mark.anyio
async def test_c3_generate_student_briefing_data_source_failure_is_safe():
    mcp = _c3_mcp(repository=_ExplodingFeaturesRepository())

    with pytest.raises(ToolError) as caught:
        await _c3_call(mcp, "generate_student_briefing", student_hash=FLAGGED)

    assert str(caught.value) == "databricks data source unavailable"
    assert "warehouse" not in str(caught.value)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tool", "student_hash", "expected"),
    [
        ("generate_student_briefing", UNKNOWN, "student hash not found"),
        ("get_student_briefing", UNKNOWN, "student hash not found"),
        ("generate_student_briefing", NOT_FLAGGED, "student is not flagged at risk"),
    ],
)
async def test_c3_safely_mapped_failures_are_unchanged(tool, student_hash, expected):
    mcp = _c3_mcp()

    with pytest.raises(ToolError) as caught:
        await _c3_call(mcp, tool, student_hash=student_hash)

    assert str(caught.value) == expected


@pytest.mark.anyio
async def test_c3_configuration_failure_keeps_its_own_text():
    mcp = _c3_mcp(
        generation=ScriptedGenerationProvider(
            ConfigurationError("Briefing generation is not configured")
        )
    )

    with pytest.raises(ToolError) as caught:
        await _c3_call(mcp, "generate_student_briefing", student_hash=FLAGGED)

    assert str(caught.value) == "briefing generation is not configured"








# ---- B1: store read outage reported as "could not be stored" (register B1) ----







