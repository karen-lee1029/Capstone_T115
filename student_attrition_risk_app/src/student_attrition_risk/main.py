"""Application composition root."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .api import create_api
from .briefing_instructions import InterimInstructions
from .briefing_provider import StubGenerationProvider
from .briefing_store import InMemoryBriefingStore
from .briefing_validation import InterimValidator
from .config import Settings
from .mcp_server import create_mcp_server
from .retry_workflow import RetryNotConfigured
from .streamlit_host import StreamlitHost, StreamlitProxy
from .student_repository import DatabricksStudentRepository, MockStudentRepository
from .student_service import StudentService


def build_service(settings: Settings | None = None) -> StudentService:
    settings = settings or Settings.from_env()
    repository = MockStudentRepository() if settings.use_mock_data else DatabricksStudentRepository(settings)
    # Feature-001 (US-08) wires placeholder seams. Concrete implementations are swapped in
    # here by US-13 (generation), US-12 (instructions), US-14 (validation), and
    # US-15 / Feature-002 (retry + governed Volume storage) with no orchestration change.
    return StudentService(
        repository=repository,
        generation_provider=StubGenerationProvider(),
        instructions=InterimInstructions(),
        validator=InterimValidator(),
        retry_workflow=RetryNotConfigured(),
        store=InMemoryBriefingStore(),
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
