# Student Attrition Risk App

This is a self-contained Databricks App proof of concept. It provides a compact Streamlit review screen, a FastAPI REST API, and a FastMCP server mounted at `/mcp`. All three interfaces use the same `StudentService`; SQL, mock data, and managed-model calls are adapters behind small protocols.

## Architecture

```text
Streamlit UI ─┐
FastAPI API ──┼──> StudentService ──> StudentRepository ──> Databricks SQL (prediction + feature tables)
MCP tools ────┘         │
                        └─> briefing seams ──> GenerationProvider · BriefingInstructions ·
                                               BriefingValidator · RetryWorkflow · BriefingStore
```

`DatabricksStudentRepository` reads the prediction table and, when configured, retrieves the approved snapshot columns that exist in the fact table (`get_snapshot`, 11 fields, unchanged) and — for briefing generation — the 21 approved machine-learning feature values assembled from the fact table plus the course and teaching-period dimension joins (`get_model_features`). Table identifiers are trusted configuration only and must be three-part safe identifiers.

### Feature-001 (US-08) briefing workflow

`StudentService.request_briefing` coordinates a Structured Advisor Briefing request end to end
through five replaceable integration seams. Feature-001 ships **placeholder implementations
only**; the concrete behaviour is delivered by later backlog stories:

| Seam | Feature-001 placeholder | Concrete owner |
|---|---|---|
| `GenerationProvider` | `StubGenerationProvider` (fails fast: "Briefing generation is not configured") | US-13 |
| `BriefingInstructions` | `InterimInstructions` (reuses the existing safe prompt wording) | US-12 |
| `BriefingValidator` | `InterimValidator` (pass-through, `validator_id="interim-pass-through"`) | US-14 |
| `RetryWorkflow` | `RetryNotConfigured` (terminal failure, no retry) | Feature-002 / US-15 — `SingleRetryWorkflow` (shipped) |
| `BriefingStore` | `InMemoryBriefingStore` | US-15 — `VolumeBriefingStore` (shipped); in-memory kept for local/tests |

The advisor-facing dashboard, at-risk display, and selection interaction are US-09 / US-10 /
US-11. A request routes to generation only for a student the model flags at risk and only when
no validated briefing exists (or `?regenerate=true` is passed); otherwise the existing
validated briefing is returned without invoking generation. A failed first attempt is handed to
the retry seam once; a `502` and nothing stored is the terminal outcome when the retry also
fails — a deterministic/template briefing is never substituted for a real one.

### Feature-002 (US-15) briefing retry and validated-briefing storage

`SingleRetryWorkflow` is the concrete `RetryWorkflow`. When the first attempt does not yield a
validated briefing — the draft failed validation, or generation failed with a retryable error
(anything other than a configuration error) — it performs **exactly one** more generation
attempt and re-validates it. It runs the generation boundary once and the validation boundary
at most once, so a third attempt is structurally impossible. On success it returns a
`ValidatedBriefing` with `attempt_count = 2` through the existing successful-outcome path;
`StudentService` persists it (the workflow never persists). On a second failure it returns a
terminal `generation` or `validation` outcome, which maps to the existing `502`; a
configuration error surfacing during the retry is re-raised unchanged (`503`). No new
advisor-visible retry indicator is added — `attempt_count` is the record. The revision request
sent to generation is the original context with a minimal block relaying only the failed
acceptance criteria and Validation Feedback that validation actually returned; it is replaced
when the final US-12 instructions land.

`VolumeBriefingStore` is the concrete `BriefingStore`, backed by a governed Databricks Unity
Catalog Volume. It writes one JSON document per validated briefing to
`${BRIEFING_VOLUME}/<student_hash>/<timestamp>-attempt<n>-<token>.json`. Storage is
**append-only** — nothing is ever overwritten or deleted, and there is no pruning of superseded
briefings; "most recent" is the greatest file name (the fixed-width timestamp prefix orders
chronologically). A missing student directory is an explicit "none available"; any other
Files-API failure surfaces as `BriefingStorageError` (`503`). Set `BRIEFING_VOLUME` to a
`/Volumes/<catalog>/<schema>/<volume>` path to enable it; leave it blank to keep
`InMemoryBriefingStore` (local mode and the test suite). The concrete deployment Volume path is
supplied at deploy time — none is hard-coded.

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

`DATABRICKS_PREDICTION_TABLE` defaults to the repository-confirmed `workspace.student_aggregate.student_attrition_risk_prediction`. `DATABRICKS_FACT_TABLE` defaults to the repository-confirmed fact table, but can be blank to disable snapshot retrieval. `DATABRICKS_COURSE_TABLE` and `DATABRICKS_TEACHING_PERIOD_TABLE` default to the repository-confirmed dimension tables used to assemble the 21 approved feature values for briefing generation; either can be blank to disable that join (the affected features are then marked unavailable). `DATABRICKS_MODEL_NAME` is unused by the Feature-001 briefing workflow (the generative integration is US-13). `BRIEFING_VOLUME` (Feature-002 / US-15) selects the validated-briefing store: a `/Volumes/<catalog>/<schema>/<volume>` path enables `VolumeBriefingStore`; blank or unset keeps `InMemoryBriefingStore`. It is validated as a Unity Catalog Volume path and is never hard-coded — the deployment value is set at deploy time.

## REST API

- `GET /api/health`
- `GET /api/students/{student_hash}`
- `GET /api/students/high-risk?limit=20`
- `POST /api/students/{student_hash}/briefing[?regenerate=true]` — get-or-create: returns the existing validated briefing if one exists, otherwise runs the generation seams; `regenerate=true` forces a fresh run.
- `GET /api/students/{student_hash}/briefing` — the most recent stored validated briefing, or `404 "No validated briefing available"`.

Unknown hashes return 404, a briefing request for a student not flagged at risk returns 409, request validation returns 422 at FastAPI, a downstream briefing-generation dependency failure returns 502, and not-configured / data-source / storage failures return 503 with safe messages.

## MCP

The five tools are `get_student_prediction`, `get_student_profile`, `get_high_risk_students`, `generate_student_briefing` (get-or-create; accepts `regenerate`), and `get_student_briefing` (retrieve the stored validated briefing). They contain no SQL and delegate to `StudentService`.

The FastMCP HTTP app is mounted at `/mcp`; the remote URL is therefore `https://YOUR_APP_URL/mcp/` (the trailing slash is accepted by the mounted transport). Use `.vscode/mcp.json.example` as a credential-free template for a remote connection. It references a short-lived `DATABRICKS_TOKEN` environment variable and contains no secret.

For local development, point an MCP client at `http://127.0.0.1:8000/mcp/`. When the app is running in explicit mock mode, no Databricks authentication header is needed.

## Databricks UI deployment

Push this folder to the Git folder visible in the Databricks workspace. Use the Databricks App **Deploy** button, select `student_attrition_risk_app` as the source folder, configure the app environment and SQL warehouse resource, and deploy. `app.yaml` starts Uvicorn on `${DATABRICKS_APP_PORT}`. This project intentionally includes no Asset Bundle, deployment automation, or resource-creation script.

## Data and briefing limitations

The data is cross-sectional synthetic data: each hash is one independent snapshot. The app never presents changes over time, declines, historical trends, or causal explanations. Raw values are labelled `Student Snapshot`, not individual feature contributions. There are no per-student SHAP or explanation values; global feature importance is not used as a personal explanation. When the generation seam is unavailable, a briefing request returns an explicit error — a deterministic or template briefing is never substituted for a real one. The briefing context and the interim instructions carry the 21 approved feature values as background only, identify the record as synthetic, describe risk as a model-generated signal, and avoid sensitive inferences; the final briefing content rules and acceptance-criteria validation are owned by US-12 / US-14.

## Checks

```zsh
uv run ruff check .
uv run pytest
```

The tests use an in-memory repository and do not require a live workspace. A local smoke check is `curl http://127.0.0.1:8000/api/health`, followed by `curl http://127.0.0.1:8000/api/students/synthetic-student-001`.
