"""Databricks SQL connection factory with unified-auth support."""

import os
from typing import Any

from .config import ConfigurationError, Settings


def create_sql_connection(settings: Settings) -> Any:
    """Create a SQL connector connection without logging credentials."""
    if not settings.databricks_warehouse_id:
        raise ConfigurationError("DATABRICKS_WAREHOUSE_ID is required for live SQL access.")
    from databricks import sql

    kwargs: dict[str, Any] = {
        "server_hostname": settings.databricks_host,
        "http_path": f"/sql/1.0/warehouses/{settings.databricks_warehouse_id}",
    }
    token = os.getenv("DATABRICKS_TOKEN")
    if token:
        kwargs["access_token"] = token
        return sql.connect(**kwargs)

    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(profile=settings.databricks_config_profile, host=settings.databricks_host)
    config = client.config
    authorization = config.authenticate().get("Authorization", "")
    access_token = authorization.removeprefix("Bearer ").strip()
    if not access_token:
        raise ConfigurationError("Databricks unified authentication did not provide an access token.")
    kwargs["server_hostname"] = config.host.removeprefix("https://")
    kwargs["access_token"] = access_token
    return sql.connect(**kwargs)
