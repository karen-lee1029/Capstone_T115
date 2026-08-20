import pytest

from student_attrition_risk.config import ConfigurationError, validate_table_identifier


def test_table_names_require_three_safe_parts():
    assert validate_table_identifier("catalog.schema.table") == "catalog.schema.table"
    for name in ("schema.table", "catalog.schema.table; DROP TABLE x", "catalog.schema.`table`"):
        with pytest.raises(ConfigurationError):
            validate_table_identifier(name)
