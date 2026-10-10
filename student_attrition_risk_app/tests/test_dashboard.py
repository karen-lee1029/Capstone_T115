"""Tests for the Student Attrition Risk Overview Lakeview dashboard.

Tests the dashboard's derived-column logic (risk_level, risk_score_bucket,
student_id, risk_pct), validates the underlying prediction-table data
quality, and verifies the dashboard widget configuration.

The derived-column tests run against ``MockStudentRepository`` synthetic
data so no Databricks connection is required.  The data-quality tests query
the live ``workspace.student_aggregate.student_attrition_risk_prediction``
table and are skipped when no SQL warehouse is configured.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

from student_attrition_risk.student_repository import MockStudentRepository

# ---------------------------------------------------------------------------
# Dashboard constants -- mirrored from the .lvdash.json dataset config
# ---------------------------------------------------------------------------

PREDICTION_TABLE = "workspace.student_aggregate.student_attrition_risk_prediction"
RISK_LEVEL_THRESHOLD = 50  # attrition_risk_percentage >= 50 -> 'At Risk'

RISK_SCORE_BUCKETS = (
    (0, 46, "0-46%"),
    (46, 48, "46-48%"),
    (48, 49, "48-49%"),
    (49, 50, "49-50%"),
    (50, 51, "50-51%"),
    (51, 52, "51-52%"),
    (52, 54, "52-54%"),
    (54, float("inf"), "54-100%"),
)

EXPECTED_WIDGET_TITLES = {
    "Total Students",
    "At Risk",
    "Not At Risk",
    "Risk Level Distribution",
    "Risk Score Distribution",
    "Student Details",
    "Risk by Course Level",
    "Risk by Field of Education",
    "Risk by Age Band",
    "Risk by Gender",
    "Risk by Origin",
    "Filter by Risk Level",
}


# ---------------------------------------------------------------------------
# Derived-column logic -- Python replicas of the dashboard SQL expressions
# ---------------------------------------------------------------------------

def _risk_level(percentage: float) -> str:
    """Replicate CASE WHEN attrition_risk_percentage >= 50 THEN 'At Risk' ELSE 'Not At Risk' END."""
    return "At Risk" if percentage >= RISK_LEVEL_THRESHOLD else "Not At Risk"


def _risk_score_bucket(percentage: float) -> str:
    """Replicate the dashboard risk_score_bucket CASE expression."""
    for lower, upper, label in RISK_SCORE_BUCKETS:
        if lower <= percentage < upper:
            return label
    return RISK_SCORE_BUCKETS[-1][2]


STUDENT_ID_LENGTH = 16  # 8 characters let ~110 of ~974k students share an ID (US-28)


def _student_id(student_hash: str) -> str:
    """Replicate LEFT(student_deidentified_hash, 16)."""
    return student_hash[:STUDENT_ID_LENGTH]


def _risk_pct(percentage: float) -> float:
    """Replicate CAST(FLOOR(attrition_risk_percentage * 10) AS DOUBLE) / 10."""
    return math.floor(percentage * 10) / 10


# ---------------------------------------------------------------------------
# risk_level classification
# ---------------------------------------------------------------------------

class TestRiskLevelClassification:

    def test_high_risk(self):
        assert _risk_level(78.5) == "At Risk"

    def test_low_risk(self):
        assert _risk_level(18.0) == "Not At Risk"

    def test_boundary_at_threshold(self):
        assert _risk_level(50.0) == "At Risk"

    def test_just_below_threshold(self):
        assert _risk_level(49.9) == "Not At Risk"

    def test_mock_predictions_classify_correctly(self):
        repo = MockStudentRepository()
        for student_hash, prediction in repo.predictions.items():
            level = _risk_level(prediction.attrition_risk_percentage)
            if level == "At Risk":
                assert prediction.attrition_risk_flag, (
                    f"{student_hash} is At Risk "
                    f"({prediction.attrition_risk_percentage}%) "
                    "but attrition_risk_flag is False"
                )


# ---------------------------------------------------------------------------
# risk_score_bucket classification
# ---------------------------------------------------------------------------

class TestRiskScoreBucket:

    def test_lowest_bucket(self):
        assert _risk_score_bucket(0) == "0-46%"

    def test_boundary_46(self):
        assert _risk_score_bucket(46.0) == "46-48%"

    def test_boundary_50(self):
        assert _risk_score_bucket(50.0) == "50-51%"

    def test_just_below_54(self):
        assert _risk_score_bucket(53.9) == "52-54%"

    def test_highest_bucket(self):
        assert _risk_score_bucket(78.5) == "54-100%"

    def test_all_integers_covered(self):
        """Every integer percentage 0-100 must map to a known bucket."""
        valid = {b[2] for b in RISK_SCORE_BUCKETS}
        for pct in range(0, 101):
            assert _risk_score_bucket(float(pct)) in valid


# ---------------------------------------------------------------------------
# student_id truncation
# ---------------------------------------------------------------------------

class TestStudentIdTruncation:

    def test_truncates_to_16_chars(self):
        assert _student_id("synthetic-student-001") == "synthetic-studen"

    def test_short_hash_returns_full(self):
        assert _student_id("abc") == "abc"

    def test_mock_hashes_truncate_correctly(self):
        repo = MockStudentRepository()
        for h in repo.predictions:
            assert len(_student_id(h)) <= STUDENT_ID_LENGTH


# ---------------------------------------------------------------------------
# risk_pct rounding
# ---------------------------------------------------------------------------

class TestRiskPctRounding:

    def test_rounds_to_1_decimal(self):
        assert _risk_pct(78.54) == 78.5

    def test_already_one_decimal(self):
        assert _risk_pct(18.0) == 18.0

    def test_truncates_down(self):
        assert _risk_pct(49.99) == 49.9


# ---------------------------------------------------------------------------
# Data-quality tests against the live prediction table (skipped without SQL)
# ---------------------------------------------------------------------------

def _can_connect_to_warehouse() -> bool:
    """Check whether a SQL warehouse connection is configured."""
    try:
        from student_attrition_risk.config import Settings

        settings = Settings.from_env()
        return bool(settings.databricks_warehouse_id and settings.databricks_host)
    except Exception:
        return False


_sql_skip = pytest.mark.skipif(
    not _can_connect_to_warehouse(),
    reason="DATABRICKS_WAREHOUSE_ID and DATABRICKS_HOST not set",
)


@_sql_skip
class TestPredictionDataQuality:
    """Data-quality tests against the prediction table."""

    def _query(self, sql: str) -> list[dict]:
        from student_attrition_risk.config import Settings
        from student_attrition_risk.databricks_client import create_sql_connection

        settings = Settings.from_env()
        conn = create_sql_connection(settings)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                columns = [c[0] for c in cursor.description]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def test_table_has_data(self):
        rows = self._query(f"SELECT COUNT(*) AS cnt FROM {PREDICTION_TABLE}")
        assert rows[0]["cnt"] > 0, "Prediction table should contain at least one row"

    def test_risk_percentages_in_valid_range(self):
        rows = self._query(
            f"SELECT MIN(attrition_risk_percentage) AS min_pct,"
            f" MAX(attrition_risk_percentage) AS max_pct"
            f" FROM {PREDICTION_TABLE}"
        )
        assert 0 <= rows[0]["min_pct"] <= 100
        assert 0 <= rows[0]["max_pct"] <= 100

    def test_prediction_thresholds_in_valid_range(self):
        rows = self._query(
            f"SELECT MIN(prediction_threshold) AS min_t,"
            f" MAX(prediction_threshold) AS max_t"
            f" FROM {PREDICTION_TABLE}"
        )
        assert 0 <= rows[0]["min_t"] <= 1
        assert 0 <= rows[0]["max_t"] <= 1

    def test_no_null_student_hashes(self):
        rows = self._query(
            f"SELECT COUNT(*) AS cnt FROM {PREDICTION_TABLE}"
            f" WHERE student_deidentified_hash IS NULL"
        )
        assert rows[0]["cnt"] == 0, "student_deidentified_hash must never be NULL"

    def test_student_hashes_are_unique(self):
        rows = self._query(
            f"SELECT COUNT(DISTINCT student_deidentified_hash) AS distinct_cnt,"
            f" COUNT(*) AS total_cnt"
            f" FROM {PREDICTION_TABLE}"
        )
        assert rows[0]["distinct_cnt"] == rows[0]["total_cnt"], (
            "student_deidentified_hash should be unique"
        )

    def test_dashboard_student_ids_are_unique(self):
        """The dashboard's truncated Student ID must still identify one student."""
        rows = self._query(
            f"SELECT COUNT(DISTINCT LEFT(student_deidentified_hash, {STUDENT_ID_LENGTH})) AS distinct_cnt,"
            f" COUNT(*) AS total_cnt"
            f" FROM {PREDICTION_TABLE}"
        )
        assert rows[0]["distinct_cnt"] == rows[0]["total_cnt"], (
            f"LEFT(student_deidentified_hash, {STUDENT_ID_LENGTH}) should be unique"
        )

    def test_risk_flag_consistent_with_model_threshold(self):
        """Flagged students must have percentage >= their prediction threshold."""
        rows = self._query(
            f"SELECT COUNT(*) AS inconsistent FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_flag = true"
            f" AND attrition_risk_percentage < (prediction_threshold * 100)"
        )
        assert rows[0]["inconsistent"] == 0

    def test_dashboard_high_risk_count_matches_threshold(self):
        """Dashboard counts At Risk as percentage >= 50; verify non-zero."""
        rows = self._query(
            f"SELECT COUNT(DISTINCT student_deidentified_hash) AS at_risk_cnt"
            f" FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_percentage >= {RISK_LEVEL_THRESHOLD}"
        )
        assert rows[0]["at_risk_cnt"] > 0, "Should have at least one At Risk student"

    def test_dashboard_low_risk_count_matches_threshold(self):
        rows = self._query(
            f"SELECT COUNT(DISTINCT student_deidentified_hash) AS not_at_risk_cnt"
            f" FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_percentage < {RISK_LEVEL_THRESHOLD}"
        )
        assert rows[0]["not_at_risk_cnt"] > 0, "Should have at least one Not At Risk student"

    def test_total_count_equals_high_plus_low(self):
        """Dashboard Total Students counter should equal At Risk + Not At Risk."""
        rows = self._query(
            f"SELECT"
            f" COUNT(DISTINCT student_deidentified_hash) AS total,"
            f" COUNT(DISTINCT CASE WHEN attrition_risk_percentage >= {RISK_LEVEL_THRESHOLD}"
            f" THEN student_deidentified_hash END) AS at_risk,"
            f" COUNT(DISTINCT CASE WHEN attrition_risk_percentage < {RISK_LEVEL_THRESHOLD}"
            f" THEN student_deidentified_hash END) AS not_at_risk"
            f" FROM {PREDICTION_TABLE}"
        )
        assert rows[0]["total"] == rows[0]["at_risk"] + rows[0]["not_at_risk"]


# ---------------------------------------------------------------------------
# Dashboard widget configuration tests
# ---------------------------------------------------------------------------

class TestDashboardWidgets:
    """Verify the dashboard widget set matches expectations."""

    DASHBOARD_PATH = (
        "/Users/t115.capstone2026@outlook.com/"
        "Student Attrition Risk Overview.lvdash.json"
    )

    def _load_dashboard(self):
        import json

        try:
            from databricks.sdk import WorkspaceClient

            client = WorkspaceClient()
            return json.loads(
                client.files.download(self.DASHBOARD_PATH).contents.read().decode()
            )
        except Exception:
            pytest.skip("Dashboard file is not accessible from this workspace")

    def test_all_expected_widgets_present(self):
        dash = self._load_dashboard()
        titles = set()
        for page in dash.get("pages", []):
            for item in page.get("layout", []):
                widget = item.get("widget", item)
                spec = widget.get("spec", {})
                frame = spec.get("frame", {})
                title = frame.get("title", {})
                if isinstance(title, dict) and title.get("value"):
                    titles.add(title["value"])
        missing = EXPECTED_WIDGET_TITLES - titles
        assert not missing, f"Missing expected widget titles: {missing}"

    def test_has_two_datasets(self):
        dash = self._load_dashboard()
        datasets = dash.get("datasets", [])
        assert len(datasets) == 2

    def test_prediction_dataset_source_table(self):
        dash = self._load_dashboard()
        pred_ds = next(
            (
                d for d in dash["datasets"]
                if d["displayName"] == "student_attrition_risk_prediction"
            ),
            None,
        )
        assert pred_ds is not None, "Prediction dataset not found"
        config = pred_ds.get("config", {})
        # US-29 Q25: the source is now a query over the prediction table that joins in the
        # enrolment filter fields; it must still read from the prediction table.
        assert f"FROM {PREDICTION_TABLE} p" in config.get("source", "")

    def test_has_one_page_named_overview(self):
        dash = self._load_dashboard()
        pages = dash.get("pages", [])
        assert len(pages) == 1
        assert pages[0]["displayName"] == "Overview"


# ---------------------------------------------------------------------------
# Repository dashboard definition -- Feature-005 / US-28 visual contract
# (specs/005-enhanced-risk-visualisation/contracts/dashboard-visual-contract.md)
# ---------------------------------------------------------------------------

REPO_DASHBOARD_PATH = (
    Path(__file__).resolve().parent.parent
    / "dashboard"
    / "Student Attrition Risk Overview.lvdash.json"
)

RISK_COLOUR_MAPPINGS = [
    {"color": "#1565C0", "value": "At Risk"},
    {"color": "#42A5F5", "value": "Not At Risk"},
]

# Widget names follow the four-page layout introduced by US-27 (commit 946aab0). US-27 (commit
# 3fc0a9f) moved Risk by Gender onto Demographic Breakdown as dfe9d497, unchanged apart from its name.
CHART_DESCRIPTIONS = {
    "5e91fa54": (
        "Number of students in each risk category: At Risk (50% or higher) "
        "and Not At Risk (below 50%)"
    ),
    "329be35e": (
        "Number of students in each attrition risk score range, lowest to highest; "
        "ranges from 50% are At Risk"
    ),
    "028257ed": "At Risk and Not At Risk student counts for each course level",
    "90548010": "At Risk and Not At Risk student counts for each broad field of education",
    "eaf7eaf4": "At Risk and Not At Risk student counts for each age band",
    "dfe9d497": "At Risk and Not At Risk student counts for each gender",
    "292bc630": (
        "At Risk and Not At Risk student counts for domestic and international students"
    ),
}

# Chart widget name -> categorical axis that carries the natural-order sort.
CHART_CATEGORICAL_AXIS = {
    "5e91fa54": "y",
    "329be35e": "x",
    "028257ed": "y",
    "90548010": "y",
    "eaf7eaf4": "y",
    "dfe9d497": "y",
    "292bc630": "y",
}

COUNTER_CONTRACT = {
    "counter_high": ("At Risk", "#1565C0"),
    "counter_low": ("Not At Risk", "#42A5F5"),
}

LEGACY_CATEGORY_PATTERN = re.compile(r"\b(?:High|Low|Medium)\b")


def _load_repo_dashboard() -> dict:
    return json.loads(REPO_DASHBOARD_PATH.read_text(encoding="utf-8"))


def _layout_items(dash: dict) -> list[dict]:
    return [item for page in dash.get("pages", []) for item in page.get("layout", [])]


def _widget(dash: dict, name: str) -> dict:
    for item in _layout_items(dash):
        if item["widget"]["name"] == name:
            return item["widget"]
    raise AssertionError(f"Widget {name!r} not found in the dashboard definition")


def _dimension_expr(dash: dict, name: str) -> str:
    for dataset in dash["datasets"]:
        for dim in dataset["config"].get("dimensions", []):
            if dim.get("name") == name:
                return dim["expr"]
    raise AssertionError(f"Dimension {name!r} not found in the dashboard definition")


def _widget_title(widget: dict) -> str | None:
    title = widget.get("spec", {}).get("frame", {}).get("title")
    if isinstance(title, dict):
        return title.get("value")
    return title


class TestRepositoryDashboardDefinition:
    """Offline checks of the committed dashboard JSON against the US-28 contract."""

    def test_risk_level_dimension_uses_new_categories(self):
        expr = _dimension_expr(_load_repo_dashboard(), "risk_level")
        assert f">= {RISK_LEVEL_THRESHOLD}" in expr
        assert "THEN 'At Risk'" in expr
        assert "ELSE 'Not At Risk'" in expr

    def test_student_id_dimension_shows_16_characters(self):
        expr = _dimension_expr(_load_repo_dashboard(), "student_id")
        assert expr == f"LEFT(source.student_deidentified_hash, {STUDENT_ID_LENGTH})"

    def test_student_id_is_labelled_de_identified(self):
        raw = REPO_DASHBOARD_PATH.read_text(encoding="utf-8")
        # The dimension, the Student Details table and the Overview "Students in this view" table
        # (US-27, commit 3fc0a9f, kept only the Overview one of the three US-29 tables).
        assert raw.count('"displayName": "Student ID (de-identified)"') == 3
        assert '"displayName": "Student ID"' not in raw

    def test_no_legacy_category_text(self):
        raw = REPO_DASHBOARD_PATH.read_text(encoding="utf-8")
        found = LEGACY_CATEGORY_PATTERN.findall(raw)
        assert not found, f"Legacy risk category text found: {found}"

    @pytest.mark.parametrize("name", sorted(COUNTER_CONTRACT))
    def test_counter_title_filter_and_colour(self, name):
        label, colour = COUNTER_CONTRACT[name]
        widget = _widget(_load_repo_dashboard(), name)
        assert _widget_title(widget) == label
        filters = [f["expression"] for q in widget["queries"] for f in q["query"]["filters"]]
        assert filters == [f"`student_attrition_risk_prediction`.`risk_level` IN ('{label}')"]
        assert widget["spec"]["style"]["fontColor"] == {"dark": colour, "light": colour}

    @pytest.mark.parametrize("name", sorted(CHART_CATEGORICAL_AXIS))
    def test_chart_colour_map_matches_contract(self, name):
        widget = _widget(_load_repo_dashboard(), name)
        assert widget["spec"]["widgetType"] == "bar"
        assert widget["spec"]["encodings"]["color"]["scale"]["mappings"] == RISK_COLOUR_MAPPINGS

    def test_every_bar_chart_is_in_contract(self):
        bars = {
            item["widget"]["name"]
            for item in _layout_items(_load_repo_dashboard())
            if item["widget"].get("spec", {}).get("widgetType") == "bar"
        }
        assert bars == set(CHART_CATEGORICAL_AXIS)

    @pytest.mark.parametrize("name", sorted(CHART_CATEGORICAL_AXIS))
    def test_chart_categorical_axis_natural_order(self, name):
        axis = CHART_CATEGORICAL_AXIS[name]
        scale = _widget(_load_repo_dashboard(), name)["spec"]["encodings"][axis]["scale"]
        assert scale["type"] == "categorical"
        assert scale.get("sort") == {"by": "natural-order"}

    def test_score_buckets_ascending_with_percent_labels(self):
        expr = _dimension_expr(_load_repo_dashboard(), "risk_score_bucket")
        labels = re.findall(r"'([^']+)'", expr)
        expected = [b[2] for b in RISK_SCORE_BUCKETS]
        assert labels == expected
        assert sorted(labels) == expected
        assert all(label.endswith("%") for label in labels)

    @pytest.mark.parametrize("name", sorted(CHART_DESCRIPTIONS))
    def test_chart_description_shown(self, name):
        frame = _widget(_load_repo_dashboard(), name)["spec"]["frame"]
        assert frame["showDescription"] is True
        assert frame["description"] == {"value": CHART_DESCRIPTIONS[name], "fields": []}

    def test_how_to_read_widget_content(self):
        widget = _widget(_load_repo_dashboard(), "how_to_read")
        text = "".join(widget["multilineTextboxSpec"]["lines"])
        for required in (
            "How to read this dashboard", "At Risk", "Not At Risk", "50%", "#1565C0", "#42A5F5",
        ):
            assert required in text, f"how_to_read is missing {required!r}"

    def test_how_to_read_position(self):
        dash = _load_repo_dashboard()
        item = next(i for i in _layout_items(dash) if i["widget"]["name"] == "how_to_read")
        assert item["position"] == {"x": 0, "y": 2, "width": 12, "height": 3}

    def test_all_expected_widget_titles_present(self):
        titles = {_widget_title(item["widget"]) for item in _layout_items(_load_repo_dashboard())}
        missing = EXPECTED_WIDGET_TITLES - titles
        assert not missing, f"Missing expected widget titles: {missing}"

    def test_layout_has_no_overlapping_widgets(self):
        for page in _load_repo_dashboard().get("pages", []):
            cells: dict[tuple[int, int], str] = {}
            for item in page.get("layout", []):
                pos, name = item["position"], item["widget"]["name"]
                for x in range(pos["x"], pos["x"] + pos["width"]):
                    for y in range(pos["y"], pos["y"] + pos["height"]):
                        assert (x, y) not in cells, f"{name} overlaps {cells[(x, y)]} at {(x, y)}"
                        cells[(x, y)] = name
