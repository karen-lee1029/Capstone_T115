---
description: "Task list for Feature-001 — Databricks Application Backend (US-08)"
---

# Tasks: Feature-001 — Databricks Application Backend (US-08)

**Input**: Design documents from `specs/001-advisor-briefing-backend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md,
`.specify/memory/constitution.md`, and the approved planning decisions (plan.md → *Approved
planning decisions*, 2026-09-03).

**Scope guard**: Feature-001 is strictly **US-08**. Do not implement functionality deferred to
US-09…US-26. The generation, instructions, validation, retry, and persistence *seams* are
defined here with **placeholder implementations only**; their concrete behaviour is US-13
(generation), US-12 (final prompt/instructions/criteria), US-14 (validation), US-15 (retry +
governed Unity Catalog Volume storage), and US-09/10/11 (dashboard). Do not modify the ML model
or synthetic-data-generation notebooks. No new dependencies, no refactoring, no cleanup or
optimisation beyond what the plan requires.

**Tests**: included — the feature's Success Criteria (SC-001…SC-012) and plan.md → *Proportionate
testing* define them. All tests are offline (mock repository, in-memory store, stub seams); no
live workspace, no network.

**Path root**: `student_attrition_risk_app/` (the existing package). Source:
`student_attrition_risk_app/src/student_attrition_risk/`. Tests:
`student_attrition_risk_app/tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` for user-story phases only

---

## Phase 1: Setup

**Purpose**: baseline confirmation and the read-side configuration the backend needs.

- [ ] T001 From `student_attrition_risk_app/`, run `uv sync --dev`, `uv run ruff check .`, and `uv run pytest`; confirm a green baseline before any change (records the starting state; no code change).
- [ ] T002 [P] Add `course_table` and `teaching_period_table` to `student_attrition_risk_app/src/student_attrition_risk/config.py` (`Settings` dataclass + `Settings.from_env`), each defaulting to the repository-confirmed three-part name in research.md R1 (`workspace.student_aggregate.dwh_curriculum__course`, `workspace.student_aggregate.dwh_learning_and_teaching__teaching_period`), validated with the existing `validate_table_identifier`; an empty value disables the corresponding join. Do not add any OpenAI or Volume setting.
- [ ] T003 [P] Add `DATABRICKS_COURSE_TABLE=` and `DATABRICKS_TEACHING_PERIOD_TABLE=` (empty) to `student_attrition_risk_app/.env.example`. No secret values.
- [ ] T004 Add accept/reject cases for the two new settings to `student_attrition_risk_app/tests/test_config.py` (valid three-part name accepted; malformed rejected via `ConfigurationError`; blank tolerated). Depends on T002.

**Checkpoint**: configuration in place; baseline green.

---

## Phase 2: Foundational (blocking prerequisites for US1, US2, US3)

**Purpose**: the shared data types, the five seam interfaces, the placeholder seam
implementations, the 21-feature repository retrieval, the mock fixtures, and the service /
composition-root skeleton. No user-story orchestration is implemented here.

**CRITICAL**: no user-story phase can begin until this phase is complete.

- [ ] T005 [P] Add the shared briefing data types to `student_attrition_risk_app/src/student_attrition_risk/models.py` per data-model.md: an `UNAVAILABLE` sentinel; `ApprovedModelFeatureValues` (ordered mapping `feature_name -> value | UNAVAILABLE`); `BriefingGenerationContext` (`student_deidentified_hash`, `prediction`, `features`, `instructions_id`, `composed_prompt`); `DraftBriefing`; `ValidationOutcome` (`passed`, `failed_criteria`, `feedback`, `validator_id`); `FirstAttemptOutcome` (`GenerationFailed{category}` | `ValidationFailed{outcome}`); `BriefingOutcome` (`Produced{briefing}` | `TerminalFailure{category}`); `ValidatedBriefing` (fields per data-model.md incl. `source`, `validated`, `validator_id`, `generated_at`, `attempt_count`, `mlflow_run_id`, `risk_percentage`, `at_risk_flag`, `prediction_threshold`, `scored_at`). Leave all existing models intact.
- [ ] T006 [P] Add the five seam `Protocol`s to `student_attrition_risk_app/src/student_attrition_risk/ports.py`: `GenerationProvider.generate(context) -> DraftBriefing` (raises on a pre-draft failure); `BriefingInstructions.compose(context) -> str` plus an `instructions_id`; `BriefingValidator.validate(draft, context) -> ValidationOutcome`; `RetryWorkflow.run(context, first_outcome) -> BriefingOutcome`; `BriefingStore` with `has_validated(hash) -> bool`, `get_latest_validated(hash) -> ValidatedBriefing | None`, `save_validated(briefing) -> None`. Add `get_model_features(student_hash) -> ApprovedModelFeatureValues | None` to the existing `StudentRepository` protocol. Depends on T005.
- [ ] T007 [P] Add typed service exceptions to `student_attrition_risk_app/src/student_attrition_risk/student_service.py`: `StudentNotAtRiskError`, `BriefingNotProducedError` (carries `category` = `"generation"` | `"validation"`), `BriefingStorageError`. Keep `StudentNotFoundError`. No behaviour change yet.
- [ ] T008 [P] Create `student_attrition_risk_app/src/student_attrition_risk/briefing_instructions.py`: `InterimInstructions` implementing `BriefingInstructions` — `instructions_id = "interim-default"`; `compose` reuses the existing safe proof-of-concept `_prompt` text from `briefing_provider.py` and renders the 21 feature values (including `UNAVAILABLE`) as labelled, explicitly non-causal context. Module docstring states the final prompt / sections / language are US-12. Depends on T005, T006.
- [ ] T009 [P] Create `student_attrition_risk_app/src/student_attrition_risk/briefing_validation.py`: `InterimValidator` implementing `BriefingValidator` — always returns `ValidationOutcome(passed=True, failed_criteria=[], feedback=None, validator_id="interim-pass-through")`. Module docstring states this is interim development behaviour, not the final Structured Advisor Briefing validation (US-14), and that it invents no acceptance criteria. Depends on T005, T006.
- [ ] T010 [P] Create `student_attrition_risk_app/src/student_attrition_risk/briefing_store.py`: `InMemoryBriefingStore` implementing `BriefingStore` — a dict of per-hash ordered `ValidatedBriefing` lists; `save_validated` appends and never removes; `get_latest_validated` returns the last entry or `None`; `has_validated` returns presence. Module docstring states the governed Unity Catalog Volume implementation is US-15. Depends on T005, T006.
- [ ] T011 [P] Create `student_attrition_risk_app/src/student_attrition_risk/retry_workflow.py`: `RetryNotConfigured` implementing `RetryWorkflow` — `run(context, first_outcome)` performs no generation and returns `BriefingOutcome.TerminalFailure(first_outcome.category)`. Module docstring states the concrete one-retry behaviour is Feature-002 / US-15. Depends on T005, T006.
- [ ] T012 [P] In `student_attrition_risk_app/src/student_attrition_risk/briefing_provider.py` add `StubGenerationProvider` implementing `GenerationProvider` — `generate` raises a "briefing generation is not configured" `ConfigurationError`. Leave `TemplateBriefingProvider` and `DatabricksModelBriefingProvider` untouched and unwired (concrete generation is US-13). Depends on T005, T006.
- [ ] T013 In `student_attrition_risk_app/src/student_attrition_risk/student_repository.py` add a `MODEL_FEATURE_COLUMNS` constant holding the authoritative 21-feature definition from research.md R1 (final name, role, source table) — **leave `SNAPSHOT_COLUMNS` and `get_snapshot` unchanged** — and implement `DatabricksStudentRepository.get_model_features(student_hash)`: select the 16 fact-owned columns from the fact table, `LEFT JOIN` `settings.course_table` on `course_key_hash` for the 4 course-dimension columns, `LEFT JOIN` `settings.teaching_period_table` on `teaching_period_key_hash` for `teaching_period`; parameterised query; per-source-table `information_schema.columns` check so an absent column produces an `UNAVAILABLE` marker rather than an error; return `None` only when the hash is absent from the fact table. Read-only; raw values only — no encoding, imputation, or other ML transformation (accepted risk TR-1). Depends on T002, T005, T006.
- [ ] T014 In `student_attrition_risk_app/src/student_attrition_risk/student_repository.py` update `MockStudentRepository`: implement `get_model_features` returning a representative 21-key mapping with at least one `UNAVAILABLE` (leave the existing `get_snapshot` mock intact); keep `synthetic-student-001` (flag `True`) and `synthetic-student-002` (flag `False`); add `synthetic-student-003` (flag `True`) for tests to seed as the "already has a validated briefing" case. Depends on T005, T013 (same file — sequential).
- [ ] T015 In `student_attrition_risk_app/src/student_attrition_risk/student_service.py` change `StudentService.__init__` to accept `repository`, `generation_provider`, `instructions`, `validator`, `retry_workflow`, and `store`; add a module-level `logging.getLogger(__name__)` and a small metadata-only log helper that accepts only `student_deidentified_hash`, `outcome`, `attempt_count`, `validator_id`, timestamps, and an exception class — and rejects / never emits prompt text, briefing text, or secrets. Leave the existing `generate_briefing` in place for now; it is removed in T041 once its callers are re-pointed. Depends on T006, T007.
- [ ] T016 In `student_attrition_risk_app/src/student_attrition_risk/main.py` update `build_service` to construct and inject the Feature-001 placeholder seams — `StubGenerationProvider`, `InterimInstructions`, `InterimValidator`, `RetryNotConfigured`, `InMemoryBriefingStore` — with the repository, and adjust the composition so the module imports cleanly. Do not wire `TemplateBriefingProvider` / `DatabricksModelBriefingProvider`. Depends on T008, T009, T010, T011, T012, T015.
- [ ] T017 [P] Create `student_attrition_risk_app/tests/test_briefing_seams.py`: `InterimInstructions.compose` output contains all 21 feature labels and marks features as non-causal context (mirrors the existing `test_template_briefing.py` wording-assertion style); `StubGenerationProvider.generate` raises "not configured"; `InterimValidator.validate` returns `passed` with `validator_id="interim-pass-through"` and empty criteria; `RetryNotConfigured.run` returns `TerminalFailure` carrying the first-attempt category. Verifies FR-010, FR-014, FR-016, FR-019, SC-012. Depends on T008, T009, T011, T012.
- [ ] T018 [P] Create `student_attrition_risk_app/tests/test_briefing_store.py`: `InMemoryBriefingStore` — `save_validated` stores exactly what it is given; `get_latest_validated` returns the most recently saved; multiple saves for one hash → latest wins; `has_validated` reflects presence; unknown hash → `None`. Verifies the FR-025/FR-030 seam contract. Depends on T010.
- [ ] T019 [P] Add a `get_model_features` shape test to `student_attrition_risk_app/tests/test_student_service.py`: `MockStudentRepository.get_model_features` returns a mapping whose key set is **exactly** the 21 feature names from research.md R1 — never a reduced set; an `UNAVAILABLE` marker is preserved; a hash absent from the source yields `None`. Verifies FR-003, FR-007, and FR-008's non-reduction guarantee. Depends on T013, T014.

**Checkpoint**: seams, types, repository retrieval, mock fixtures, and the service /
composition-root skeleton are ready. User-story phases can begin.

---

## Phase 3: User Story 1 — Coordinate a briefing request end-to-end through the integration seams (Priority: P1) — MVP

**Goal**: `StudentService.request_briefing` coordinates the success path, the at-risk
precondition, the return-existing path, and regeneration routing, exposed on REST and MCP, with
the Streamlit screen kept compatible.

**Independent test**: with the mock repository, a stub generation seam, a stub validation seam
set to pass, and `InMemoryBriefingStore`, a briefing request assembles a context containing the
risk result and all 21 feature values, calls the seams in the FR-033 order, and returns a
validated briefing the in-memory seam recorded; swapping the stubs for refuse / return-existing
/ regenerate values exercises the other US1 paths.

### Tests for User Story 1

- [ ] T020 [P] [US1] Create `student_attrition_risk_app/tests/test_briefing_orchestration.py` with success/precondition tests using local stub seams: (a) flagged student, no existing briefing, `StubValidator(passed=True)` → seams invoked in the FR-033 order, `BriefingGenerationContext` carries all 21 feature values + the risk result, `save_validated` called once, `ValidatedBriefing` returned; (b) the at-risk decision uses `attrition_risk_flag` only — a record with flag `False` is refused even at a high percentage, a record with flag `True` proceeds (FR-005); (c) not-flagged known student → `StudentNotAtRiskError`, zero generation-seam calls (FR-034, SC-010); (d) student with an existing validated briefing + no `regenerate` → returns the stored briefing (`source="stored"`), zero generation-seam calls (FR-035, SC-011); (e) `regenerate=true` for that student → full seam run, success supersedes as the latest (FR-036); (f) `regenerate=true` terminal failure → the previous validated briefing is retained (FR-037). Covers US1 scenarios 1–8, SC-001.
- [ ] T021 [P] [US1] Add `POST /api/students/{hash}/briefing` cases to `student_attrition_risk_app/tests/test_api.py`: 200 returns the stored briefing when one exists; 200 returns a generated briefing on a fresh run (stub seams); 409 for a not-flagged student; 404 for an unknown hash; `?regenerate=true` forces a fresh run. Matches contracts/rest-api.md.
- [ ] T022 [P] [US1] Update `student_attrition_risk_app/tests/test_mcp_tools.py` for `generate_student_briefing`: the `regenerate` parameter is accepted; the tool returns the stored briefing when one exists; a not-flagged student yields the tool error "student is not flagged at risk"; an unknown hash yields a not-found tool error.

### Implementation for User Story 1

- [ ] T023 [US1] Implement `StudentService.request_briefing(student_hash, regenerate=False)` in `student_attrition_risk_app/src/student_attrition_risk/student_service.py` following the contracts/internal-seams.md "Orchestration call order" steps 1–8: `get_prediction` → `StudentNotFoundError`; `attrition_risk_flag` false → `StudentNotAtRiskError`; if not `regenerate` and `store.has_validated` → return `store.get_latest_validated` with `source="stored"`; otherwise assemble `ApprovedModelFeatureValues` via `repository.get_model_features`, build `BriefingGenerationContext` using `instructions.compose` / `instructions.instructions_id`; invoke `generation_provider.generate` once; on a pre-draft failure build `FirstAttemptOutcome.GenerationFailed(category)`; otherwise `validator.validate` → on pass build `ValidatedBriefing`, call `store.save_validated`, return it; on fail build `FirstAttemptOutcome.ValidationFailed(outcome)`; call `retry_workflow.run(context, first_outcome)` exactly once → `Produced` ⇒ `save_validated` if not already stored, return; `TerminalFailure(c)` ⇒ raise `BriefingNotProducedError(c)`. Emit one metadata-only log line per terminal outcome. Never substitute a template/deterministic briefing (FR-020). Delivers FR-009, FR-013, FR-015, FR-018, FR-019, FR-033, FR-034, FR-035, FR-036, FR-037. Depends on T015, T016.
- [ ] T024 [US1] Replace the existing `POST /api/students/{student_hash}/briefing` handler in `student_attrition_risk_app/src/student_attrition_risk/api.py` with one that takes `regenerate: bool = False` (query) and calls `service.request_briefing`; map `StudentNotFoundError`→404 "Student hash not found", `StudentNotAtRiskError`→409 "Student is not flagged at risk", `ConfigurationError`→503 "Briefing generation is not configured" (or the constraint message for FR-008), and any other data-source `Exception`→503 "Databricks data source unavailable"; return the `ValidatedBriefing` on success. (Retry-terminal 502 and storage 503 are added in US3.) Depends on T023.
- [ ] T025 [US1] Update `generate_student_briefing` in `student_attrition_risk_app/src/student_attrition_risk/mcp_server.py` to `generate_student_briefing(student_hash, regenerate: bool = False)` delegating to `service.request_briefing`; surface `StudentNotAtRiskError`, `StudentNotFoundError`, and `ConfigurationError` as clear tool errors; return `model_dump(mode="json")`. No SQL. Depends on T023.
- [ ] T026 [US1] Update `student_attrition_risk_app/src/student_attrition_risk/ui.py` minimally so the existing single-student screen runs against the changed service: the briefing action calls `service.request_briefing(hash)` and shows the returned briefing or the explicit error message. No new advisor-facing behaviour (US-09/10/11 own that). Depends on T023.

**Checkpoint**: US1 is functional and independently testable — happy path, at-risk
precondition, return-existing, and regenerate routing on REST and MCP.

---

## Phase 4: User Story 2 — Expose backend retrieval of a stored validated briefing (Priority: P2)

**Goal**: a backend operation that returns the most recent stored validated briefing for a
student, read through the persistence seam, without invoking generation.

**Independent test**: with `InMemoryBriefingStore` holding one validated briefing for a student,
the retrieval operation returns it; for a student with none it returns an explicit "none
available" result; drafts and failed briefings are never returned (only validated briefings are
ever stored).

### Tests for User Story 2

- [ ] T027 [P] [US2] Add retrieval tests to `student_attrition_risk_app/tests/test_briefing_orchestration.py`: `get_stored_briefing` returns the latest validated briefing when present; returns an explicit "none available" result when absent; an unknown hash → `StudentNotFoundError`; a draft/failed briefing is never returned. Covers US2 scenarios 1–4, SC-002.
- [ ] T028 [P] [US2] Add `GET /api/students/{hash}/briefing` cases to `student_attrition_risk_app/tests/test_api.py`: 200 with the latest validated briefing; 404 "No validated briefing available" when none; 404 for an unknown hash. Matches contracts/rest-api.md.
- [ ] T029 [P] [US2] Add `get_student_briefing` to `student_attrition_risk_app/tests/test_mcp_tools.py` and update the registered-tool-set assertion to the five tools (`get_student_prediction`, `get_student_profile`, `get_high_risk_students`, `generate_student_briefing`, `get_student_briefing`).

### Implementation for User Story 2

- [ ] T030 [US2] Implement `StudentService.get_stored_briefing(student_hash)` in `student_attrition_risk_app/src/student_attrition_risk/student_service.py`: confirm the student exists via `get_prediction` (→ `StudentNotFoundError`), then `store.get_latest_validated`; `None` → an explicit "none available" result object; no at-risk check, no generation. Emit a metadata-only log line. Delivers FR-028, FR-029, FR-030. Depends on T023.
- [ ] T031 [US2] Add `GET /api/students/{student_hash}/briefing` to `student_attrition_risk_app/src/student_attrition_risk/api.py` calling `service.get_stored_briefing`; map "none available" → 404 "No validated briefing available", `StudentNotFoundError`→404, and a store/data-source failure → 503. Depends on T030.
- [ ] T032 [US2] Add a `get_student_briefing(student_hash)` tool to `student_attrition_risk_app/src/student_attrition_risk/mcp_server.py` delegating to `service.get_stored_briefing`; return the validated briefing or `{"available": false, "student_hash": <hash>}`. Depends on T030.

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 — Safe outcome handling when the first attempt does not yield a validated briefing (Priority: P3)

**Goal**: verify and finish the failure guarantees — first-attempt failure hands off to the
retry seam exactly once, a retry-seam terminal outcome maps to a single explicit error, no
template is ever substituted as success, a persistence-seam failure is surfaced without losing
the previous briefing, and every terminal outcome is logged with metadata only.

**Independent test**: with the generation seam stubbed to fail, then separately the validation
seam stubbed to fail, the backend invokes the retry seam exactly once and performs no
generation itself; with `RetryNotConfigured`, the backend returns an explicit error and
`InMemoryBriefingStore` holds no new briefing for that request.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add failure-path tests to `student_attrition_risk_app/tests/test_briefing_orchestration.py`: (a) `StubGenerationProvider` raising → `FirstAttemptOutcome.GenerationFailed` passed to the retry seam; with `RetryNotConfigured` → `BriefingNotProducedError("generation")`, nothing stored; (b) `StubValidator(passed=False, failed_criteria=[…], feedback="…")` → `ValidationFailed` passed to the retry seam; with `RetryNotConfigured` → `BriefingNotProducedError("validation")`, nothing stored; (c) on any failure, no deterministic/template briefing is returned or stored (SC-003); (d) `save_validated` raising `BriefingStorageError` → surfaced, and any previous validated briefing is intact (FR-024, FR-037); (e) the retry seam is invoked at most once and never by the normal path itself (SC-009). Covers US3 scenarios 1–4.
- [ ] T034 [P] [US3] Add a logging test to `student_attrition_risk_app/tests/test_briefing_orchestration.py` (using `caplog`): after any run, captured records contain `student_deidentified_hash` / outcome / `attempt_count` / `validator_id` but no prompt text, no briefing text, and no secret. Verifies FR-031, FR-032, SC-005.
- [ ] T035 [P] [US3] Add status-mapping cases to `student_attrition_risk_app/tests/test_api.py`: a retry-seam terminal outcome → 502 with the `generation` / `validation` category in the detail text (both map to 502, not a separate code); a persistence-seam failure → 503 "Validated briefing could not be stored"; an unconfigured generation seam → 503 "Briefing generation is not configured". Matches the approved status set (research.md R9).

### Implementation for User Story 3

- [ ] T036 [US3] Extend the `POST /api/students/{hash}/briefing` handler in `student_attrition_risk_app/src/student_attrition_risk/api.py` to map `BriefingNotProducedError`→502 with detail `"Briefing could not be produced (<category>)"` (category text only; no separate code) and `BriefingStorageError`→503 "Validated briefing could not be stored". Depends on T024, T030.
- [ ] T037 [US3] Map `BriefingNotProducedError` and `BriefingStorageError` to the tool-error messages from contracts/mcp-tools.md in `generate_student_briefing` in `student_attrition_risk_app/src/student_attrition_risk/mcp_server.py`. Depends on T025.
- [ ] T038 [US3] Finalise the metadata-only log calls for every terminal branch of `request_briefing` and `get_stored_briefing` in `student_attrition_risk_app/src/student_attrition_risk/student_service.py` (`generated`, `returned_existing`, `not_at_risk`, `not_found`, `terminal_generation`, `terminal_validation`, `storage_error`) using the T015 helper; confirm no prompt/briefing text/secret is passed to the logger. Depends on T023, T030.

**Checkpoint**: all three stories independently functional; failure guarantees verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T039 [P] Update `student_attrition_risk_app/README.md`: the changed `POST /api/students/{hash}/briefing` (get-or-create + `?regenerate=true`), the new `GET /api/students/{hash}/briefing`, the new `get_student_briefing` MCP tool, the `DATABRICKS_COURSE_TABLE` / `DATABRICKS_TEACHING_PERIOD_TABLE` settings, the five integration seams and their placeholder status, and the US-08 backlog boundary (concrete generation/validation/retry/storage = US-12/13/14/15; dashboard = US-09/10/11).
- [ ] T040 [P] Confirm `student_attrition_risk_app/pyproject.toml` and `student_attrition_risk_app/uv.lock` are unchanged (no new dependency) and `.env.example` contains no secret.
- [ ] T041 Remove the superseded `generate_briefing` method and its `except Exception → TemplateBriefingProvider` fallback from `student_attrition_risk_app/src/student_attrition_risk/student_service.py`; grep the package to confirm no remaining reference (`api.py`, `mcp_server.py`, `ui.py`, and all tests now use `request_briefing` / `get_stored_briefing`). No code path may retain the silent-template behaviour (FR-020, constitution IV). Depends on T024, T025, T026, T038.
- [ ] T042 Run the full gate from `student_attrition_risk_app/`: `uv run ruff check .` and `uv run pytest` — all green. Depends on all prior tasks.
- [ ] T043 Execute the `specs/001-advisor-briefing-backend/quickstart.md` offline (mock-mode) walk-through and confirm every documented status/outcome, including `POST` on an unconfigured backend returning 503 "Briefing generation is not configured" (never a template briefing). Depends on T042.

---

## Dependencies & Execution Order

### Phase order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** → **Phase 3 (US1)** → **Phase 4 (US2)** → **Phase 5 (US3)** → **Phase 6 (Polish)**.
- Phase 2 blocks every user-story phase.
- US2 and US3 build on US1's `request_briefing` and the `api.py` / `mcp_server.py` handlers, so
  they extend the same files — run them in priority order rather than fully in parallel. Each
  story remains **independently testable** (its own tests exercise its own inputs and pass
  without the later stories).

### Key task dependencies

- T005 → T006, T008, T009, T010, T011, T012, T013, T015
- T002 → T004, T013
- T013 → T014, T019
- T008–T012, T015 → T016
- T015, T016 → T023
- T023 → T024, T025, T026, T030
- T030 → T031, T032
- T024, T030 → T036 ; T025 → T037 ; T023, T030 → T038
- T024, T025, T026, T038 → T041 (remove superseded `generate_briefing`) → T042 (gate) → T043 (quickstart)

### Parallel opportunities

- Setup: T002 and T003 in parallel; T004 after T002.
- Foundational: T005 and T007 in parallel; then T006; then T008/T009/T010/T011/T012 in parallel
  (distinct new files); T013 then T014 (same file, sequential); T015 then T016; T017/T018/T019
  in parallel once their targets exist.
- Within US1: T020/T021/T022 (tests) in parallel; implementation T023 then T024/T025/T026
  (T024 and T025 touch different files and can be parallel, T026 too).
- Within US2: T027/T028/T029 in parallel; T030 then T031/T032 in parallel.
- Within US3: T033/T034/T035 in parallel; T036/T037/T038 touch three different files and can be
  parallel.
- Polish: T039 and T040 in parallel; then T041 (remove superseded method); then T042 (gate); then T043 (quickstart).

## Parallel Example: User Story 1

```text
# Tests first (different files / new file sections):
Task T020: orchestration tests in student_attrition_risk_app/tests/test_briefing_orchestration.py
Task T021: POST cases in student_attrition_risk_app/tests/test_api.py
Task T022: generate_student_briefing cases in student_attrition_risk_app/tests/test_mcp_tools.py

# Then implementation:
Task T023: request_briefing in .../student_service.py
# then, in parallel:
Task T024: POST handler in .../api.py
Task T025: generate_student_briefing in .../mcp_server.py
Task T026: minimal ui.py compatibility
```

## Implementation Strategy

### MVP (Setup + Foundational + US1)

1. Phase 1 → Phase 2 → Phase 3.
2. Stop and validate: run `uv run pytest` — US1's orchestration, REST, and MCP tests pass with
   placeholder seams; `POST` on the default (unconfigured) backend returns an explicit 503, never
   a template briefing.
3. This is a demonstrable US-08 increment: risk data + 21 features retrieved and assembled, the
   request coordinated through all five seams, preconditions and return-existing enforced.

### Incremental delivery

- + US2 → backend retrieval of a stored validated briefing (REST `GET` + MCP tool).
- + US3 → the failure guarantees and metadata-only logging are verified and the 502 / 503
  mappings are complete.
- + Polish → README, remove the superseded `generate_briefing`, gate, quickstart validation.

### Explicitly NOT in these tasks (later backlog stories)

- Concrete OpenAI / generative integration, the `openai` dependency, `OPENAI_*` config — US-13.
- Final briefing prompt, sections, language guidance, acceptance-criteria content — US-12.
- Real acceptance-criteria validation behaviour — US-14.
- Concrete one-retry behaviour and the governed Unity Catalog Volume storage
  (`VolumeBriefingStore`, `BRIEFING_VOLUME`, path/format/naming/retention) — US-15
  (retry: Feature-002).
- Advisor-facing dashboard, at-risk display, student-selection interaction — US-09 / US-10 / US-11.
- End-to-end integration across all components — US-16; broad app / workflow testing — US-17 / US-18.
- Any change to the ML model or synthetic-data-generation notebooks.

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- `[Story]` labels appear only on Phase 3–5 tasks.
- Tests within a story are written before the implementation they verify and must fail first.
- Every test is offline: `MockStudentRepository`, `InMemoryBriefingStore`,
  `StubGenerationProvider` / `StubValidator`. No live workspace, no network.
- The five seams keep their interfaces stable so US-12/13/14/15 attach concrete implementations
  by swapping the object wired in `main.build_service` — no change to `request_briefing`.
