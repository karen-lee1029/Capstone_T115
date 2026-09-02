"""REST API routes."""

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query

from .config import ConfigurationError
from .models import HealthStatus, StudentPrediction, StudentRiskProfile, ValidatedBriefing
from .student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotAtRiskError,
    StudentNotFoundError,
    StudentService,
)


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

    @router.post("/students/{student_hash}/briefing", response_model=ValidatedBriefing)
    def request_briefing(
        student_hash: str = Path(min_length=1, max_length=256),
        regenerate: bool = Query(default=False),
    ) -> ValidatedBriefing:
        """Get-or-create: return the existing validated briefing if one exists, otherwise
        run the generation seams. ``?regenerate=true`` forces a fresh run."""
        try:
            return service.request_briefing(student_hash, regenerate=regenerate)
        except StudentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Student hash not found") from exc
        except StudentNotAtRiskError as exc:
            raise HTTPException(status_code=409, detail="Student is not flagged at risk") from exc
        except BriefingNotProducedError as exc:
            raise HTTPException(
                status_code=502, detail=f"Briefing could not be produced ({exc.category})"
            ) from exc
        except BriefingStorageError as exc:
            raise HTTPException(
                status_code=503, detail="Validated briefing could not be stored"
            ) from exc
        except ConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Databricks data source unavailable") from exc

    @router.get("/students/{student_hash}/briefing", response_model=ValidatedBriefing)
    def stored_briefing(
        student_hash: str = Path(min_length=1, max_length=256),
    ) -> ValidatedBriefing:
        try:
            briefing = service.get_stored_briefing(student_hash)
        except StudentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Student hash not found") from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="Validated briefing store unavailable"
            ) from exc
        if briefing is None:
            raise HTTPException(status_code=404, detail="No validated briefing available")
        return briefing

    app.include_router(router)
    return app
