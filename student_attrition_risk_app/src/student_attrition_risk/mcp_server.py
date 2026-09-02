"""FastMCP tools backed by the shared StudentService."""

from typing import Any

from .student_service import StudentService


def create_mcp_server(service: StudentService) -> Any:
    from fastmcp import FastMCP

    mcp = FastMCP("student-attrition-risk")

    @mcp.tool()
    def get_student_prediction(student_hash: str) -> dict[str, Any]:
        profile = service.get_student_profile(student_hash)
        return profile.prediction.model_dump(mode="json")

    @mcp.tool()
    def get_student_profile(student_hash: str) -> dict[str, Any]:
        return service.get_student_profile(student_hash).model_dump(mode="json")

    @mcp.tool()
    def get_high_risk_students(limit: int = 20) -> list[dict[str, Any]]:
        return [prediction.model_dump(mode="json") for prediction in service.get_high_risk_students(limit)]

    @mcp.tool()
    def generate_student_briefing(student_hash: str) -> dict[str, Any]:
        return service.generate_briefing(student_hash).model_dump(mode="json")

    return mcp
