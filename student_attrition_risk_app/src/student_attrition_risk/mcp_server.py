"""FastMCP tools backed by the shared StudentService."""

from typing import Any

from .config import ConfigurationError
from .student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotAtRiskError,
    StudentNotFoundError,
    StudentService,
)


def create_mcp_server(service: StudentService) -> Any:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

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
    def generate_student_briefing(student_hash: str, regenerate: bool = False) -> dict[str, Any]:
        try:
            return service.request_briefing(student_hash, regenerate=regenerate).model_dump(mode="json")
        except StudentNotFoundError as exc:
            raise ToolError("student hash not found") from exc
        except StudentNotAtRiskError as exc:
            raise ToolError("student is not flagged at risk") from exc
        except BriefingNotProducedError as exc:
            raise ToolError(f"briefing could not be produced ({exc.category})") from exc
        except BriefingStorageError as exc:
            raise ToolError("validated briefing could not be stored") from exc
        except ConfigurationError as exc:
            raise ToolError(str(exc).lower()) from exc

    @mcp.tool()
    def get_student_briefing(student_hash: str) -> dict[str, Any]:
        try:
            briefing = service.get_stored_briefing(student_hash)
        except StudentNotFoundError as exc:
            raise ToolError("student hash not found") from exc
        if briefing is None:
            return {"available": False, "student_hash": student_hash}
        return briefing.model_dump(mode="json")

    return mcp
