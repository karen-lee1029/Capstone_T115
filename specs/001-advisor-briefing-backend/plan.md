# Implementation Plan: Feature-001 — Databricks Application Backend (US-08)

**Branch**: `001-advisor-briefing-backend` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-advisor-briefing-backend/spec.md` (re-scoped to
US-08 on 2026-09-02).

## Summary

Feature-001 delivers **US-08 — the Databricks application backend**: it retrieves risk data and
the 21 approved machine-learning feature values from the governed Delta tables, and it
coordinates a Structured Advisor Briefing request end to end through four integration seams
(generation, instructions, validation, retry) plus a persistence/retrieval seam. It ships
minimal interim placeholders for those seams so the backend is runnable and testable now, and
it exposes the capability through the existing service + REST + MCP layers for the
advisor-facing stories to call.

The concrete generative integration (US-13), the final prompt/instructions/criteria (US-12),
the real validation behaviour (US-14), the concrete one-retry behaviour and the concrete
governed validated-briefing storage (US-15), and the dashboard (US-09/10/11) are **out of
Feature-001 scope** and attach later to the seams defined here.

Approach: **reuse and extend, not redesign**. The three interfaces stay over one
`StudentService`; SQL, generation, validation, retry, and persistence are adapters behind small
`Protocol` interfaces; the existing Databricks SQL client, `Settings` pattern, Pydantic models,
and typed-exception / explicit-status-mapping error convention are reused. New modules are added
only for the seam definitions and their interim placeholders.

## Technical Context

**Language/Version**: Python `>=3.11,<3.14` (unchanged).

**Primary Dependencies**: Existing only — FastAPI, Uvicorn, Streamlit, FastMCP, Pydantic v2,
`databricks-sdk`, `databricks-sql-connector`, httpx, websockets. Dev — pytest, pytest-asyncio,
ruff. **No new runtime dependency** (the `openai` SDK is added by US-13, not here).

**Storage**:
- *Read*: Databricks Delta via a SQL warehouse — the prediction table
  `workspace.student_aggregate.student_attrition_risk_prediction`, and, for the 21 features, the
  fact table
  `workspace.student_aggregate.rpt_student_management__fact__all_enrolment_eftsl__deidentified`
  left-joined to `dwh_curriculum__course` (`course_key_hash`) and
  `dwh_learning_and_teaching__teaching_period` (`teaching_period_key_hash`).
- *Write*: none in Feature-001. The persistence seam's in-memory implementation holds validated
  briefings for tests / local mode; the governed Unity Catalog Volume implementation is US-15.

**Testing**: pytest with mock repository, in-memory persistence seam, stub generation seam, and
stub validation seam. No network, no live workspace. Gate: `uv run ruff check .` and
`uv run pytest`.

**Target Platform**: Databricks App on serverless-compatible compute; Uvicorn on
`${DATABRICKS_APP_PORT}` via `app.yaml`.

**Project Type**: Single package, three interfaces over one service layer. Package:
`student_attrition_risk_app/src/student_attrition_risk/`.

**Performance Goals**: Backend orchestration overhead for non-generation paths (not-found,
not-flagged, return-existing) under ~1 s excluding downstream seam latency (spec SC-006).
Advisor-interactive workload — low concurrency.

**Constraints**: Deidentified hash only, no PII. Metadata-only logging — no full prompts, no
full briefing text, no secrets (spec FR-031/FR-032). ML and synthetic-data implementations are
read-only (constitution II, XVI). No new compute infrastructure.

**Scale/Scope**: ~1M synthetic rows in the prediction table; tens of concurrent advisors.
Implementation touches ~8 existing files and adds ~4 new modules plus their tests.

## Constitution Check

*Evaluated against `.specify/memory/constitution.md` v1.0.0. Re-checked after Phase 1 —
unchanged: PASS.*

| Principle | Assessment |
|---|---|
| I. Specification-Driven Development | PASS — every element traces to an FR / Clarification in the re-scoped spec. |
| II. Strict Scope Containment | PASS — strengthened by the 2026-09-02 correction: Feature-001 now modifies only its own backend files and defines seams instead of implementing US-12/13/14/15 work. Notebooks, `docs/`, data-generation code untouched. |
| III. Read Broadly, Write Narrowly | PASS — ML notebook inspected for the 21-feature list and join keys only. |
| IV. Minimal Necessary Change | PASS — reuses `StudentService`, `ports.py`, `DatabricksStudentRepository._query`, `create_sql_connection`, `config.Settings`, the models, and the API error convention. New modules are seam definitions + placeholders. Existing provider classes are left as-is. |
| V. Reuse and Extend Existing Architecture | PASS — three interfaces over one service; seams behind protocols; no parallel backend. |
| VI. No Unnecessary Complexity | PASS — 4 small new modules, 5 protocols, no new framework, no new dependency. Placeholders are trivial. |
| VII. Plan-Defined Implementation Structure | PASS — this plan names the files, seams, and contracts. |
| VIII. Application Technology Compatibility | PASS — Python, existing SQL client, existing Delta access. No external integration is introduced by Feature-001 (that is US-13). |
| IX. Separation of Responsibilities and Modularity | PASS — presentation / interface / orchestration / data access / generation / validation / retry / persistence each remain distinct; the seams are independently testable. |
| X. Security and Privacy | PASS — deidentified hash only; metadata-only logging; no secrets; the 21 features (incl. sensitive attributes) are carried as non-causal context. No external transmission occurs in Feature-001. |
| XI. Input Validation and Explicit Error Handling | PASS — hash bounds retained; table identifiers validated; typed service exceptions mapped explicitly; the silent template fallback is removed. |
| XII. Proportionate Testing | PASS — offline orchestration + seam tests only; broad end-to-end testing is US-17/18. |
| XIII. Human Review of AI-Generated Work | PASS — decisions needing sign-off listed below. |
| XIV. Documentation and Implementation Traceability | PASS — research / data-model / contracts / quickstart map FRs to design. |
| XV. Completion Means Specification Satisfaction | PASS — scope limited to FR-001…FR-039; nothing from US-12/13/14/15 pre-built. |
| XVI. Preserve Team Contributions | PASS — notebooks, docs, other modules untouched; existing provider classes kept. |
| XVII. Human-Controlled Version Control | PASS — no Git operations. |

**Gate result: PASS. Complexity Tracking empty.**

## Project Structure

### Documentation (this feature)

```text
specs/001-advisor-briefing-backend/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions on the deferred choices that remain in US-08
├── data-model.md        # Phase 1 — entities, the 21-feature contract, seam objects, state
├── quickstart.md        # Phase 1 — run and validate the backend with placeholder seams
├── contracts/
│   ├── rest-api.md      # REST endpoint contracts
│   ├── mcp-tools.md     # MCP tool contracts
│   └── internal-seams.md# The 5 seams and which backlog story owns each concrete impl
├── spec.md
├── checklists/requirements.md
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

All work is inside the existing package. Flat modules; no new sub-packages.

```text
student_attrition_risk_app/
├── README.md                         # MODIFY — document the new backend operations and seams (US-08 portion only)
├── .env.example                      # MODIFY — add DATABRICKS_COURSE_TABLE / DATABRICKS_TEACHING_PERIOD_TABLE (data retrieval only; no OpenAI/Volume keys)
├── src/student_attrition_risk/
│   ├── config.py                     # MODIFY — add course_table + teaching_period_table settings (validated via existing validate_table_identifier); add the 21-feature column set constant
│   ├── models.py                     # MODIFY — add ValidationOutcome, FirstAttemptOutcome, extend the briefing model; define (not persist) Workflow Metadata fields
│   ├── ports.py                      # MODIFY — add GenerationProvider, BriefingInstructions, BriefingValidator, RetryWorkflow, BriefingStore protocols; add get_model_features to StudentRepository
│   ├── student_repository.py         # MODIFY — add `get_model_features` (21 approved features: fact + 2 dimension joins, per-table availability tolerance) alongside the unchanged 11-field `get_snapshot`; enrich MockStudentRepository (not-at-risk + has-existing-briefing fixtures)
│   ├── briefing_instructions.py      # NEW — BriefingInstructions protocol impl: InterimInstructions (reuses the existing safe PoC prompt text; final content = US-12)
│   ├── briefing_validation.py        # NEW — BriefingValidator protocol impl: InterimValidator (pass-through, explicitly non-final; real criteria = US-14)
│   ├── briefing_store.py             # NEW — BriefingStore protocol impl: InMemoryBriefingStore (Feature-001 test/local double; governed Volume impl = US-15)
│   ├── retry_workflow.py             # NEW — RetryWorkflow protocol impl: RetryNotConfigured (terminal-failure passthrough; concrete retry = Feature-002 / US-15)
│   ├── briefing_provider.py          # MODIFY (light) — add StubGenerationProvider (non-final placeholder that raises "generation not configured"); keep TemplateBriefingProvider and DatabricksModelBriefingProvider untouched and unwired. Concrete OpenAI provider = US-13.
│   ├── student_service.py            # MODIFY — replace generate_briefing with request_briefing(hash, regenerate) + get_stored_briefing(hash); add typed errors; call the seams in the FR-033 order
│   ├── api.py                        # MODIFY — GET /briefing (retrieve); POST /briefing → get-or-create + ?regenerate=true; map new errors to status codes
│   ├── mcp_server.py                 # MODIFY — update generate_student_briefing (request semantics + regenerate); add get_student_briefing
│   ├── main.py                       # MODIFY — build_service wires the placeholder seams from settings
│   ├── ui.py                         # MODIFY (minimal) — keep the existing screen working against request_briefing / get_stored_briefing only; advisor-facing behaviour is US-09/10/11
│   ├── databricks_client.py          # READ-ONLY — reused unchanged
│   └── streamlit_host.py             # READ-ONLY — unchanged
└── tests/
    ├── test_student_service.py       # MODIFY — request_briefing / get_stored_briefing
    ├── test_api.py                   # MODIFY — new/changed routes and status codes
    ├── test_mcp_tools.py             # MODIFY — new/changed tools
    ├── test_config.py                # MODIFY — course/teaching-period table identifier validation
    ├── test_briefing_orchestration.py# NEW — the FR-033 sequence with stub seams: happy path, not-at-risk, return-existing, regenerate (success + terminal), generation-seam failure → retry seam, validation-seam failure → retry seam, retry seam terminal → explicit error, persistence-seam failure, no-template-as-success, metadata-only logging
    ├── test_briefing_store.py        # NEW — InMemoryBriefingStore seam contract: save only validated, get latest, none-available, most-recent selection
    └── test_briefing_seams.py        # NEW — InterimInstructions composes a prompt from the 21-feature context; InterimValidator identifies itself as non-final; RetryNotConfigured returns terminal failure; StubGenerationProvider raises "not configured"
```

**No changes** to `pyproject.toml` / `uv.lock` (no new dependency), `app.yaml` (no OpenAI /
Volume env), or any notebook / doc.

### Structure Decision

Extend the existing single package. Add four flat modules — one per new seam plus its interim
placeholder — and modify eight existing files. No sub-packages, no second service. This is the
smallest structure that makes the five seams independently testable and lets US-12/13/14/15
attach concrete implementations without changing the Feature-001 orchestration.

## Feature-001 ↔ downstream integration (US-12/13/14/15, Feature-002)

Feature-001 owns the orchestration and the seam interfaces; each concrete implementation is a
later story.

| Seam (Protocol) | Feature-001 provides | Concrete implementation |
|---|---|---|
| `GenerationProvider` | `StubGenerationProvider` (raises "generation not configured") | **US-13** — the OpenAI integration |
| `BriefingInstructions` | `InterimInstructions` (reuses the existing safe PoC prompt text) | **US-12** — the final prompt / sections / language |
| `BriefingValidator` | `InterimValidator` (pass-through, marked non-final) | **US-14** — the acceptance-criteria validation |
| `RetryWorkflow` | `RetryNotConfigured` (returns `TerminalFailure`) | **Feature-002 / US-15** — the one-retry behaviour |
| `BriefingStore` | `InMemoryBriefingStore` | **US-15** — the governed Unity Catalog Volume storage + most-recent retrieval |

Shared objects (`BriefingGenerationContext`, `ValidationOutcome`, `FirstAttemptOutcome`,
`BriefingOutcome`, the validated-briefing model) are defined once by Feature-001 in
`models.py` / `ports.py`; the downstream stories import rather than redefine them.
`main.build_service` selects the concrete implementation when configured, else the placeholder —
no Feature-001 orchestration change when a concrete one lands.

`student_service.request_briefing` calls `RetryWorkflow.run` exactly once, only inside a
generation/regeneration run, only when attempt 1 fails to produce a validated briefing
(FR-019, FR-033).

## Data retrieval and Delta Table integration (US-08 core)

- **Prediction result** (FR-002): reuse `DatabricksStudentRepository.get_prediction` unchanged.
  `MockStudentRepository` gains a not-at-risk fixture and a has-existing-briefing fixture.
- **21 approved features** (FR-003, FR-007): a new `get_model_features(student_hash)` reads the
  16 fact-owned columns from the fact table, `LEFT JOIN dwh_curriculum__course` on
  `course_key_hash` for 4 course-dimension columns, and `LEFT JOIN
  dwh_learning_and_teaching__teaching_period` on `teaching_period_key_hash` for
  `teaching_period`. Full list in `data-model.md` / `research.md` R1. Per-source-table
  `information_schema.columns` checks make an absent column an "unavailable" marker rather than
  a query error. A missing prediction row still stops the request (FR-023).
- **At-risk retrieval** (FR-005): the existing `get_high_risk_students` already filters on
  `attrition_risk_flag = TRUE`; it is retained as the backend risk-data retrieval that US-10
  consumes.
- **Config**: `config.py` adds `course_table` and `teaching_period_table` (defaults to the
  repository-confirmed three-part names; blank disables the corresponding join), validated via
  the existing `validate_table_identifier`. The 21 feature names live as a new
  `MODEL_FEATURE_COLUMNS` constant in `student_repository.py`; the existing `SNAPSHOT_COLUMNS` /
  `get_snapshot` (11 fields) are left unchanged for the profile endpoint.
- No change to any Delta table (FR-004). No app-side re-implementation of model preprocessing —
  raw approved feature values only.

## Generation seam (concrete implementation: US-13)

- New `GenerationProvider` protocol in `ports.py` (a draft-returning operation over the
  `BriefingGenerationContext`; raises on a pre-draft failure).
- Feature-001 ships `StubGenerationProvider` — it does not call any external service; it raises
  a "generation not configured" error so an unconfigured backend fails fast and explicitly,
  never returning a template as success (FR-014, FR-020).
- `student_service` invokes the seam once per run and maps its failure to
  `FirstAttemptOutcome.GenerationFailed` for the retry seam (FR-013, FR-019).
- The existing `TemplateBriefingProvider` and `DatabricksModelBriefingProvider` are left in the
  file untouched and unwired.

## Instructions seam (concrete implementation: US-12)

- New `BriefingInstructions` protocol: compose a prompt string from the context.
- Feature-001 ships `InterimInstructions`, reusing the existing safe PoC `_prompt` text (no
  causal/longitudinal claims, no sensitive inferences), rendering the 21 feature values as
  labelled context. It carries an `instructions_id` marking it interim. It does **not** define
  final sections or language guidance (US-12).

## Validation seam (concrete implementation: US-14)

- New `BriefingValidator` protocol: `validate(draft, context) -> ValidationOutcome`, where
  `ValidationOutcome` carries `passed`, optional `failed_criteria`, optional `feedback`, and a
  `validator_id`.
- Feature-001 ships `InterimValidator` — always `passed`, `validator_id="interim-pass-through"`,
  surfaced as interim in logs and in the object handed to the persistence seam (FR-016). It
  invents no criteria.
- Tests use a `StubValidator(passed=…, failed_criteria=…, feedback=…)` to drive both branches
  (FR-017). On a failing outcome, `student_service` packages it into
  `FirstAttemptOutcome.ValidationFailed` for the retry seam.

## Persistence and retrieval seam (concrete implementation: US-15)

- New `BriefingStore` protocol in `ports.py`: `has_validated(hash) -> bool`,
  `get_latest_validated(hash) -> ValidatedBriefing | None`, `save_validated(briefing) -> None`.
- Feature-001 ships `InMemoryBriefingStore` (dict of ordered lists) as its test / local double.
  The governed Unity Catalog Volume implementation — path, file format, naming, retention,
  most-recent selection — is **US-15**.
- `student_service` only ever calls `save_validated` with a briefing whose `ValidationOutcome`
  passed (FR-025); a `BriefingStorageError` from the seam becomes an explicit error and the
  request is not reported successful (FR-024); a failed regeneration never calls a remove/replace
  (FR-037).
- Retrieval: `student_service.get_stored_briefing(hash)` → `store.get_latest_validated(hash)`;
  `None` → explicit "none available" (FR-028–FR-030). Exposed via `GET
  /api/students/{hash}/briefing` and MCP `get_student_briefing`.
- Config: no `BRIEFING_VOLUME` setting and no `validate_volume_identifier` in Feature-001 —
  they arrive with the US-15 implementation. `main.build_service` wires `InMemoryBriefingStore`
  unconditionally in Feature-001; US-15 will add the selection.

## Error handling

Reuses the established convention: typed service exceptions; explicit per-interface status
mapping; safe generic messages; `raise ... from exc`; FastAPI request validation still yields
422.

| Condition | Service signal | REST | MCP |
|---|---|---|---|
| Unknown / malformed hash, or no prediction row | `StudentNotFoundError` (existing) | 404 "Student hash not found" | error: not found |
| Known student, `attrition_risk_flag` not set (FR-034) | `StudentNotAtRiskError` (new) | 409 "Student is not flagged at risk" | error: not flagged at risk |
| Delta source unavailable / query failure | generic `Exception` (existing path) | 503 "Databricks data source unavailable" | error: data source unavailable |
| A configured constraint forbids an approved feature reaching the generation seam (FR-008; the concrete constraint source arrives with US-13) | `ConfigurationError` (existing type) | 503 + message naming the constraint for human review | error: human-review required |
| Generation seam not configured (FR-014) | `ConfigurationError` | 503 "Briefing generation is not configured" | error: not configured |
| Attempt 1 generation-seam failure or validation-seam failure | routed to `RetryWorkflow` seam; not surfaced directly | — | — |
| Retry seam concludes without a briefing (FR-021) | `BriefingNotProducedError(category)` (new) | **502** — the downstream briefing-generation workflow (generation, or its validation gate) failed to produce a valid briefing; the `category` (`generation` / `validation`) appears only in the safe detail text, not as a distinct code | error: briefing could not be produced (category) |
| Persistence seam reports a write failure (FR-024) | `BriefingStorageError` (new) | 503 "Validated briefing could not be stored" | error: storage failure |
| Retrieval, no validated briefing (FR-030) | explicit "none available" value (not an exception) | 404 "No validated briefing available" | result: none available |

No deterministic/template briefing is ever returned or persisted as success (FR-020). Logging
is metadata-only via a small `logging.getLogger(__name__)` helper — no prompts, no briefing
text, no secrets (FR-031/FR-032); no new logging framework.

## Proportionate testing (US-08 only — broad testing is US-17/18)

All offline: mock repository, `InMemoryBriefingStore`, `StubGenerationProvider` /
`StubValidator`, no network.

| Spec item | Test |
|---|---|
| US1 happy path; SC-001 | `test_briefing_orchestration.py::test_seam_sequence_returns_validated_briefing` — asserts the context carries all 21 features + the risk result and the seams are called in the FR-033 order |
| US1 scenario 3; FR-005 | `test_briefing_orchestration.py::test_uses_model_flag_not_a_second_threshold` |
| US1 scenario 5; FR-011 | `test_briefing_seams.py::test_context_marks_features_as_non_causal` |
| US1 scenario 6; FR-034; SC-010 | `test_briefing_orchestration.py::test_not_flagged_is_refused_without_seam_calls` |
| US1 scenario 7; FR-035; SC-011 | `test_briefing_orchestration.py::test_existing_briefing_returned_without_generation` |
| US1 scenario 8; FR-036/FR-037 | `test_briefing_orchestration.py::test_regenerate_supersedes_on_success_and_preserves_on_terminal_failure` |
| US2; FR-028–FR-030 | `test_briefing_orchestration.py::test_retrieve_latest_and_none_available`; `test_briefing_store.py` |
| US3 scenarios 1–2; FR-019; SC-009 | `test_briefing_orchestration.py::test_generation_and_validation_failures_pass_outcome_to_retry_seam` |
| US3 scenario 3; FR-020; SC-003 | `test_briefing_orchestration.py::test_no_template_substituted_as_success` |
| US3 scenario 4; FR-021; SC-004 | `test_briefing_orchestration.py::test_retry_terminal_returns_explicit_error_and_stores_nothing` |
| FR-024 | `test_briefing_orchestration.py::test_persistence_failure_surfaces_error_and_keeps_previous` |
| FR-007 | repository test — absent column marked unavailable, request proceeds |
| FR-014 | `test_briefing_seams.py::test_stub_generation_provider_raises_not_configured` |
| FR-016 | `test_briefing_seams.py::test_interim_validator_identifies_itself` |
| FR-017 | covered across `test_briefing_orchestration.py` via `StubValidator` |
| FR-031/FR-032; SC-005 | `test_briefing_orchestration.py::test_logs_contain_no_prompt_briefing_or_secret` |
| FR-038; contracts | `test_api.py`, `test_mcp_tools.py` — new routes/tools, status codes, `regenerate` flag |
| FR-039; SC-012 | `test_briefing_seams.py` — each seam has a defined interface + a Feature-001 placeholder; orchestration passes with placeholders only |
| Config | `test_config.py` — course/teaching-period identifier validation |

`quickstart.md` documents the offline placeholder-seam smoke path.

## Approved planning decisions (2026-09-03)

1. **`POST /api/students/{hash}/briefing` — get-or-create (approved).** When a validated
   briefing already exists for the selected student, the normal briefing request returns that
   existing validated briefing without invoking the generation seam; a fresh briefing is
   produced only through an explicit regeneration request (`?regenerate=true`). Feature-001 owns
   only this backend orchestration/routing behaviour; concrete generation, validation, retry,
   and persistent storage remain owned by US-13/US-14/US-15 (retry: Feature-002). Matches spec
   FR-035/FR-036 — no spec change.
2. **21-feature retrieval — application-side join (approved).** Feature-001 retrieves and
   assembles the selected student's 21 approved feature values from the existing synthetic-data
   Delta tables using the existing identifiers and relationships (`fact` + `dwh_curriculum__course`
   on `course_key_hash` + `dwh_learning_and_teaching__teaching_period` on
   `teaching_period_key_hash`), and combines them with the prediction result from the existing
   prediction Delta table. The ML model and synthetic-data-generation implementations are not
   modified and no additional ML projection table is requested. Recorded as a design decision
   and accepted technical risk in **Technical risks** below.
3. **HTTP status conventions — approved set only.** `404` requested student/resource does not
   exist; `409` a valid request conflicts with application state (including a briefing request
   for a student not flagged at risk); `422` request/input validation, via the existing
   FastAPI/Pydantic behaviour only; `502` an invoked downstream briefing-generation dependency
   (generation, or its validation gate) fails to produce a valid briefing; `503` required
   Databricks/data/backend infrastructure is unavailable (including the generation seam being
   unconfigured until US-13, and the persistence seam being unavailable). No additional status
   codes are introduced. Retry-seam terminal failures return a single `502` with the
   `generation`/`validation` category carried only in the concise, safe detail text — not as a
   separate code. External error responses stay safe and concise; internal exception typing and
   `raise ... from exc` chaining are preserved.

*Forward note (not a Feature-001 decision):* outbound egress to the OpenAI API and the data
owner's acceptance of sending synthetic sensitive demographic attributes to an external API
will need approval when **US-13** supplies the concrete generation seam. Feature-001 transmits
nothing externally.

## Technical risks

**TR-1 — application-side reconstruction of the 21-feature input set (accepted).** Feature-001
reproduces the joins needed to reconstruct the approved 21-feature set rather than consuming a
dedicated ML-generated feature-projection table. If the ML feature set, the source-table
relationships, or the upstream transformation logic changes later, the application-side
retrieval/join logic may also need to change. Accepted because modifying the existing ML
implementation is outside Feature-001 scope. Mitigations:
- the approved 21-feature contract (`research.md` R1) is treated as authoritative and is the
  single place the feature list and join keys are defined;
- all feature-retrieval and join logic is isolated in the data-access layer, behind the
  `StudentRepository.get_model_features` seam — nothing above it knows how the 21 values are
  sourced;
- no ML transformation logic is duplicated beyond what is required to read the existing feature
  values (raw values only; no encoding, imputation, or preprocessing);
- a future canonical feature-projection table can replace the application-side join by
  supplying a different `StudentRepository` implementation, with no change to Feature-001
  orchestration.

## Complexity Tracking

No constitution violations — table intentionally empty.
