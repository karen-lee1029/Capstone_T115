"""Student repository adapters."""

from typing import Any

from .config import Settings
from .databricks_client import create_sql_connection
from .models import StudentPrediction, StudentSnapshot

SNAPSHOT_COLUMNS = (
    "age_band",
    "international_domestic_student",
    "attendance_mode",
    "course_admission_load_category",
    "eftsl",
    "enrolment_year",
    "commencing_continuing",
    "cumulative_credit_points_enrolled",
    "cumulative_credit_points_passed",
    "cumulative_credit_points_failed",
    "cumulative_credit_points_withdrawn",
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
        }

    def get_prediction(self, student_hash: str) -> StudentPrediction | None:
        return self.predictions.get(student_hash)

    def get_snapshot(self, student_hash: str) -> StudentSnapshot | None:
        if student_hash not in self.predictions:
            return None
        return StudentSnapshot(attributes={"attendance_mode": "Synthetic online", "enrolment_year": 2026})

    def get_high_risk_students(self, limit: int) -> list[StudentPrediction]:
        return sorted(
            [prediction for prediction in self.predictions.values() if prediction.attrition_risk_flag],
            key=lambda prediction: prediction.attrition_risk_percentage,
            reverse=True,
        )[:limit]

    def health_check(self) -> bool:
        return True
