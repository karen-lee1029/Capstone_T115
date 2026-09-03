import pytest

from student_attrition_risk.config import (
    DEFAULT_COURSE_TABLE,
    DEFAULT_TEACHING_PERIOD_TABLE,
    ConfigurationError,
    Settings,
    validate_table_identifier,
)


def test_table_names_require_three_safe_parts():
    assert validate_table_identifier("catalog.schema.table") == "catalog.schema.table"
    for name in ("schema.table", "catalog.schema.table; DROP TABLE x", "catalog.schema.`table`"):
        with pytest.raises(ConfigurationError):
            validate_table_identifier(name)


def test_course_and_teaching_period_tables_default_to_confirmed_names(monkeypatch):
    monkeypatch.delenv("DATABRICKS_COURSE_TABLE", raising=False)
    monkeypatch.delenv("DATABRICKS_TEACHING_PERIOD_TABLE", raising=False)
    settings = Settings.from_env()
    assert settings.course_table == DEFAULT_COURSE_TABLE
    assert settings.teaching_period_table == DEFAULT_TEACHING_PERIOD_TABLE


def test_course_and_teaching_period_tables_accept_valid_override(monkeypatch):
    monkeypatch.setenv("DATABRICKS_COURSE_TABLE", "workspace.other_schema.course_dim")
    monkeypatch.setenv("DATABRICKS_TEACHING_PERIOD_TABLE", "workspace.other_schema.tp_dim")
    settings = Settings.from_env()
    assert settings.course_table == "workspace.other_schema.course_dim"
    assert settings.teaching_period_table == "workspace.other_schema.tp_dim"


def test_blank_course_or_teaching_period_table_disables_the_join(monkeypatch):
    monkeypatch.setenv("DATABRICKS_COURSE_TABLE", "")
    monkeypatch.setenv("DATABRICKS_TEACHING_PERIOD_TABLE", "")
    settings = Settings.from_env()
    assert settings.course_table is None
    assert settings.teaching_period_table is None


def test_malformed_course_table_is_rejected(monkeypatch):
    monkeypatch.setenv("DATABRICKS_COURSE_TABLE", "schema.table; DROP TABLE x")
    with pytest.raises(ConfigurationError):
        Settings.from_env()
