# Quickstart & Validation: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

How to run and validate the single-retry workflow and the governed Unity Catalog Volume store.
References: [spec.md](./spec.md), [plan.md](./plan.md), [contracts/](./contracts/),
[data-model.md](./data-model.md). Feature-001 quickstart still applies for the base backend.

## Prerequisites

- `uv` installed; from `student_attrition_risk_app/`: `uv sync --dev`.
- Offline validation (the merge gate) needs nothing else — no workspace, no network.
- Exercising the Volume store against a real Volume needs a Databricks CLI profile with write
  access to the `${BRIEFING_VOLUME}` path.

## Checks (must pass before merge — constitution IV, XII)

```
uv run ruff check .
uv run pytest
```

All existing Feature-001 test files must stay green, plus the new
`test_retry_workflow.py`, `test_briefing_retry_integration.py`, `test_volume_briefing_store.py`,
and the extended `test_config.py`.

## Offline validation — the single-retry workflow

Driven entirely by scripted test doubles (`ScriptedGenerationProvider`, `ScriptedValidator`);
no external service. Covered by `tests/test_retry_workflow.py` and
`tests/test_briefing_retry_integration.py`:

| Scenario | Expected |
|---|---|
| Attempt 1 validation fails, Attempt 2 generates + passes validation | `request_briefing` returns a `ValidatedBriefing` with `attempt_count == 2`; store holds it as most-recent |
| Attempt 1 generation raises a retryable error, Attempt 2 passes | returns `attempt_count == 2` |
| Attempt 1 validation fails (criteria + feedback present), inspect the retry request | attempt-2 `composed_prompt` contains the failed criteria and feedback; `hash` / `prediction` / `features` / `instructions_id` unchanged |
| Attempt 1 validation fails under the interim validator (no criteria, no feedback) | attempt-2 `composed_prompt` equals the original; nothing fabricated |
| Attempt 2 generation fails | `BriefingNotProducedError` / 502 with category `generation`; nothing stored |
| Attempt 2 validation fails | `BriefingNotProducedError` / 502 with category `validation`; nothing stored |
| Any first-attempt failure | `generate` invoked exactly twice total across the request; never a third time |
| Attempt 2 raises `ConfigurationError` | surfaces unchanged as 503; never a 502, never a template |
| Regeneration for a student with a prior briefing, both attempts fail | previous validated briefing still returned by `GET /api/students/{hash}/briefing` |
| Any failure | logs carry `attempt_count` / outcome category / `validator_id`; no prompt text, no briefing text, no secret |

Run just this slice:

```
uv run pytest tests/test_retry_workflow.py tests/test_briefing_retry_integration.py -q
```

## Offline validation — the governed Volume store

`tests/test_volume_briefing_store.py` runs `VolumeBriefingStore` against an in-memory
`FakeFilesClient` (emulates `upload` / `download` / `list_directory_contents`):

| Scenario | Expected |
|---|---|
| `save_validated` then `get_latest_validated` | returns an equal `ValidatedBriefing`; `has_validated` is `True` |
| `get_latest_validated` / `has_validated` for an unknown hash | `None` / `False` |
| Two `save_validated` calls | the later (greater filename) briefing is returned; the first file still exists |
| `upload` raises | `BriefingStorageError`; any prior latest file untouched |
| `download` / `list` raises a non-not-found error | `BriefingStorageError` (distinct from `None`) |
| Body written | JSON of `ValidatedBriefing` only — no prompt key, no secret |
| Feature-001 `test_briefing_store.py` scenarios re-run against `VolumeBriefingStore` | pass unchanged (SC-010) |

```
uv run pytest tests/test_volume_briefing_store.py tests/test_config.py -q
```

## Store selection

```
# in-memory store (default for local / mock / tests)
unset BRIEFING_VOLUME

# governed Unity Catalog Volume store
export BRIEFING_VOLUME=/Volumes/<catalog>/<schema>/<volume>          # e.g. /Volumes/workspace/student_aggregate/advisor_briefings
```

`config.validate_volume_path` rejects a value that does not start `/Volumes/` or lacks
catalog/schema/volume segments (`ConfigurationError`). `main.build_service` picks
`VolumeBriefingStore` when `BRIEFING_VOLUME` is set, else `InMemoryBriefingStore`.

## Live check (needs a workspace; full retry needs US-13)

```
export USE_MOCK_DATA=false
export DATABRICKS_CONFIG_PROFILE=<profile>
export DATABRICKS_HOST=https://<workspace host>
export DATABRICKS_WAREHOUSE_ID=<warehouse id>
export BRIEFING_VOLUME=/Volumes/<catalog>/<schema>/<volume>
uv run uvicorn student_attrition_risk.main:app --host 0.0.0.0 --port 8000
```

1. `POST /api/students/<at-risk hash>/briefing` → **503** "Briefing generation is not
   configured" until US-13 supplies the generation seam — the retry path is reached only after
   a real first-attempt generation, so a full retry cannot be exercised live before US-13.
2. Once US-13 is wired: a first attempt that fails validation is followed by exactly one more
   generation, and on success a JSON file appears under
   `${BRIEFING_VOLUME}/<hash>/…-attempt2-….json`; `GET /api/students/<hash>/briefing` returns
   it with `attempt_count = 2`.
3. Two failed attempts → **502** "Briefing could not be produced (generation|validation)"; no
   new file under `${BRIEFING_VOLUME}/<hash>/`; any earlier file for that student is still
   there and still returned by `GET`.

## Interim behaviour to remember

- The generation seam is a stub until **US-13**; until then the retry path is unreachable in a
  live run (first-attempt `ConfigurationError` is surfaced before the hand-off).
- Validation is `interim-pass-through` until **US-14**; a validation-failure retry is only
  exercised via a stub validator, and it then carries no `failed_criteria` / `feedback` — the
  retry request equals the original context.
- `RetryNotConfigured` remains available as the "retry disabled" wiring and is still used by the
  Feature-001 orchestration tests.
- With `BRIEFING_VOLUME` unset the app behaves exactly as Feature-001 (in-memory store).
