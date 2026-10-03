"""Feature-005 (US-28) follow-up — the student summary card's left edge follows the risk category.

The red summary-card edge sat beside the blue badge and score ring after Feature-005. The edge now
uses the dashboard's category blues: ``#1565C0`` for At Risk and ``#42A5F5`` for Not At Risk
(``specs/005-enhanced-risk-visualisation/contracts/dashboard-visual-contract.md`` § 7b).

Offline: the page runs under ``AppTest`` with a local minimal service fake on
``MockStudentRepository``. No merged test file is imported or edited.
"""

import re
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from student_attrition_risk.models import StudentRiskProfile
from student_attrition_risk.student_repository import MockStudentRepository

UI_PATH = str(Path(__file__).resolve().parent.parent / "src" / "student_attrition_risk" / "ui.py")

HASH_AT_RISK = "synthetic-student-001"
HASH_NOT_AT_RISK = "synthetic-student-002"

AT_RISK_EDGE = "#1565C0"
NOT_AT_RISK_EDGE = "#42A5F5"


class _ProfileOnlyService:
    """Minimal service fake: profiles from ``MockStudentRepository``; no stored briefing."""

    def __init__(self) -> None:
        self._repository = MockStudentRepository()

    def get_student_profile(self, student_hash):
        return StudentRiskProfile(
            prediction=self._repository.get_prediction(student_hash),
            snapshot=self._repository.get_snapshot(student_hash),
        )

    def has_stored_briefing(self, student_hash):
        return False

    def get_stored_briefing(self, student_hash):
        return None


@pytest.fixture
def loaded_page(monkeypatch):
    """Factory: render the page and load ``student_hash`` through the Retrieve button."""

    def _load(student_hash):
        service = _ProfileOnlyService()
        monkeypatch.setattr("student_attrition_risk.main.build_service", lambda *_a, **_kw: service)
        st.cache_resource.clear()
        at = AppTest.from_file(UI_PATH, default_timeout=10)
        at.run()
        at.text_input[0].set_value(student_hash).run()
        next(b for b in at.button if b.label == "Retrieve").click().run()
        assert not at.exception
        return at

    return _load


def _css_rule(css: str, selector: str) -> dict[str, str]:
    match = re.search(rf"(?<![\w.-])\.{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
    assert match, f"No .{selector} rule in the page style"
    declarations = {}
    for declaration in match.group(1).split(";"):
        if ":" in declaration:
            name, value = declaration.split(":", 1)
            declarations[name.strip().lower()] = value.strip()
    return declarations


def _page_css(at) -> str:
    styles = [el.value for el in at.markdown if "<style>" in el.value and ".summary-card" in el.value]
    assert styles, "No <style> markdown containing .summary-card was rendered"
    return styles[0]


@pytest.mark.parametrize(
    ("student_hash", "card_class"),
    [
        (HASH_AT_RISK, "summary-card"),
        (HASH_NOT_AT_RISK, "summary-card not-risk-card"),
    ],
)
def test_summary_card_uses_category_class(loaded_page, student_hash, card_class):
    at = loaded_page(student_hash)

    assert any(f'<div class="{card_class}">' in el.value for el in at.markdown), (
        f'No <div class="{card_class}"> wrapping the student summary'
    )


def test_summary_card_edge_uses_dashboard_blues(loaded_page):
    css = _page_css(loaded_page(HASH_AT_RISK))

    at_risk_edge = _css_rule(css, "summary-card")["border-left"].split()[-1]
    not_at_risk_edge = _css_rule(css, "summary-card.not-risk-card")["border-left-color"]
    assert at_risk_edge.upper() == AT_RISK_EDGE
    assert not_at_risk_edge.upper() == NOT_AT_RISK_EDGE
