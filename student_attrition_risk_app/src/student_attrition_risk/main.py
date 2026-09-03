"""Application composition root."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .api import create_api
from .briefing_instructions import InterimInstructions
from .briefing_provider import StubGenerationProvider
from .briefing_store import InMemoryBriefingStore, VolumeBriefingStore
from .briefing_validation import InterimValidator
from .config import Settings
from .mcp_server import create_mcp_server
from .retry_workflow import SingleRetryWorkflow
from .streamlit_host import StreamlitHost, StreamlitProxy
from .student_repository import DatabricksStudentRepository, MockStudentRepository
from .student_service import StudentService


def build_service(settings: Settings | None = None) -> StudentService:
    settings = settings or Settings.from_env()
    repository = MockStudentRepository() if settings.use_mock_data else DatabricksStudentRepository(settings)
    # Placeholder seams still owned by later stories: generation (US-13), instructions (US-12),
    # validation (US-14). Feature-002 / US-15 supplies the concrete retry workflow and, when
    # BRIEFING_VOLUME is set, the governed Unity Catalog Volume store; orchestration is unchanged.
    generation_provider = StubGenerationProvider()
    validator = InterimValidator()
    store = VolumeBriefingStore(settings) if settings.briefing_volume else InMemoryBriefingStore()
    return StudentService(
        repository=repository,
        generation_provider=generation_provider,
        instructions=InterimInstructions(),
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


app = create_app()
