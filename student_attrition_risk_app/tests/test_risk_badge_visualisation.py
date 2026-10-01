"""Feature-005 (US-28) — advisor page risk badge and score circle match the dashboard.

Checks the Track C change described in
``specs/005-enhanced-risk-visualisation/contracts/dashboard-visual-contract.md`` § 7: the
``.risk-badge`` / ``.not-risk-badge`` rules and the relative-risk score circle
(``.risk-circle`` / ``.risk-circle.not-risk-circle``) use the dashboard's category blues, keep
text contrast of at least 4.5:1 (WCAG 2.x), and stay page-owned markup with no Streamlit alert
widget. A last check compares the badge colours with the repository dashboard's colour maps,
accepting either the original ``High`` / ``Low`` labels or the renamed ``At Risk`` /
``Not At Risk`` labels, so it holds before and after the dashboard rename (Track B).

Offline: the page runs under ``AppTest`` with a local minimal service fake on
``MockStudentRepository``. No merged test file is imported or edited.
"""

import json
import re
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from student_attrition_risk.models import StudentRiskProfile
from student_attrition_risk.student_repository import MockStudentRepository

APP_ROOT = Path(__file__).resolve().parent.parent
UI_PATH = str(APP_ROOT / "src" / "student_attrition_risk" / "ui.py")
DASHBOARD_PATH = APP_ROOT / "dashboard" / "Student Attrition Risk Overview.lvdash.json"

HASH_AT_RISK = "synthetic-student-001"
HASH_NOT_AT_RISK = "synthetic-student-002"

# Contract § 7: (background, text colour) per badge rule.
AT_RISK_BACKGROUND = "#1565C0"
AT_RISK_TEXT = "#FFFFFF"
NOT_AT_RISK_BACKGROUND = "#42A5F5"
NOT_AT_RISK_TEXT = "#172033"

EXPECTED_BADGE_COLOURS = {
    "risk-badge": (AT_RISK_BACKGROUND, AT_RISK_TEXT),
    "not-risk-badge": (NOT_AT_RISK_BACKGROUND, NOT_AT_RISK_TEXT),
}

# Score circle stays a ring on a white fill: selector -> (ring border colour, text colour).
CIRCLE_FILL = "WHITE"
EXPECTED_CIRCLE_COLOURS = {
    "risk-circle": (AT_RISK_BACKGROUND, AT_RISK_BACKGROUND),
    "risk-circle.not-risk-circle": (NOT_AT_RISK_BACKGROUND, NOT_AT_RISK_TEXT),
}

MIN_CONTRAST = 4.5

# Dashboard category label -> badge rule. Old labels apply before the Track B rename.
DASHBOARD_LABEL_TO_BADGE = {
    "At Risk": "risk-badge",
    "Not At Risk": "not-risk-badge",
    "High": "risk-badge",
    "Low": "not-risk-badge",
}


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


def _css_rule(css: str, class_name: str) -> dict[str, str]:
    """Declarations of the first top-level-looking ``.<class_name> { ... }`` rule in ``css``."""
    match = re.search(rf"(?<![\w.-])\.{re.escape(class_name)}\s*\{{([^}}]*)\}}", css)
    assert match, f"No .{class_name} rule in the page style"
    declarations = {}
    for declaration in match.group(1).split(";"):
        if ":" in declaration:
            name, value = declaration.split(":", 1)
            declarations[name.strip().lower()] = value.strip()
    return declarations


def _page_css(at) -> str:
    styles = [el.value for el in at.markdown if "<style>" in el.value and ".risk-badge" in el.value]
    assert styles, "No <style> markdown containing .risk-badge was rendered"
    return styles[0]


def _relative_luminance(hex_colour: str) -> float:
    value = hex_colour.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _dashboard_colour_mappings(node):
    """Yield every ``{"color": ..., "value": ...}`` mapping in the dashboard definition."""
    if isinstance(node, dict):
        if isinstance(node.get("color"), str) and isinstance(node.get("value"), str):
            yield node
        for child in node.values():
            yield from _dashboard_colour_mappings(child)
    elif isinstance(node, list):
        for child in node:
            yield from _dashboard_colour_mappings(child)


@pytest.mark.parametrize(
    ("student_hash", "badge_class", "label"),
    [
        (HASH_AT_RISK, "risk-badge", "At Risk"),
        (HASH_NOT_AT_RISK, "not-risk-badge", "Not At Risk"),
    ],
)
def test_badge_span_wraps_label_without_alert_widgets(loaded_page, student_hash, badge_class, label):
    at = loaded_page(student_hash)

    pattern = re.compile(rf'<span class="{badge_class}">\s*{re.escape(label)}\s*</span>')
    assert any(pattern.search(el.value) for el in at.markdown), (
        f'No <span class="{badge_class}"> wrapping "{label}" in the student summary'
    )
    assert len(at.info) == 0
    assert len(at.success) == 0
    assert len(at.warning) == 0


def test_badge_css_uses_dashboard_blues_and_contract_text_colours(loaded_page):
    css = _page_css(loaded_page(HASH_AT_RISK))

    for badge_class, (background, text) in EXPECTED_BADGE_COLOURS.items():
        rule = _css_rule(css, badge_class)
        assert rule.get("background", "").upper() == background, badge_class
        assert rule.get("color", "").upper() == text, badge_class


@pytest.mark.parametrize("badge_class", sorted(EXPECTED_BADGE_COLOURS))
def test_badge_text_contrast_is_at_least_4_5(loaded_page, badge_class):
    rule = _css_rule(_page_css(loaded_page(HASH_AT_RISK)), badge_class)

    ratio = _contrast_ratio(rule["color"], rule["background"])
    assert ratio >= MIN_CONTRAST, f".{badge_class} contrast {ratio:.2f}:1 is below {MIN_CONTRAST}:1"


def test_badge_backgrounds_match_dashboard_colour_maps():
    definition = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    mappings = [
        m for m in _dashboard_colour_mappings(definition) if m["value"] in DASHBOARD_LABEL_TO_BADGE
    ]
    if not mappings:
        pytest.skip("Dashboard has no At Risk / Not At Risk (or High / Low) colour mappings")

    for mapping in mappings:
        expected_background = EXPECTED_BADGE_COLOURS[DASHBOARD_LABEL_TO_BADGE[mapping["value"]]][0]
        assert mapping["color"].upper() == expected_background, (
            f"Dashboard colour for {mapping['value']!r} is {mapping['color']}, "
            f"badge background is {expected_background}"
        )


@pytest.mark.parametrize(
    ("student_hash", "circle_class"),
    [
        (HASH_AT_RISK, "risk-circle"),
        (HASH_NOT_AT_RISK, "risk-circle not-risk-circle"),
    ],
)
def test_score_circle_uses_category_class(loaded_page, student_hash, circle_class):
    at = loaded_page(student_hash)

    pattern = re.compile(rf'<div class="{circle_class}">\s*[\d.]+%\s*</div>')
    assert any(pattern.search(el.value) for el in at.markdown), (
        f'No <div class="{circle_class}"> holding the relative risk score'
    )


def test_score_circle_is_a_white_ring_in_dashboard_blues(loaded_page):
    css = _page_css(loaded_page(HASH_AT_RISK))

    assert _css_rule(css, "risk-circle").get("background", "").upper() == CIRCLE_FILL
    for selector, (border_colour, text) in EXPECTED_CIRCLE_COLOURS.items():
        rule = _css_rule(css, selector)
        border = rule.get("border-color") or rule.get("border", "").split()[-1]
        assert "background" not in rule or rule["background"].upper() == CIRCLE_FILL, selector
        assert border.upper() == border_colour, selector
        assert rule.get("color", "").upper() == text, selector


@pytest.mark.parametrize("selector", sorted(EXPECTED_CIRCLE_COLOURS))
def test_score_circle_text_contrast_is_at_least_4_5(loaded_page, selector):
    rule = _css_rule(_page_css(loaded_page(HASH_AT_RISK)), selector)

    ratio = _contrast_ratio(rule["color"], "#FFFFFF")
    assert ratio >= MIN_CONTRAST, f".{selector} contrast {ratio:.2f}:1 is below {MIN_CONTRAST}:1"
