"""Application composition root."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

from .api import create_api

# from .briefing_instructions import InterimInstructions
from .briefing_instructions import StructuredBriefingInstructions
from .briefing_provider import DatabricksGenerationProvider, StubGenerationProvider
from .briefing_store import InMemoryBriefingStore, VolumeBriefingStore
from .briefing_validation import StructuredBriefingValidator
from .config import ConfigurationError, Settings
from .mcp_server import create_mcp_server
from .retry_workflow import SingleRetryWorkflow
from .streamlit_host import StreamlitHost, StreamlitProxy
from .student_repository import DatabricksStudentRepository, MockStudentRepository
from .student_service import StudentService

logger = logging.getLogger(__name__)


def build_service(settings: Settings | None = None) -> StudentService:
    settings = settings or Settings.from_env()
    repository = MockStudentRepository() if settings.use_mock_data else DatabricksStudentRepository(settings)
    # Placeholder seams still owned by later stories: generation (US-13), instructions (US-12),
    # validation (US-14). Feature-002 / US-15 supplies the concrete retry workflow and, when
    # BRIEFING_VOLUME is set, the governed Unity Catalog Volume store; orchestration is unchanged.
    # Without a model name the stub provider raises ConfigurationError only when a briefing is
    # requested, so profiles, the high-risk list and mock mode keep working (Feature-001 FR-014).
    if settings.model_name:
        generation_provider = DatabricksGenerationProvider(model_name=settings.model_name)
    else:
        generation_provider = StubGenerationProvider()
    validator = StructuredBriefingValidator()
    store = VolumeBriefingStore(settings) if settings.briefing_volume else InMemoryBriefingStore()
    return StudentService(
        repository=repository,
        generation_provider=generation_provider,
        instructions=StructuredBriefingInstructions(),
        # instructions=InterimInstructions(),
        validator=validator,
        retry_workflow=SingleRetryWorkflow(
            generation_provider=generation_provider, validator=validator
        ),
        store=store,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    service = build_service(settings)
    mcp = create_mcp_server(service)
    mcp_app = mcp.http_app(path="/")
    streamlit = StreamlitHost(settings.streamlit_port)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with mcp_app.lifespan(_):
            streamlit.start()
            try:
                yield
            finally:
                streamlit.stop()

    app = create_api(service)
    app.router.lifespan_context = lifespan
    app.mount("/mcp", mcp_app)
    app.mount("/ui", StreamlitProxy(settings.streamlit_port))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/ui/")

    return app


def create_configuration_error_app(error: ConfigurationError) -> FastAPI:
    """Stand-in app for invalid configuration: every request gets a 503 that names the problem,
    rather than an unexplained 500. Configuration messages name settings, never their values."""
    detail = f"Application configuration error: {error}"
    logger.error(detail)
    app = FastAPI()

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    def configuration_error(path: str) -> JSONResponse:
        return JSONResponse({"detail": detail}, status_code=503)

    return app


try:
    app = create_app()
except ConfigurationError as error:
    app = create_configuration_error_app(error)
