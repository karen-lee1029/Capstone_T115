import pytest

from student_attrition_risk.config import (
    DEFAULT_COURSE_TABLE,
    DEFAULT_TEACHING_PERIOD_TABLE,
    ConfigurationError,
    Settings,
    validate_table_identifier,
    validate_volume_path,
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


def test_validate_volume_path_accepts_a_unity_catalog_volume():
    assert (
        validate_volume_path("/Volumes/main/advising/briefings")
        == "/Volumes/main/advising/briefings"
    )
    # a deeper prefix under the volume is allowed
    assert validate_volume_path("/Volumes/main/advising/briefings/v2").endswith("/v2")


def test_validate_volume_path_rejects_bad_values():
    for bad in (
        "main.advising.briefings",  # missing /Volumes/ prefix
        "/Volumes/main/advising",  # fewer than catalog/schema/volume
        "/Volumes/main/advising/brief ings",  # unsafe character
        "/Volumes/main/advising/../secrets",  # traversal segment
    ):
        with pytest.raises(ConfigurationError):
            validate_volume_path(bad)


def test_briefing_volume_env_is_read_validated_and_optional(monkeypatch):
    monkeypatch.setenv("BRIEFING_VOLUME", "/Volumes/main/advising/briefings")
    assert Settings.from_env().briefing_volume == "/Volumes/main/advising/briefings"

    monkeypatch.setenv("BRIEFING_VOLUME", "")
    assert Settings.from_env().briefing_volume is None

    monkeypatch.delenv("BRIEFING_VOLUME", raising=False)
    assert Settings.from_env().briefing_volume is None

    monkeypatch.setenv("BRIEFING_VOLUME", "not-a-volume-path")
    with pytest.raises(ConfigurationError):
        Settings.from_env()
