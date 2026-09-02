import pytest

from student_attrition_risk.briefing_provider import TemplateBriefingProvider
from student_attrition_risk.mcp_server import create_mcp_server
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import StudentService


@pytest.mark.anyio
async def test_mcp_registers_shared_service_tools():
    mcp = create_mcp_server(StudentService(MockStudentRepository(), TemplateBriefingProvider()))
    tools = await mcp.get_tools()
    assert set(tools) == {
        "get_student_prediction",
        "get_student_profile",
        "get_high_risk_students",
        "generate_student_briefing",
    }
