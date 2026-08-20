"""Environment-backed application configuration."""

import os
import re
from dataclasses import dataclass

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_PREDICTION_TABLE = "workspace.student_aggregate.student_attrition_risk_prediction"
DEFAULT_FACT_TABLE = (
    "workspace.student_aggregate.rpt_student_management__fact__all_enrolment_eftsl__deidentified"
)


class ConfigurationError(ValueError):
    """Raised when required application configuration is invalid."""


def validate_table_identifier(identifier: str) -> str:
    """Accept only a three-part Unity Catalog identifier."""
    parts = identifier.split(".")
    if len(parts) != 3 or any(not _IDENTIFIER.fullmatch(part) for part in parts):
        raise ConfigurationError("Table identifiers must contain three safe name parts.")
    return identifier


@dataclass(frozen=True)
class Settings:
    app_env: str
    use_mock_data: bool
    databricks_config_profile: str | None
    databricks_host: str | None
    databricks_warehouse_id: str | None
    prediction_table: str
    fact_table: str | None
    model_name: str | None
    app_port: int
    streamlit_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        prediction_table = os.getenv("DATABRICKS_PREDICTION_TABLE", DEFAULT_PREDICTION_TABLE)
        fact_table = os.getenv("DATABRICKS_FACT_TABLE", DEFAULT_FACT_TABLE) or None
        validate_table_identifier(prediction_table)
        if fact_table:
            validate_table_identifier(fact_table)
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            use_mock_data=os.getenv("USE_MOCK_DATA", "false").lower() == "true",
            databricks_config_profile=os.getenv("DATABRICKS_CONFIG_PROFILE") or None,
            databricks_host=os.getenv("DATABRICKS_HOST") or None,
            databricks_warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID") or None,
            prediction_table=prediction_table,
            fact_table=fact_table,
            model_name=os.getenv("DATABRICKS_MODEL_NAME") or None,
            app_port=int(os.getenv("DATABRICKS_APP_PORT", "8000")),
            streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
        )
