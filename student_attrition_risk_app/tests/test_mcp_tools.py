from datetime import UTC, datetime

import pytest

from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.briefing_validation import InterimValidator
from student_attrition_risk.mcp_server import create_mcp_server
from student_attrition_risk.models import DraftBriefing, ValidatedBriefing
from student_attrition_risk.retry_workflow import RetryNotConfigured
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import StudentService

FLAGGED = "synthetic-student-001"
NOT_FLAGGED = "synthetic-student-002"
HAS_EXISTING = "synthetic-student-003"


def _mcp(*, generation_provider=None, store=None):
    service = StudentService(
        repository=MockStudentRepository(),
        generation_provider=generation_provider or StubGenerationProvider(),
        instructions=InterimInstructions(),
        validator=InterimValidator(),
        retry_workflow=RetryNotConfigured(),
        store=store if store is not None else InMemoryBriefingStore(),
    )
    return create_mcp_server(service)


async def _call(mcp, name, **arguments):
    tools = await mcp.get_tools()
    return tools[name].fn(**arguments)


def _seed(store, student_hash, text):
    InMemoryBriefingStore.save_validated(
        store,
        ValidatedBriefing(
            student_deidentified_hash=student_hash,
            text=text,
            source="generated",
            validator_id="interim-pass-through",
            generated_at=datetime.now(UTC),
            risk_percentage=64.0,
            at_risk_flag=True,
            prediction_threshold=0.5,
        ),
    )


@pytest.mark.anyio
async def test_mcp_registers_the_five_shared_service_tools():
    tools = await _mcp().get_tools()
    assert set(tools) == {
        "get_student_prediction",
        "get_student_profile",
        "get_high_risk_students",
        "generate_student_briefing",
        "get_student_briefing",
    }


@pytest.mark.anyio
async def test_generate_student_briefing_returns_existing_then_regenerates():
    store = InMemoryBriefingStore()
    _seed(store, HAS_EXISTING, "stored body")
    mcp = _mcp(
        generation_provider=StubGenerationProvider(
            draft=DraftBriefing(student_deidentified_hash=HAS_EXISTING, text="regen")),
        store=store,
    )
    existing = await _call(mcp, "generate_student_briefing", student_hash=HAS_EXISTING)
    assert existing["source"] == "stored"
    regenerated = await _call(
        mcp, "generate_student_briefing", student_hash=HAS_EXISTING, regenerate=True
    )
    assert regenerated["text"] == "regen"


@pytest.mark.anyio
async def test_generate_student_briefing_error_messages():
    from fastmcp.exceptions import ToolError

    mcp = _mcp()
    with pytest.raises(ToolError, match="not flagged at risk"):
        await _call(mcp, "generate_student_briefing", student_hash=NOT_FLAGGED)
    with pytest.raises(ToolError, match="not found"):
        await _call(mcp, "generate_student_briefing", student_hash="missing")


@pytest.mark.anyio
async def test_get_student_briefing_returns_value_or_none_available():
    store = InMemoryBriefingStore()
    _seed(store, HAS_EXISTING, "kept")
    mcp = _mcp(store=store)
    present = await _call(mcp, "get_student_briefing", student_hash=HAS_EXISTING)
    assert present["source"] == "stored"
    absent = await _call(mcp, "get_student_briefing", student_hash=FLAGGED)
    assert absent == {"available": False, "student_hash": FLAGGED}
