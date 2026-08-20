# Student Attrition Risk App

This is a self-contained Databricks App proof of concept. It provides a compact Streamlit review screen, a FastAPI REST API, and a FastMCP server mounted at `/mcp`. All three interfaces use the same `StudentService`; SQL, mock data, and managed-model calls are adapters behind small protocols.

## Architecture

```text
Streamlit UI ─┐
FastAPI API ──┼──> StudentService ──> StudentRepository ──> Databricks SQL
MCP tools ────┘                    └─> BriefingProvider ──> Databricks model
```

`DatabricksStudentRepository` reads the prediction table and, when configured, retrieves only approved snapshot columns that exist in the fact table. Table identifiers are trusted configuration only and must be three-part safe identifiers. `TemplateBriefingProvider` is always available as a deterministic fallback.

## Local setup on macOS/zsh

From this folder:

Install `uv` using the official installer or your package manager, then run:

```zsh
uv sync --dev
source .venv/bin/activate
export PYTHONPATH="$PWD/src"
```

`uv.lock` is the reproducible dependency lockfile. Use `uv sync --locked --dev` in CI or when you want to ensure the lockfile is not changed.

Copy `.env.example` to `.env` only for local use and export its values in your shell. A real `.env` is ignored. Never print or commit `DATABRICKS_TOKEN`.

### Mock mode

Mock mode is explicit and is useful without Databricks:

```zsh
export USE_MOCK_DATA=true
export DATABRICKS_APP_PORT=8000
uv run uvicorn student_attrition_risk.main:app --host 0.0.0.0 --port "$DATABRICKS_APP_PORT"
```

Open `http://127.0.0.1:8000/ui/`. The mock hashes are `synthetic-student-001` and `synthetic-student-002`.

### Live Databricks mode

Set `USE_MOCK_DATA=false`, `DATABRICKS_CONFIG_PROFILE`, `DATABRICKS_WAREHOUSE_ID`, and the configured three-part table names. `DATABRICKS_HOST` is optional when the CLI profile already supplies it. For example, with the local `free` profile:

```zsh
export USE_MOCK_DATA=false
export DATABRICKS_CONFIG_PROFILE=free
export DATABRICKS_WAREHOUSE_ID=YOUR_WAREHOUSE_ID
export DATABRICKS_HOST=https://YOUR_WORKSPACE_HOST
uv run uvicorn student_attrition_risk.main:app --host 0.0.0.0 --port 8000
```

The app calls `WorkspaceClient.config.authenticate()` and passes the resulting short-lived bearer token in memory to the Databricks SQL connector. It does not print or persist that token. `DATABRICKS_TOKEN` is supported only when explicitly supplied for a terminal session. In a deployed Databricks App, the same code path uses the app's injected OAuth/service-principal credentials, provided the app has permission to the SQL warehouse and tables.

For a current CLI profile, inspect available authentication commands with `databricks auth --help`, then obtain a short-lived token for the current terminal using the CLI command shown by that installed version. Export it only in the current shell, for example `export DATABRICKS_TOKEN="$(databricks auth token --host "$DATABRICKS_HOST")"` when that command is supported. Do not paste a token into this repository or echo it.

## Configuration

`DATABRICKS_PREDICTION_TABLE` defaults to the repository-confirmed `workspace.student_aggregate.student_attrition_risk_prediction`. `DATABRICKS_FACT_TABLE` defaults to the repository-confirmed fact table, but can be blank to disable snapshot retrieval. `DATABRICKS_MODEL_NAME` is optional; leave it blank for template briefings. Set it only to a callable serving endpoint/model identifier confirmed in the target workspace. The code does not assume a model family.

## REST API

- `GET /api/health`
- `GET /api/students/{student_hash}`
- `GET /api/students/high-risk?limit=20`
- `POST /api/students/{student_hash}/briefing`

Unknown hashes return 404, invalid limits return 422 at FastAPI validation, and data-source failures return 503 with safe messages.

## MCP

The four tools are `get_student_prediction`, `get_student_profile`, `get_high_risk_students`, and `generate_student_briefing`. They contain no SQL and delegate to `StudentService`.

The FastMCP HTTP app is mounted at `/mcp`; the remote URL is therefore `https://YOUR_APP_URL/mcp/` (the trailing slash is accepted by the mounted transport). Use `.vscode/mcp.json.example` as a credential-free template for a remote connection. It references a short-lived `DATABRICKS_TOKEN` environment variable and contains no secret.

For local development, point an MCP client at `http://127.0.0.1:8000/mcp/`. When the app is running in explicit mock mode, no Databricks authentication header is needed.

## Databricks UI deployment

Push this folder to the Git folder visible in the Databricks workspace. Use the Databricks App **Deploy** button, select `student_attrition_risk_app` as the source folder, configure the app environment and SQL warehouse resource, and deploy. `app.yaml` starts Uvicorn on `${DATABRICKS_APP_PORT}`. This project intentionally includes no Asset Bundle, deployment automation, or resource-creation script.

## Data and briefing limitations

The data is cross-sectional synthetic data: each hash is one independent snapshot. The app never presents changes over time, declines, historical trends, or causal explanations. Raw values are labelled `Student Snapshot`, not individual feature contributions. There are no per-student SHAP or explanation values; global feature importance is not used as a personal explanation. Briefings identify the record as synthetic, describe risk as a model-generated signal, avoid sensitive inferences, and recommend only supportive human review.

## Checks

```zsh
uv run ruff check .
uv run pytest
```

The tests use an in-memory repository and do not require a live workspace. A local smoke check is `curl http://127.0.0.1:8000/api/health`, followed by `curl http://127.0.0.1:8000/api/students/synthetic-student-001`.
