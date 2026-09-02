"""REST API routes."""

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query

from .models import HealthStatus, StudentBriefing, StudentPrediction, StudentRiskProfile
from .student_service import StudentNotFoundError, StudentService


def create_api(service: StudentService) -> FastAPI:
    app = FastAPI(title="Student Attrition Risk API")
    router = APIRouter(prefix="/api")

    @router.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        try:
            return service.health_check()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Databricks data source unavailable") from exc

    @router.get("/students/high-risk", response_model=list[StudentPrediction])
    def high_risk(limit: int = Query(default=20, ge=1, le=100)) -> list[StudentPrediction]:
        try:
            return service.get_high_risk_students(limit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Databricks data source unavailable") from exc

    @router.get("/students/{student_hash}", response_model=StudentRiskProfile)
    def student(
        student_hash: str = Path(min_length=1, max_length=256),
    ) -> StudentRiskProfile:
        try:
            return service.get_student_profile(student_hash)
        except StudentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Student hash not found") from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Databricks data source unavailable") from exc

    @router.post("/students/{student_hash}/briefing", response_model=StudentBriefing)
    def briefing(student_hash: str = Path(min_length=1, max_length=256)) -> StudentBriefing:
        try:
            return service.generate_briefing(student_hash)
        except StudentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Student hash not found") from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Databricks data source unavailable") from exc

    app.include_router(router)
    return app
