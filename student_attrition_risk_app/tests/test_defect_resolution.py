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

import pytest

from student_attrition_risk.config import ConfigurationError
from student_attrition_risk.models import ValidationOutcome
from student_attrition_risk.student_service import BriefingNotProducedError
from workflow_doubles import (
    FLAGGED,
    CountingStore,
    PromptAwareGenerationProvider,
    build_rest_client,
    build_service,
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








# ---- B1: store read outage reported as "could not be stored" (register B1) ----







