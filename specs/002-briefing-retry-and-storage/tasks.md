---
description: "Task list for Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)"
---

# Tasks: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

**Input**: Design documents from `specs/002-briefing-retry-and-storage/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` (all approved 2026-09-03)

**Tests**: Included — the feature input explicitly requires implementation tasks paired with
proportionate tests. Test files match `plan.md` § Test plan.

**Organization**: Tasks are grouped by the three user stories in `spec.md`. US1 (P1) is the MVP.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` for user-story phases only

## Scope guardrails (from the approved plan — do not exceed)

- Reuse the Feature-001 seams and orchestration verbatim; no parallel implementations.
- **No** tasks for US-13 (OpenAI), US-14 (validation rules), legacy-provider cleanup,
  dashboard/frontend, unrelated refactoring, or ML/data-generation notebooks.
- Preserve the five approved planning decisions: configurable `BRIEFING_VOLUME`;
  unconditional `SingleRetryWorkflow` wiring; minimal Feature-002 retry-feedback wrapper;
  append-only briefing history with no pruning; one JSON file per validated briefing.
- No Git/GitHub write operations.

## Files touched (per `plan.md` § Project Structure)

| Action | Path |
|---|---|
| MODIFY | `student_attrition_risk_app/src/student_attrition_risk/retry_workflow.py` (add `SingleRetryWorkflow` + `_retry_context`; keep `RetryNotConfigured`) |
| MODIFY | `student_attrition_risk_app/src/student_attrition_risk/briefing_store.py` (add `VolumeBriefingStore`; keep `InMemoryBriefingStore`) |
| MODIFY | `student_attrition_risk_app/src/student_attrition_risk/config.py` (add `briefing_volume` + `validate_volume_path`) |
| MODIFY (additive) | `student_attrition_risk_app/src/student_attrition_risk/models.py` (add `make_validated_briefing`) |
| MODIFY (behaviour-preserving) | `student_attrition_risk_app/src/student_attrition_risk/student_service.py` (`_build_validated` delegates) |
| MODIFY | `student_attrition_risk_app/src/student_attrition_risk/main.py` (`build_service` wiring) |
| MODIFY | `student_attrition_risk_app/.env.example`, `student_attrition_risk_app/app.yaml` (blank `BRIEFING_VOLUME`) |
| MODIFY | `student_attrition_risk_app/README.md` |
| NEW | `student_attrition_risk_app/tests/doubles.py`, `tests/test_retry_workflow.py`, `tests/test_briefing_retry_integration.py`, `tests/test_volume_briefing_store.py` |
| MODIFY | `student_attrition_risk_app/tests/test_config.py` |
| READ-ONLY | `ports.py`, `api.py`, `mcp_server.py`, `briefing_provider.py`, `briefing_instructions.py`, `briefing_validation.py`, `student_repository.py`, `databricks_client.py`, `ui.py`, and every existing Feature-001 test file |

---

## Phase 1: Setup

**Purpose**: Establish the pre-change baseline.

- [X] T001 From `student_attrition_risk_app/`, run `uv sync --dev`, then `uv run ruff check .` and `uv run pytest`; record that the Feature-001 suite is green before any Feature-002 change.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks every user story needs. **No user story may start until this phase is done.**

- [X] T002 [P] Add `make_validated_briefing(*, student_hash, prediction, text, validator_id, attempt_count, generated_at=None) -> ValidatedBriefing` to `student_attrition_risk_app/src/student_attrition_risk/models.py` — additive only; builds `ValidatedBriefing` from a `StudentPrediction` with `source="generated"`, `validated=True`, `generated_at` defaulting to `datetime.now(UTC)` (per `data-model.md` § new implementation types, `research.md` R3).
- [X] T003 Refactor `StudentService._build_validated` in `student_attrition_risk_app/src/student_attrition_risk/student_service.py` to delegate to `make_validated_briefing` (identical output; `attempt_count=1`). No orchestration/call-order change. Existing `tests/test_student_service.py` and `tests/test_briefing_orchestration.py` must stay green. (depends on T002)
- [X] T004 [P] Create `student_attrition_risk_app/tests/doubles.py` with the offline test doubles from `plan.md` § Test plan: `ScriptedGenerationProvider` (ordered list of draft-or-exception, one consumed per `generate`, raises on over-call), `ScriptedValidator` (ordered `ValidationOutcome`s), and `FakeFilesClient` (in-memory dict emulating `upload` / `download` / `list_directory_contents`, including a not-found error).

**Checkpoint**: shared factory + test doubles ready.

---

## Phase 3: User Story 1 — Recover from a first-attempt failure with a single retry (Priority: P1) 🎯 MVP

**Goal**: After a first-attempt validation failure or a retryable (non-`ConfigurationError`)
generation failure, perform exactly one more generation attempt, revalidate it, and on success
return + persist it as a `ValidatedBriefing` with `attempt_count == 2`, through the existing
`StudentService._hand_off_to_retry` path.

**Independent Test**: With `ScriptedGenerationProvider` set to fail once then return a draft and
`ScriptedValidator` set to fail once then pass, one `request_briefing` call produces exactly two
generation attempts and returns a validated briefing with `attempt_count == 2`; repeating with
the first generation call raising a retryable error exercises the generation-failure retry.

### Tests for User Story 1

- [X] T005 [P] [US1] Write `student_attrition_risk_app/tests/test_retry_workflow.py` covering: validation-failure → retry generation → revalidation passes ⇒ `Produced`, `attempt_count == 2`; generation-failure → retry → validation passes ⇒ `Produced`, `attempt_count == 2`; retry request for a validation failure with `failed_criteria` + `feedback` present has both in the attempt-2 `composed_prompt` and keeps `student_deidentified_hash` / `prediction` / `features` / `instructions_id` unchanged; retry request for a validation failure with empty `failed_criteria` and `feedback is None` equals the original `composed_prompt` (nothing fabricated); retry request for a generation failure equals the original `composed_prompt`; `generation_provider.generate` is called exactly once inside `run`. Import doubles from `tests/doubles.py`. (fails until T007–T008)
- [X] T006 [P] [US1] Write `student_attrition_risk_app/tests/test_briefing_retry_integration.py` US1 case: through a real `StudentService` with `SingleRetryWorkflow` + `InMemoryBriefingStore` and scripted doubles, a validation-fail-then-pass sequence makes `request_briefing` return the validated briefing with `attempt_count == 2` and the store holds that briefing; assert the briefing reaches the store via the existing `StudentService._hand_off_to_retry` → `_persist` path and **not** via any persistence call inside `SingleRetryWorkflow` (the workflow returns `Produced` only — FR-019, US1 Acceptance Scenario 8); the workflow log line carries `attempt_count=2` and an outcome category but no prompt text and no briefing text (FR-033). (fails until T007–T009)

### Implementation for User Story 1

- [X] T007 [US1] Implement `SingleRetryWorkflow` in `student_attrition_risk_app/src/student_attrition_risk/retry_workflow.py` per `contracts/retry-workflow.md`: `__init__(generation_provider: GenerationProvider, validator: BriefingValidator)`; `run(context, first_outcome) -> BriefingOutcome` calls `generation_provider.generate` **exactly once** and `validator.validate` **at most once** (no loop, no recursion — a third attempt is structurally impossible); on attempt-2 validation pass return `Produced(make_validated_briefing(student_hash=context.student_deidentified_hash, prediction=context.prediction, text=<attempt-2 draft text>, validator_id=<attempt-2 outcome.validator_id>, attempt_count=2))`; on attempt-2 generation failure (non-`ConfigurationError`) return `TerminalFailure(category="generation")`; on attempt-2 validation fail return `TerminalFailure(category="validation")`; let a `ConfigurationError` from the attempt-2 `generate` propagate unchanged (guarded **before** any generic exception handling). `run` returns the outcome only — it performs **no** persistence; storing a `Produced` briefing remains the responsibility of the existing `StudentService._hand_off_to_retry` → `_persist` path (FR-019). Keep `RetryNotConfigured` in the module unchanged. (depends on T002)
- [X] T008 [US1] In the same file, implement the private `_retry_context(context, first_outcome) -> BriefingGenerationContext` helper plus one module-level retry-feedback wrapper constant: return `context.model_copy(update={"composed_prompt": P})`; for `ValidationFailed` whose `outcome.failed_criteria` **or** `outcome.feedback` is non-empty, `P` = original `composed_prompt` + the wrapper block listing those failed criteria and quoting that feedback verbatim; for `GenerationFailed`, or `ValidationFailed` with nothing to relay, `P` = original `composed_prompt` unchanged. The wrapper is minimal, adds no substantive briefing instructions, does not duplicate the US-12 prompt design, carries no US-14 criteria, and is a single replaceable constant (approved decision 3). Always preserve `student_deidentified_hash` / `prediction` / `features` / `instructions_id`. (depends on T007)
- [X] T009 [US1] In `student_attrition_risk_app/src/student_attrition_risk/main.py`, `build_service` constructs `retry_workflow = SingleRetryWorkflow(generation_provider=generation_provider, validator=validator)` **unconditionally** (same instances passed to `StudentService`; no feature flag — approved decision 2), replacing `RetryNotConfigured()`. No other wiring change in this task. (depends on T007)
- [X] T010 [US1] Run `uv run ruff check .` and `uv run pytest tests/test_retry_workflow.py tests/test_briefing_retry_integration.py`; then `uv run pytest` for the full suite to confirm the Feature-001 tests (`test_briefing_orchestration.py`, `test_student_service.py`, `test_api.py`, `test_mcp_tools.py`) still pass with `SingleRetryWorkflow` wired.

**Checkpoint**: A first-attempt failure now recovers via one retry; `attempt_count == 2` on success; MVP is demonstrable.

---

## Phase 4: User Story 2 — Fail safely when the retry also does not produce a valid briefing (Priority: P2)

**Goal**: When the single retry also fails, terminate with the existing application-visible
briefing-failure result carrying the correct last-failure category, perform no third attempt,
store nothing, substitute no template, and leave any previously stored validated briefing in
place. (Behaviour is implemented in T007 + the pre-existing `StudentService._hand_off_to_retry`;
this phase proves it.)

**Independent Test**: With the scripted doubles failing on both attempts, `request_briefing`
performs exactly two generation attempts, raises `BriefingNotProducedError` with the right
category, and the store holds nothing new; with a prior validated briefing seeded, that briefing
is still returned by `get_stored_briefing` afterward.

### Tests for User Story 2

- [X] T011 [P] [US2] Extend `student_attrition_risk_app/tests/test_retry_workflow.py`: attempt-2 generation raises a non-`ConfigurationError` ⇒ `TerminalFailure(category="generation")`; attempt-2 draft fails revalidation ⇒ `TerminalFailure(category="validation")`; across a full `run`, `generate` is called exactly once and `validate` at most once (no third attempt); attempt-2 `generate` raising `ConfigurationError` ⇒ `run` re-raises it (never a `TerminalFailure`, never templated).
- [X] T012 [P] [US2] Extend `student_attrition_risk_app/tests/test_briefing_retry_integration.py`: two failed attempts through `StudentService` ⇒ `BriefingNotProducedError` with category `generation` and, separately, `validation`; `get_stored_briefing` returns nothing new (FR-016/FR-017); a `regenerate=True` request that fails both attempts for a student with a seeded prior briefing leaves that prior briefing as the one returned by `get_stored_briefing` (FR-018); no deterministic/template briefing is ever returned or stored; the terminal log line is metadata-only. Also cover the **successful retry with a failing persistence boundary**: a validation-fail-then-pass sequence whose `store.save_validated` raises `BriefingStorageError` surfaces that error through the existing `StudentService._persist` path (the existing storage-error result / 503), the request is not reported successful, and any prior stored briefing for that student is left intact (FR-020; spec Edge Case "The persistence boundary fails when storing the validated retry briefing").
- [X] T013 [US2] Run `uv run pytest tests/test_retry_workflow.py tests/test_briefing_retry_integration.py` and the Feature-001 orchestration suites (`tests/test_briefing_orchestration.py`, `tests/test_api.py`, `tests/test_mcp_tools.py`); confirm the `502` category mapping and `ConfigurationError → 503` path are unchanged. `uv run ruff check .`.

**Checkpoint**: The exceptional path is bounded and safe; US1 + US2 both pass independently.

---

## Phase 5: User Story 3 — Persist validated briefings in governed Unity Catalog Volume storage (Priority: P3)

**Goal**: A concrete `VolumeBriefingStore` implementing the existing `BriefingStore` boundary,
backed by a configurable Unity Catalog Volume, one JSON file per validated briefing, append-only
with no pruning, most-recent retrieval by filename, explicit "none available", storage failures
surfaced as `BriefingStorageError`. Selected by `BRIEFING_VOLUME`; `InMemoryBriefingStore`
otherwise.

**Independent Test**: Exercise `VolumeBriefingStore` through the existing store-contract
scenarios with `FakeFilesClient` — save/retrieve, none-available, most-recent, storage failure —
with no retry workflow involved and no change to `StudentService`.

### Tests for User Story 3

- [X] T014 [P] [US3] Extend `student_attrition_risk_app/tests/test_config.py`: a valid `/Volumes/<catalog>/<schema>/<volume>` value sets `Settings.briefing_volume`; a value missing the `/Volumes/` prefix, with fewer than three segments, or with unsafe characters raises `ConfigurationError`; a blank/unset value leaves `briefing_volume` as `None`.
- [X] T015 [US3] Add a `briefing_volume: str | None` field to `Settings` and a `validate_volume_path(path: str) -> str` helper to `student_attrition_risk_app/src/student_attrition_risk/config.py` (mirrors `validate_table_identifier`: must start `/Volumes/`, ≥3 safe-name segments after it). `Settings.from_env` reads `BRIEFING_VOLUME`, treats blank as `None`, and calls `validate_volume_path` only when non-blank. No OpenAI settings. (blocks T017, T018; needed by T014)
- [X] T016 [P] [US3] Write `student_attrition_risk_app/tests/test_volume_briefing_store.py` using `FakeFilesClient` from `tests/doubles.py`, per `contracts/volume-briefing-store.md`: `save_validated` then `get_latest_validated` returns an equal `ValidatedBriefing` and `has_validated` is `True`; unknown hash ⇒ `None` / `False`; two saves ⇒ the later (greater filename) briefing is returned and the first file still exists; `upload` raising ⇒ `BriefingStorageError` with any prior latest file untouched; `download` / `list_directory_contents` raising a non-not-found error ⇒ `BriefingStorageError` (distinct from `None`); the written body is `ValidatedBriefing` JSON only (no prompt key, no secret); the four Feature-001 `tests/test_briefing_store.py` scenarios pass against `VolumeBriefingStore` (parity, SC-010). (fails until T017)
- [X] T017 [US3] Implement `VolumeBriefingStore` in `student_attrition_risk_app/src/student_attrition_risk/briefing_store.py` per `contracts/volume-briefing-store.md`: `__init__(settings: Settings, files=None)` with `files` defaulting to `databricks.sdk.WorkspaceClient().files`; `save_validated(briefing)` ⇒ `files.upload(f"{settings.briefing_volume}/{briefing.student_deidentified_hash}/{generated_at:%Y%m%dT%H%M%S%fZ}-attempt{briefing.attempt_count}-{token}.json", briefing.model_dump_json(), overwrite=False)`, any Files-API error ⇒ `raise BriefingStorageError(...) from exc`; `get_latest_validated(hash)` ⇒ `list_directory_contents` the student dir, take the lexicographically greatest filename, `download`, parse JSON ⇒ `ValidatedBriefing`, empty/missing dir ⇒ `None`, non-not-found error ⇒ `BriefingStorageError`; `has_validated(hash)` ⇒ `True` iff ≥1 file. Append-only — never overwrite or delete (approved decision 4). Keep `InMemoryBriefingStore` unchanged. (depends on T015)
- [X] T018 [US3] In `student_attrition_risk_app/src/student_attrition_risk/main.py`, `build_service` sets `store = VolumeBriefingStore(settings) if settings.briefing_volume else InMemoryBriefingStore()`, replacing the unconditional `InMemoryBriefingStore()`. (depends on T009 — same function — and T015, T017)
- [X] T019 [P] [US3] Add `BRIEFING_VOLUME=` (blank) to `student_attrition_risk_app/.env.example` and a `BRIEFING_VOLUME` env entry with an empty value to `student_attrition_risk_app/app.yaml`. Do not set a real `/Volumes/...` path (approved decision 1).
- [X] T020 [US3] Run `uv run ruff check .` and `uv run pytest tests/test_volume_briefing_store.py tests/test_config.py`; then `uv run pytest` full suite, confirming `tests/test_briefing_store.py` and all Feature-001 suites remain green with `BRIEFING_VOLUME` unset (in-memory path).

**Checkpoint**: All three user stories pass independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 [P] Update `student_attrition_risk_app/README.md` to document the single-retry workflow (`SingleRetryWorkflow`, exactly one retry, `attempt_count = 2`), the governed `VolumeBriefingStore` (append-only, one JSON file per validated briefing, most-recent retrieval), and the `BRIEFING_VOLUME` setting (blank ⇒ in-memory store).
- [X] T022 From `student_attrition_risk_app/`, run the full merge gate: `uv run ruff check .` and `uv run pytest` — all Feature-001 and Feature-002 suites green.
- [X] T023 Walk the offline sections of `specs/002-briefing-retry-and-storage/quickstart.md` (retry-workflow table, governed-store table, store-selection) and confirm each stated expectation holds.

---

## Dependencies & Execution Order

### Phase order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** → **Phase 3 (US1)** → **Phase 4 (US2)** → **Phase 5 (US3)** → **Phase 6 (Polish)**.
- US2 depends on US1 implementation (T007–T008) being in place — it is the terminal half of the same `run` method plus the existing service mapping; US2 adds only tests + verification.
- US3 is functionally independent of US1/US2 and could be built in parallel after Phase 2 by a second contributor, **except** T018 shares `main.py` with T009 and must follow it.

### Key task dependencies

- T002 → T003, T007
- T004 → T005, T006, T011, T012, T016
- T007 → T008, T009; T007+T008 → T010
- T009 → T018 (same file)
- T015 → T016 (test expectations), T017, T018
- T017 → T018, T020

### Parallel opportunities

- Phase 2: **T002** and **T004** in parallel.
- US1: **T005** and **T006** in parallel (both new test files), before/alongside T007–T009.
- US2: **T011** and **T012** in parallel.
- US3: **T014**, **T016**, and **T019** in parallel; T015 then T017 then T018 are sequential.

## Parallel Example: User Story 1

```bash
# Author both US1 test files together:
Task: "Write tests/test_retry_workflow.py US1 scenarios (T005)"
Task: "Write tests/test_briefing_retry_integration.py US1 case (T006)"
# Then implement in retry_workflow.py sequentially: T007 → T008, then wire T009.
```

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 (T001) → Phase 2 (T002–T004) → Phase 3 (T005–T010).
2. **Stop and validate**: a first-attempt failure recovers via exactly one retry;
   `attempt_count == 2`; Feature-001 suites still green.

### Incremental delivery

1. Setup + Foundational → shared factory and doubles ready.
2. US1 → single-retry recovery (MVP).
3. US2 → bounded, safe terminal failure (tests + verification).
4. US3 → governed Unity Catalog Volume storage, selected by `BRIEFING_VOLUME`.
5. Polish → docs + full gate + quickstart walk.

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- No change to `ports.py`, `api.py`, `mcp_server.py`, `briefing_provider.py`, the repository,
  or any notebook. `student_service.py` change is limited to the T003 delegation.
- No new runtime dependency — `databricks-sdk` already provides the Volume Files API.
- Verify each new test fails before its implementation task, then passes after.
- No Git/GitHub operations.
