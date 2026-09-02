# Quickstart & Validation: Feature-001 (US-08)

How to run and validate the backend — data retrieval + request orchestration + the five
integration seams — with Feature-001's placeholder seams. The concrete generation (US-13),
validation (US-14), storage and retry (US-15) are validated in their own stories. References:
[spec.md](./spec.md), [contracts/](./contracts/), [data-model.md](./data-model.md).

## Prerequisites

- `uv` installed; from `student_attrition_risk_app/`: `uv sync --dev`.
- Offline validation needs nothing else.
- Live Delta reads need a Databricks CLI profile with access to `workspace.student_aggregate`
  and a SQL warehouse id.

## Checks (must pass before merge — constitution IV, XII)

```
uv run ruff check .
uv run pytest
```

Fully offline: `MockStudentRepository`, `InMemoryBriefingStore`, `StubGenerationProvider`,
`StubValidator`. No network, no live workspace, no concrete provider or Volume store.

## Offline orchestration walk-through (placeholder seams)

```
export USE_MOCK_DATA=true
export DATABRICKS_APP_PORT=8000
uv run uvicorn student_attrition_risk.main:app --host 0.0.0.0 --port "$DATABRICKS_APP_PORT"
```

Default wiring: `StubGenerationProvider` (raises "not configured"), `InterimInstructions`,
`InterimValidator` (pass-through), `RetryNotConfigured`, `InMemoryBriefingStore`.

Mock students (`MockStudentRepository`):

| Hash | Flagged at risk? | Pre-existing validated briefing? |
|---|---|---|
| `synthetic-student-001` | yes | no |
| `synthetic-student-002` | no | no |
| `synthetic-student-003` (new fixture) | yes | yes (seeded into `InMemoryBriefingStore`) |

Expected observable behaviour (see `contracts/rest-api.md`):

| Call | Expected |
|---|---|
| `GET /api/students/synthetic-student-001/briefing` | `404` "No validated briefing available" |
| `POST /api/students/synthetic-student-002/briefing` | `409` "Student is not flagged at risk"; no seam calls for generation |
| `POST /api/students/synthetic-student-003/briefing` | `200`, `source="stored"`; **no generation-seam call** (FR-035) |
| `POST /api/students/synthetic-student-001/briefing` | `503` "Briefing generation is not configured" — the default generation seam is a stub (never a template briefing) |
| `GET /api/students/synthetic-student-003/briefing` | `200`, most recent validated briefing (FR-030) |

MCP (`http://127.0.0.1:8000/mcp/`): `generate_student_briefing` and `get_student_briefing`
mirror the above; failures are tool errors, never a fabricated briefing.

## Orchestration paths proven in tests (with stub seams)

`test_briefing_orchestration.py` drives the full FR-033 sequence by injecting stub seams:

| Stub setup | Asserted |
|---|---|
| `StubGenerationProvider(draft=…)` + `StubValidator(passed=True)` | context carries all 21 features + risk result; seams called in order; `save_validated` called once; `ValidatedBriefing` returned |
| `StubValidator(passed=False, failed_criteria=[…], feedback="…")` | `ValidationFailed` passed to the retry seam; with `RetryNotConfigured` → `502` (detail: "... (validation)") and nothing stored |
| `StubGenerationProvider(raises=GenerationError)` | `GenerationFailed` passed to the retry seam; with `RetryNotConfigured` → `502` (detail: "... (generation)") and nothing stored |
| student-003 + `regenerate=true` + `StubValidator(passed=True)` | new `ValidatedBriefing` supersedes; store now returns it as latest |
| student-003 + `regenerate=true` + terminal failure | previous validated briefing retained and still returned by `GET` (FR-037) |
| `InMemoryBriefingStore.save_validated` raising `BriefingStorageError` | `503` "Validated briefing could not be stored"; previous entry intact |
| any run | logs contain hash / outcome / attempt_count / validator_id but no prompt, no briefing text, no secret (FR-031/FR-032) |

## Live Delta reads (data retrieval only)

```
export USE_MOCK_DATA=false
export DATABRICKS_CONFIG_PROFILE=<profile>
export DATABRICKS_WAREHOUSE_ID=<warehouse id>
export DATABRICKS_HOST=https://<workspace host>
# optional overrides; defaults are the repository-confirmed table names
export DATABRICKS_COURSE_TABLE=workspace.student_aggregate.dwh_curriculum__course
export DATABRICKS_TEACHING_PERIOD_TABLE=workspace.student_aggregate.dwh_learning_and_teaching__teaching_period
uv run uvicorn student_attrition_risk.main:app --host 0.0.0.0 --port 8000
```

Validate against a known at-risk synthetic hash `H`:

1. `GET /api/students/H` → `200` — unchanged by Feature-001 (still the existing 11-field
   snapshot). The 21-feature assembly for briefing generation is not exposed on this endpoint;
   it is verified by the repository unit test (T019) and, live, is exercised by step 3 (the
   briefing path reaching the generation seam).
2. `GET /api/students/high-risk?limit=5` → `200`; every row has `attrition_risk_flag = true`
   (FR-005).
3. `POST /api/students/H/briefing` → `503` "Briefing generation is not configured" until US-13
   supplies the concrete generation seam. This confirms the orchestration reaches the seam and
   fails explicitly rather than templating.

## Interim behaviour to remember

- The generation seam is a stub until **US-13**; an unconfigured backend fails fast and
  explicitly (FR-014).
- Briefing instructions are the interim safe PoC text until **US-12** (FR-010).
- Validation is `interim-pass-through` until **US-14**; the `validator_id` in every response
  and stored object says so (FR-016).
- The retry seam is `RetryNotConfigured` until **Feature-002 / US-15**: a failed first attempt
  goes straight to a terminal `502` (category in the detail text), stores nothing, never
  retries (FR-019/FR-021).
- Validated-briefing storage is in-memory until **US-15** supplies the governed Unity Catalog
  Volume implementation behind the same `BriefingStore` interface.
