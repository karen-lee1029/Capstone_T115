"""Student repository adapters."""

from typing import Any

from .config import Settings
from .databricks_client import create_sql_connection
from .models import UNAVAILABLE, ApprovedModelFeatureValues, StudentPrediction, StudentSnapshot

SNAPSHOT_COLUMNS = (
    "age_at_census",
    "attendance_mode",
    "eftsl",
    "commencing_continuing",
    "commencing_continuing_period",
    "course_admission_load_category",
    "enrolment_year",
    "cumulative_credit_points_enrolled",
    "cumulative_credit_points_passed",
    "cumulative_credit_points_failed",
    "cumulative_credit_points_withdrawn",
)

# The 21 approved machine-learning model features (research.md R1). This is the ONLY place
# the feature list and the source-table joins live (accepted risk TR-1). Raw approved values
# are read only — no encoding, imputation, or other ML transformation. A future canonical
# ML feature-projection table can replace the join behind this same repository seam.
_FACT_FEATURE_COLUMNS = (
    "age_at_census",
    "socioeconomic_status",
    "regional_remote_status",
    "student_gender",
    "student_is_international_student",
    "student_is_first_nations_student",
    "attendance_mode",
    "eftsl",
    "commencing_continuing",
    "commencing_continuing_period",
    "course_admission_load_category",
    "enrolment_year",
    "cumulative_credit_points_enrolled",
    "cumulative_credit_points_passed",
    "cumulative_credit_points_failed",
    "cumulative_credit_points_withdrawn",
)
_COURSE_FEATURE_COLUMNS = (
    "course_group",
    "broad_primary_field_of_education",
    "narrow_primary_field_of_education",
    "detailed_primary_field_of_education",
)
_TEACHING_PERIOD_FEATURE_COLUMNS = ("teaching_period",)
MODEL_FEATURE_COLUMNS = (
    _FACT_FEATURE_COLUMNS + _COURSE_FEATURE_COLUMNS + _TEACHING_PERIOD_FEATURE_COLUMNS
)


def _rows(cursor: Any) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description or []]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


class DatabricksStudentRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _query(self, statement: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        connection = create_sql_connection(self.settings)
        try:
            with connection.cursor() as cursor:
                cursor.execute(statement, parameters)
                return _rows(cursor)
        finally:
            connection.close()

    def _available_columns(self, table_fqn: str, candidates: tuple[str, ...]) -> list[str]:
        catalog, schema, table = table_fqn.split(".")
        rows = self._query(
            f"""SELECT column_name FROM {catalog}.information_schema.columns
                WHERE table_schema = ? AND table_name = ?""",
            (schema, table),
        )
        present = {row["column_name"] for row in rows}
        return [column for column in candidates if column in present]

    def get_prediction(self, student_hash: str) -> StudentPrediction | None:
        statement = f"""
            SELECT student_deidentified_hash, attrition_risk_percentage,
                   attrition_risk_flag, prediction_threshold, mlflow_run_id, scored_at
            FROM {self.settings.prediction_table}
            WHERE student_deidentified_hash = ?
            LIMIT 1
        """
        rows = self._query(statement, (student_hash,))
        return StudentPrediction.model_validate(rows[0]) if rows else None

    def get_snapshot(self, student_hash: str) -> StudentSnapshot | None:
        if not self.settings.fact_table:
            return None
        catalog, schema, table = self.settings.fact_table.split(".")
        columns = self._query(
            f"""SELECT column_name FROM {catalog}.information_schema.columns
                WHERE table_schema = ? AND table_name = ?""",
            (schema, table),
        )
        available = [row["column_name"] for row in columns if row["column_name"] in SNAPSHOT_COLUMNS]
        if not available:
            return None
        selected = ", ".join(available)
        rows = self._query(
            f"SELECT {selected} FROM {self.settings.fact_table} "
            "WHERE student_deidentified_hash = ? LIMIT 1",
            (student_hash,),
        )
        return StudentSnapshot(attributes=rows[0]) if rows else None

    def get_model_features(self, student_hash: str) -> ApprovedModelFeatureValues | None:
        """Assemble the 21 approved feature values for one student from the fact table plus
        the course and teaching-period dimension joins (research.md R1).

        A source column absent from ``information_schema`` yields an ``UNAVAILABLE`` marker
        rather than an error (FR-007); a genuine SQL NULL value is preserved as ``None``.
        Returns ``None`` only when the fact table is unconfigured or the hash has no fact row.
        """
        if not self.settings.fact_table:
            return None

        select_parts: list[str] = []
        join_parts: list[str] = []

        fact_columns = self._available_columns(self.settings.fact_table, _FACT_FEATURE_COLUMNS)
        select_parts += [f"f.{column} AS {column}" for column in fact_columns]

        if self.settings.course_table:
            course_columns = self._available_columns(
                self.settings.course_table, _COURSE_FEATURE_COLUMNS
            )
            if course_columns:
                select_parts += [f"c.{column} AS {column}" for column in course_columns]
                join_parts.append(
                    f"LEFT JOIN {self.settings.course_table} c "
                    "ON f.course_key_hash = c.course_key_hash"
                )

        if self.settings.teaching_period_table:
            tp_columns = self._available_columns(
                self.settings.teaching_period_table, _TEACHING_PERIOD_FEATURE_COLUMNS
            )
            if tp_columns:
                select_parts += [f"tp.{column} AS {column}" for column in tp_columns]
                join_parts.append(
                    f"LEFT JOIN {self.settings.teaching_period_table} tp "
                    "ON f.teaching_period_key_hash = tp.teaching_period_key_hash"
                )

        if not select_parts:
            select_parts = ["f.student_deidentified_hash AS student_deidentified_hash"]

        statement = (
            f"SELECT {', '.join(select_parts)} "
            f"FROM {self.settings.fact_table} f "
            + " ".join(join_parts)
            + " WHERE f.student_deidentified_hash = ? LIMIT 1"
        )
        rows = self._query(statement, (student_hash,))
        if not rows:
            return None
        row = rows[0]
        values = {column: row.get(column, UNAVAILABLE) for column in MODEL_FEATURE_COLUMNS}
        return ApprovedModelFeatureValues(values=values)

    def get_high_risk_students(self, limit: int) -> list[StudentPrediction]:
        rows = self._query(
            f"""SELECT student_deidentified_hash, attrition_risk_percentage,
                       attrition_risk_flag, prediction_threshold, mlflow_run_id, scored_at
                FROM {self.settings.prediction_table}
                WHERE attrition_risk_flag = TRUE
                ORDER BY attrition_risk_percentage DESC
                LIMIT ?""",
            (limit,),
        )
        return [StudentPrediction.model_validate(row) for row in rows]

    def health_check(self) -> bool:
        return bool(self._query("SELECT 1 AS healthy"))


class MockStudentRepository:
    """Clearly synthetic repository for local demos and unit tests."""

    def __init__(self) -> None:
        self.predictions = {
            "synthetic-student-001": StudentPrediction(
                student_deidentified_hash="synthetic-student-001",
                attrition_risk_percentage=78.5,
                attrition_risk_flag=True,
                prediction_threshold=0.5,
                mlflow_run_id="mock-run-001",
                scored_at="2026-01-15T10:00:00Z",
            ),
            "synthetic-student-002": StudentPrediction(
                student_deidentified_hash="synthetic-student-002",
                attrition_risk_percentage=18.0,
                attrition_risk_flag=False,
                prediction_threshold=0.5,
                mlflow_run_id="mock-run-002",
                scored_at="2026-01-15T10:00:00Z",
            ),
            # Flagged at risk; tests seed the briefing store with an existing validated
            # briefing for this hash to exercise the return-existing and regenerate paths.
            "synthetic-student-003": StudentPrediction(
                student_deidentified_hash="synthetic-student-003",
                attrition_risk_percentage=64.0,
                attrition_risk_flag=True,
                prediction_threshold=0.5,
                mlflow_run_id="mock-run-003",
                scored_at="2026-01-15T10:00:00Z",
            ),
        }

    def get_prediction(self, student_hash: str) -> StudentPrediction | None:
        return self.predictions.get(student_hash)

    def get_snapshot(self, student_hash: str) -> StudentSnapshot | None:
        if student_hash not in self.predictions:
            return None
        return StudentSnapshot(attributes={"attendance_mode": "Synthetic online", "enrolment_year": 2026})

    def get_model_features(self, student_hash: str) -> ApprovedModelFeatureValues | None:
        if student_hash not in self.predictions:
            return None
        numeric = {
            "age_at_census": 21,
            "eftsl": 0.125,
            "enrolment_year": 2026,
            "cumulative_credit_points_enrolled": 96,
            "cumulative_credit_points_passed": 72,
            "cumulative_credit_points_failed": 12,
            "cumulative_credit_points_withdrawn": 12,
        }
        values: dict[str, Any] = {
            column: numeric.get(column, f"synthetic-{column}") for column in MODEL_FEATURE_COLUMNS
        }
        # A representative absent source column so tests can assert the marker is preserved.
        values["detailed_primary_field_of_education"] = UNAVAILABLE
        return ApprovedModelFeatureValues(values=values)

    def get_high_risk_students(self, limit: int) -> list[StudentPrediction]:
        return sorted(
            [prediction for prediction in self.predictions.values() if prediction.attrition_risk_flag],
            key=lambda prediction: prediction.attrition_risk_percentage,
            reverse=True,
        )[:limit]

    def health_check(self) -> bool:
        return True
