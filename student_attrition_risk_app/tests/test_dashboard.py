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

import pytest

from student_attrition_risk.student_repository import MockStudentRepository

# ---------------------------------------------------------------------------
# Dashboard constants -- mirrored from the .lvdash.json dataset config
# ---------------------------------------------------------------------------

PREDICTION_TABLE = "workspace.student_aggregate.student_attrition_risk_prediction"
RISK_LEVEL_THRESHOLD = 50  # attrition_risk_percentage >= 50 -> 'High'

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
    "High Risk",
    "Low Risk",
    "Risk Level Distribution",
    "Risk Score Distribution",
    "Student Details",
    "Risk by Age Band",
    "Risk by Gender",
    "Risk by Origin",
    "Filter by Risk Level",
    "Filter by Risk Flag",
    "Search Student",
}


# ---------------------------------------------------------------------------
# Derived-column logic -- Python replicas of the dashboard SQL expressions
# ---------------------------------------------------------------------------

def _risk_level(percentage: float) -> str:
    """Replicate CASE WHEN attrition_risk_percentage >= 50 THEN 'High' ELSE 'Low' END."""
    return "High" if percentage >= RISK_LEVEL_THRESHOLD else "Low"


def _risk_score_bucket(percentage: float) -> str:
    """Replicate the dashboard risk_score_bucket CASE expression."""
    for lower, upper, label in RISK_SCORE_BUCKETS:
        if lower <= percentage < upper:
            return label
    return RISK_SCORE_BUCKETS[-1][2]


def _student_id(student_hash: str) -> str:
    """Replicate LEFT(student_deidentified_hash, 8)."""
    return student_hash[:8]


def _risk_pct(percentage: float) -> float:
    """Replicate ROUND(attrition_risk_percentage, 1)."""
    return round(percentage, 1)


# ---------------------------------------------------------------------------
# risk_level classification
# ---------------------------------------------------------------------------

class TestRiskLevelClassification:

    def test_high_risk(self):
        assert _risk_level(78.5) == "High"

    def test_low_risk(self):
        assert _risk_level(18.0) == "Low"

    def test_boundary_at_threshold(self):
        assert _risk_level(50.0) == "High"

    def test_just_below_threshold(self):
        assert _risk_level(49.9) == "Low"

    def test_mock_predictions_classify_correctly(self):
        repo = MockStudentRepository()
        for student_hash, prediction in repo.predictions.items():
            level = _risk_level(prediction.attrition_risk_percentage)
            if level == "High":
                assert prediction.attrition_risk_flag, (
                    f"{student_hash} is High Risk "
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

    def test_truncates_to_8_chars(self):
        assert _student_id("synthetic-student-001") == "syntheti"

    def test_short_hash_returns_full(self):
        assert _student_id("abc") == "abc"

    def test_mock_hashes_truncate_correctly(self):
        repo = MockStudentRepository()
        for h in repo.predictions:
            assert len(_student_id(h)) <= 8


# ---------------------------------------------------------------------------
# risk_pct rounding
# ---------------------------------------------------------------------------

class TestRiskPctRounding:

    def test_rounds_to_1_decimal(self):
        assert _risk_pct(78.54) == 78.5

    def test_already_one_decimal(self):
        assert _risk_pct(18.0) == 18.0

    def test_rounds_up(self):
        assert _risk_pct(64.06) == 64.1


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

    def test_risk_flag_consistent_with_model_threshold(self):
        """Flagged students must have percentage >= their prediction threshold."""
        rows = self._query(
            f"SELECT COUNT(*) AS inconsistent FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_flag = true"
            f" AND attrition_risk_percentage < (prediction_threshold * 100)"
        )
        assert rows[0]["inconsistent"] == 0

    def test_dashboard_high_risk_count_matches_threshold(self):
        """Dashboard counts High Risk as percentage >= 50; verify non-zero."""
        rows = self._query(
            f"SELECT COUNT(DISTINCT student_deidentified_hash) AS high_risk_cnt"
            f" FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_percentage >= {RISK_LEVEL_THRESHOLD}"
        )
        assert rows[0]["high_risk_cnt"] > 0, "Should have at least one High Risk student"

    def test_dashboard_low_risk_count_matches_threshold(self):
        rows = self._query(
            f"SELECT COUNT(DISTINCT student_deidentified_hash) AS low_risk_cnt"
            f" FROM {PREDICTION_TABLE}"
            f" WHERE attrition_risk_percentage < {RISK_LEVEL_THRESHOLD}"
        )
        assert rows[0]["low_risk_cnt"] > 0, "Should have at least one Low Risk student"

    def test_total_count_equals_high_plus_low(self):
        """Dashboard Total Students counter should equal High + Low."""
        rows = self._query(
            f"SELECT"
            f" COUNT(DISTINCT student_deidentified_hash) AS total,"
            f" COUNT(DISTINCT CASE WHEN attrition_risk_percentage >= {RISK_LEVEL_THRESHOLD}"
            f" THEN student_deidentified_hash END) AS high,"
            f" COUNT(DISTINCT CASE WHEN attrition_risk_percentage < {RISK_LEVEL_THRESHOLD}"
            f" THEN student_deidentified_hash END) AS low"
            f" FROM {PREDICTION_TABLE}"
        )
        assert rows[0]["total"] == rows[0]["high"] + rows[0]["low"]


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
        assert config.get("source") == PREDICTION_TABLE

    def test_has_one_page_named_overview(self):
        dash = self._load_dashboard()
        pages = dash.get("pages", [])
        assert len(pages) == 1
        assert pages[0]["displayName"] == "Overview"
