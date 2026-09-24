"""Feature-004 (US-20) — Final Defect Resolution regression groups.

One section per defect fixed by Feature-004, named after its ID in
``specs/004-final-defect-resolution/defect-register.md``, in the order B2, B4, C3, B1.
Each group fails against the sweep commit ``3181882`` and passes once its fix lands
(spec FR-023, FR-024).

Offline: controlled generation, validation and storage outcomes only. The Feature-002
``doubles.py`` and Feature-003 ``workflow_doubles.py`` modules are imported read-only; any extra
double a group needs is defined locally in its own section. No merged test file is edited.
"""

import logging
from pathlib import Path

import pytest
import streamlit as st
from fastmcp import Client
from fastmcp.exceptions import ToolError
from streamlit.testing.v1 import AppTest

from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.models import ValidationOutcome
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    BriefingStoreUnavailableError,
)
from workflow_doubles import (
    FLAGGED,
    NOT_FLAGGED,
    UNKNOWN,
    CountingStore,
    PromptAwareGenerationProvider,
    ScriptedGenerationProvider,
    ScriptedValidator,
    build_mcp_server,
    build_rest_client,
    build_service,
    draft,
    failed,
    passed,
    rendered_log_output,
)

# ---- B2: validator exception escapes the retry workflow (register B2) ----


SERVICE_LOGGER = "student_attrition_risk.student_service"
B2_SECRET = "B2-VALIDATOR-INTERNAL-DETAIL"


class RaisingValidator:
    """``BriefingValidator`` double: each call consumes one scripted action, in order.

    An exception instance is raised (as the US-14 validator does on a NaN score, register D4); a
    ``ValidationOutcome`` is returned. Calling it more times than scripted is a test bug.
    """

    def __init__(self, *actions: ValidationOutcome | BaseException) -> None:
        self._actions: list[ValidationOutcome | BaseException] = list(actions)
        self.calls = 0

    def validate(self, draft_briefing, context) -> ValidationOutcome:
        self.calls += 1
        if not self._actions:
            raise AssertionError("RaisingValidator.validate called more times than scripted")
        action = self._actions.pop(0)
        if isinstance(action, BaseException):
            raise action
        return action


def _b2_service(*actions: ValidationOutcome | BaseException):
    gen = PromptAwareGenerationProvider()
    val = RaisingValidator(*actions)
    store = CountingStore()
    return build_service(generation=gen, validation=val, store=store), gen, val, store


def test_b2_attempt2_validator_exception_is_terminal_validation_failure():
    service, gen, val, store = _b2_service(
        failed(criteria=["PLACEHOLDER_CRITERION_A"]), ValueError(B2_SECRET)
    )

    with pytest.raises(BriefingNotProducedError) as excinfo:
        service.request_briefing(FLAGGED)

    assert excinfo.value.category == "validation"
    assert gen.calls == 2 and val.calls == 2
    assert store.saves == 0
    assert store.has_validated(FLAGGED) is False


def test_b2_attempt2_validator_exception_is_reported_as_briefing_failure_over_rest():
    service, _, _, store = _b2_service(failed(), ValueError(B2_SECRET))

    response = build_rest_client(service).post(f"/api/students/{FLAGGED}/briefing")

    assert response.status_code == 502
    assert response.json()["detail"] == "Briefing could not be produced (validation)"
    assert "data source unavailable" not in response.text.lower()
    assert B2_SECRET not in response.text
    assert store.saves == 0


def test_b2_attempt2_validator_exception_logs_one_metadata_only_terminal_outcome(caplog):
    service, _, _, _ = _b2_service(failed(), ValueError(B2_SECRET))

    with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
        with pytest.raises(BriefingNotProducedError):
            service.request_briefing(FLAGGED)

    workflow_lines = [
        r.getMessage() for r in caplog.records if r.getMessage().startswith("briefing_workflow")
    ]
    assert len(workflow_lines) == 1
    assert "outcome=terminal_validation" in workflow_lines[0]
    assert B2_SECRET not in rendered_log_output(caplog)


def test_b2_attempt1_validator_exception_proceeds_to_retry_with_original_prompt():
    service, gen, val, store = _b2_service(ValueError(B2_SECRET), passed())

    briefing = service.request_briefing(FLAGGED)

    assert briefing.attempt_count == 2
    assert briefing.storage_confirmed is True
    assert store.saves == 1
    assert gen.calls == 2 and val.calls == 2
    # No failed criteria and no feedback, so no revision block is appended (Feature-002 FR-010).
    assert gen.contexts[1].composed_prompt == gen.contexts[0].composed_prompt


@pytest.mark.parametrize(
    "actions",
    [
        (ConfigurationError("validation is not configured"),),
        (failed(), ConfigurationError("validation is not configured")),
    ],
    ids=["attempt1", "attempt2"],
)
def test_b2_validator_configuration_error_is_surfaced_unchanged(actions):
    service, _, _, store = _b2_service(*actions)

    with pytest.raises(ConfigurationError, match="validation is not configured"):
        service.request_briefing(FLAGGED)

    assert store.saves == 0








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


UI_PATH = str(Path(__file__).resolve().parent.parent / "src" / "student_attrition_risk" / "ui.py")


class _B1UnreadableStore(_UnreadableStore):
    """B1: every read fails with ``BriefingStorageError``; writes are recorded, never expected."""

    def __init__(self):
        self.saved = []

    def save_validated(self, briefing):
        self.saved.append(briefing)


def _b1_service(store=None):
    gen = ScriptedGenerationProvider(draft("B1 draft"))
    store = store if store is not None else _B1UnreadableStore()
    return build_service(generation=gen, validation=ScriptedValidator(passed()), store=store), gen, store


@pytest.mark.parametrize("regenerate", [False, True])
def test_b1_store_read_failure_raises_store_unavailable_without_generating(regenerate):
    service, gen, store = _b1_service()
    request = (
        service.has_stored_briefing if regenerate else service.request_briefing
    )

    with pytest.raises(BriefingStoreUnavailableError) as caught:
        request(FLAGGED)

    assert isinstance(caught.value, BriefingStorageError)  # existing handlers still catch it
    assert "/Volumes" not in str(caught.value)
    assert gen.calls == 0
    assert store.saved == []


def test_b1_store_read_failure_logs_one_store_unavailable_outcome(caplog):
    service, _, _ = _b1_service()

    with caplog.at_level(logging.INFO, logger=SERVICE_LOGGER):
        with pytest.raises(BriefingStoreUnavailableError):
            service.request_briefing(FLAGGED)

    lines = [r.getMessage() for r in caplog.records if r.name == SERVICE_LOGGER]
    assert len(lines) == 1
    assert "outcome=store_unavailable" in lines[0]
    assert "/Volumes" not in rendered_log_output(caplog)


def test_b1_rest_post_briefing_store_read_failure_is_store_unavailable():
    service, _, _ = _b1_service()

    response = build_rest_client(service).post(f"/api/students/{FLAGGED}/briefing")

    assert response.status_code == 503
    assert response.json()["detail"] == "Validated briefing store unavailable"


@pytest.mark.anyio
async def test_b1_generate_tool_store_read_failure_is_store_unavailable():
    service, _, _ = _b1_service()

    with pytest.raises(ToolError) as caught:
        await _c3_call(build_mcp_server(service), "generate_student_briefing", student_hash=FLAGGED)

    assert str(caught.value) == "validated briefing store unavailable"


@pytest.mark.anyio
async def test_b1_write_failure_is_still_could_not_be_stored():
    service, _, store = _b1_service(CountingStore(raise_on_save=True))

    response = build_rest_client(service).post(f"/api/students/{FLAGGED}/briefing")
    assert response.status_code == 503
    assert response.json()["detail"] == "Validated briefing could not be stored"

    service, _, store = _b1_service(CountingStore(raise_on_save=True))
    with pytest.raises(ToolError) as caught:
        await _c3_call(build_mcp_server(service), "generate_student_briefing", student_hash=FLAGGED)
    assert str(caught.value) == "validated briefing could not be stored"


@pytest.mark.parametrize("button", ["Generate Advisor Briefing", "Regenerate"])
def test_b1_ui_store_read_failure_shows_red_store_unavailable_notice(monkeypatch, button):
    service, gen, store = _b1_service()
    monkeypatch.setattr("student_attrition_risk.main.build_service", lambda *_a, **_kw: service)
    st.cache_resource.clear()
    at = AppTest.from_file(UI_PATH, default_timeout=10)
    at.run()
    at.text_input[0].set_value(FLAGGED).run()
    next(b for b in at.button if b.label == "Retrieve").click().run()

    next(b for b in at.button if b.label == button).click().run()

    notices = [el.value for el in at.markdown if 'class="store-error-notice"' in el.value]
    assert len(notices) == 1
    assert "Store unavailable" in notices[0]
    assert "Validated briefing store unavailable." in notices[0]
    rendered = [el.value for el in at.markdown] + [el.value for el in at.error]
    assert not any("could not be stored" in text for text in rendered)
    assert len(at.error) == 0
    assert gen.calls == 0
    assert store.saved == []
