# Implementation Plan: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

**Branch**: `002-briefing-retry-and-storage` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-briefing-retry-and-storage/spec.md` (approved and
clarified 2026-09-03). Constitution `v1.1.0`. Feature-001 (`001-advisor-briefing-backend`, merged
at `111aac8`) supplies every seam this feature fills.

## Summary

Feature-002 completes Product Backlog **US-15** by supplying the two concrete implementations
Feature-001 defined as boundaries and shipped as placeholders:

1. **The single-retry workflow** — a concrete `RetryWorkflow` (`SingleRetryWorkflow`) that
   replaces `RetryNotConfigured`. It performs exactly one additional generation attempt after a
   first-attempt validation failure or a retryable generation failure, revalidates the result,
   and returns either a `Produced(ValidatedBriefing(attempt_count=2))` or a
   `TerminalFailure(category)`. It plugs into the existing
   `StudentService._hand_off_to_retry`, which already calls `RetryWorkflow.run` once, persists a
   `Produced` result, and raises `BriefingNotProducedError(category)` on `TerminalFailure`.

2. **The governed validated-briefing store** — a concrete `BriefingStore`
   (`VolumeBriefingStore`) backed by a Databricks Unity Catalog Volume, one JSON document per
   validated briefing, selected as "most recent" by a timestamp-sortable filename. It replaces
   `InMemoryBriefingStore` when `BRIEFING_VOLUME` is configured; the in-memory store stays for
   local/mock/test mode.

**Approach: reuse and extend, do not redesign.** No change to the orchestration call order, the
retry hand-off point, the persistence orchestration, the REST/MCP surface, the shared workflow
types, or the error→status mapping. Two new classes, one additive model factory, one new
setting, and composition-root wiring. No new dependency (`databricks-sdk` is already present),
no new framework, no parallel service.

## Technical Context

**Language/Version**: Python `>=3.11,<3.14` (unchanged).

**Primary Dependencies**: Existing only — FastAPI, Uvicorn, Streamlit, FastMCP, Pydantic v2,
`databricks-sdk` (used here for the Unity Catalog Volume **Files API** via `WorkspaceClient`),
`databricks-sql-connector`. Dev: pytest, pytest-asyncio, ruff. **No new runtime dependency.**

**Storage**:
- *Read (unchanged)*: Databricks Delta via SQL warehouse — prediction table + the 21-feature
  fact/dimension joins (Feature-001).
- *Write (new)*: a governed Unity Catalog **Volume** — one JSON file per validated briefing
  under `${BRIEFING_VOLUME}/<student_hash>/`. Append-only filenames; no update, no delete. The
  in-memory store remains the local/test implementation.

**Testing**: pytest, fully offline — scripted generation/validation test doubles and an
in-memory fake Files client. No workspace, no network. Gate: `uv run ruff check .` and
`uv run pytest` (all existing Feature-001 tests must stay green).

**Target Platform**: Databricks App on serverless-compatible compute; Uvicorn via `app.yaml`.

**Project Type**: Single package, flat modules over one `StudentService`. Package
`student_attrition_risk_app/src/student_attrition_risk/`.

**Performance Goals**: Advisor-interactive, low concurrency. A retried request performs at most
two generation attempts plus at most two validations; no added budget or timeout is introduced
(a slow/failed provider call surfaces through the existing generation-failure path). Volume
reads/writes are a single-file `download`/`upload` plus one directory `list`.

**Constraints**: Deidentified hash only, no PII. Metadata-only logging — no prompts, no briefing
text, no secrets (Feature-001 FR-031/FR-032). ML, synthetic-data, and other team-owned
components are read-only (constitution II, XVI). No new compute infrastructure. Unity Catalog
governance and `WorkspaceClient` secret-management are used as-is; `BRIEFING_VOLUME` is
configuration, never hard-coded.

**Scale/Scope**: ~1M synthetic students in the prediction table; retries are the exceptional
path (small fraction of briefing requests). Implementation modifies ~7 existing files and adds
3 new test modules; ~2 new classes plus one small factory.

## Constitution Check

*Evaluated against `.specify/memory/constitution.md` v1.1.0. Re-checked after Phase 1 —
unchanged: PASS.*

| Principle | Assessment |
|---|---|
| I. Specification-Driven Development | PASS — every plan element traces to an FR / SC / Clarification in the approved spec. |
| II. Strict Scope Containment | PASS — changes are confined to the retry and store implementations and their wiring. Notebooks, `docs/`, ML, synthetic-data code untouched. Legacy `TemplateBriefingProvider` / `DatabricksModelBriefingProvider` untouched and unwired. |
| III. Read Broadly, Write Narrowly | PASS — Feature-001 source and the Physical Solution Design were read for the seam contracts and the retry narrative only. |
| IV. Minimal Necessary Change | PASS — 2 new classes (`SingleRetryWorkflow`, `VolumeBriefingStore`), 1 additive factory (`make_validated_briefing`), 1 new setting (`BRIEFING_VOLUME` + `validate_volume_path`), composition-root wiring. `student_service.py` change is a behaviour-preserving delegation of one private helper. No new dependency, framework, or service. |
| V. Reuse and Extend Existing Architecture | PASS — reuses the `RetryWorkflow` and `BriefingStore` protocols verbatim, `StudentService` orchestration and persistence, `BriefingGenerationContext` as the attempt-2 request carrier, the API/MCP error→status mapping, `WorkspaceClient`, and the `Settings` + `validate_*` pattern. |
| VI. No Unnecessary Complexity | PASS — no retry loop, no queue/event bus, no scheduler; one JSON-per-file store with filename-sorted "latest". |
| VII. Plan-Defined Implementation Structure | PASS — this plan names every file, class, and contract; the spec deferred exactly these choices. |
| VIII. Application Technology Compatibility | PASS — Python; Unity Catalog Volume via the existing `databricks-sdk`; no replacement of Databricks primitives. |
| IX. Separation of Responsibilities and Modularity | PASS — retry orchestration is its own module behind the retry boundary; persistence stays behind the store boundary; `StudentService` keeps persistence orchestration; each new class is independently testable. |
| X. Security and Privacy | PASS — Volume path keyed by deidentified hash; stored JSON is only `ValidatedBriefing` fields (no prompt, no feedback text beyond what is already in the validated briefing, no secrets); UC governance + `WorkspaceClient` auth; `BRIEFING_VOLUME` is config. |
| XI. Input Validation and Explicit Error Handling | PASS — `validate_volume_path` rejects a malformed Volume root; every Volume failure raises `BriefingStorageError`; `ConfigurationError` on the retry attempt propagates unchanged; no silent fallback to a template. |
| XII. Proportionate Testing | PASS — the nine required scenarios plus store-contract parity, offline with doubles. No broad end-to-end suite (US-17/US-18). |
| XIII. Human Review of AI-Generated Development Work | PASS — the five deferred decisions were reviewed and approved by Renny Matis on 2026-09-03; see *Approved planning decisions*. |
| XIV. Documentation and Implementation Traceability | PASS — research / data-model / contracts / quickstart map each FR to the design. |
| XV. Completion Means Specification Satisfaction | PASS — scope limited to FR-001…FR-034; nothing from US-12/US-13/US-14 is pre-built; US-14 criteria are not invented. |
| XVI. Preserve Team Contributions | PASS — only Feature-002-owned behaviour is added; other contributors' files are untouched or changed only where an actual dependency requires it (`main.py`, `config.py`, `models.py` additive, one `student_service.py` delegation). |
| XVII. Human-Controlled Version Control | PASS — no Git/GitHub operations performed during planning or implementation planning. |

**Gate result: PASS. Complexity Tracking empty.**

## Project Structure

### Documentation (this feature)

```text
specs/002-briefing-retry-and-storage/
├── plan.md                     # This file (/speckit-plan output)
├── research.md                 # Phase 0 — the deferred planning decisions, resolved
├── data-model.md               # Phase 1 — reused types, the new classes, the stored-file model, config
├── quickstart.md               # Phase 1 — run & validate the retry + governed store offline
├── contracts/
│   ├── retry-workflow.md        # Internal contract: SingleRetryWorkflow.run behaviour + outcome table
│   └── volume-briefing-store.md # Internal contract: BriefingStore over a Unity Catalog Volume
├── spec.md
├── checklists/requirements.md
└── tasks.md                    # Created later by /speckit-tasks
```

### Source Code (repository root)

All work is inside the existing package. Flat modules; no new sub-packages.

```text
student_attrition_risk_app/
├── README.md                        # MODIFY — document the single-retry workflow, the governed store, and BRIEFING_VOLUME
├── .env.example                     # MODIFY — add BRIEFING_VOLUME= (blank → in-memory store)
├── app.yaml                         # MODIFY — add BRIEFING_VOLUME env key with a BLANK value; the real /Volumes/... path is set at deploy time once the governed Volume is confirmed (approved decision 1)
├── src/student_attrition_risk/
│   ├── retry_workflow.py            # MODIFY — add SingleRetryWorkflow (+ a private retry-context builder); keep RetryNotConfigured as the passthrough/test double
│   ├── briefing_store.py            # MODIFY — add VolumeBriefingStore (Unity Catalog Volume Files API); keep InMemoryBriefingStore
│   ├── config.py                    # MODIFY — add `briefing_volume` setting + `validate_volume_path`
│   ├── models.py                    # MODIFY (additive only) — add `make_validated_briefing(...)` factory used by both the service and the retry workflow
│   ├── student_service.py           # MODIFY (behaviour-preserving) — `_build_validated` delegates to `make_validated_briefing`; no orchestration change
│   ├── main.py                      # MODIFY — `build_service` wires SingleRetryWorkflow always, and selects VolumeBriefingStore vs InMemoryBriefingStore by `settings.briefing_volume`
│   ├── ports.py                     # READ-ONLY — `RetryWorkflow` and `BriefingStore` protocols already match
│   ├── api.py                       # READ-ONLY — BriefingNotProducedError→502, BriefingStorageError→503, ConfigurationError→503 already mapped
│   ├── mcp_server.py                # READ-ONLY — same error mapping already present
│   ├── briefing_provider.py         # READ-ONLY — legacy providers + StubGenerationProvider unchanged
│   ├── briefing_instructions.py     # READ-ONLY — instructions seam is US-12
│   ├── briefing_validation.py       # READ-ONLY — validation seam is US-14
│   ├── student_repository.py        # READ-ONLY
│   ├── databricks_client.py         # READ-ONLY — SQL only; the Volume store uses WorkspaceClient directly
│   ├── streamlit_host.py            # READ-ONLY
│   └── ui.py                        # READ-ONLY — no advisor-visible retry indicator (FR-032)
└── tests/
    ├── test_retry_workflow.py       # NEW — SingleRetryWorkflow unit behaviour (see Test plan)
    ├── test_volume_briefing_store.py# NEW — VolumeBriefingStore against an in-memory fake Files client + store-contract parity
    ├── test_briefing_retry_integration.py # NEW — end-to-end via StudentService with scripted doubles: attempt_count=2, no third attempt, terminal categories, previous briefing preserved, nothing stored on failure
    ├── test_config.py               # MODIFY — BRIEFING_VOLUME / validate_volume_path cases
    ├── test_briefing_orchestration.py # READ-ONLY — must still pass unchanged (uses its own retry double)
    ├── test_briefing_store.py       # READ-ONLY — InMemoryBriefingStore contract still passes
    └── test_template_briefing.py    # READ-ONLY — legacy provider test still passes
```

**No changes** to `pyproject.toml` / `uv.lock` (no new dependency).

### Structure Decision

Extend the existing single package. Add two flat classes — one per Feature-002 concrete seam
implementation — beside their Feature-001 placeholders in the files that already own that seam
(`retry_workflow.py`, `briefing_store.py`), mirroring the Feature-001 pattern of "placeholder
and concrete implementation share a module behind one protocol". Everything else is additive
(`config.py`, `models.py`) or wiring (`main.py`), plus one behaviour-preserving delegation in
`student_service.py`. This is the smallest structure that satisfies the spec while keeping
US-13 (generation) and US-14 (validation) replaceable through the untouched boundaries.

## Design

### 1. `SingleRetryWorkflow` — the concrete retry (`retry_workflow.py`)

Constructed in `main.build_service` with the **same** `GenerationProvider` and
`BriefingValidator` instances that `StudentService` uses, so whatever US-13 / US-14 wire in is
what the retry attempt uses:

```
SingleRetryWorkflow(generation_provider: GenerationProvider, validator: BriefingValidator)
    .run(context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome) -> BriefingOutcome
```

`run` performs **exactly one** `generation_provider.generate(...)` call and **at most one**
`validator.validate(...)` call — no loop, no recursion:

| First-attempt outcome | Attempt-2 request | Attempt-2 result | `run` returns |
|---|---|---|---|
| `ValidationFailed(outcome)` | original context, `composed_prompt` augmented with the revision-feedback block **iff** `outcome.failed_criteria` or `outcome.feedback` is non-empty (FR-006–FR-008) | draft, revalidated, `passed` | `Produced(ValidatedBriefing(attempt_count=2))` (FR-014) |
| `ValidationFailed(outcome)` | as above | draft, revalidated, not `passed` | `TerminalFailure(category="validation")` (FR-013) |
| `ValidationFailed(outcome)` | as above | `generate` raises non-`ConfigurationError` | `TerminalFailure(category="generation")` (FR-012) |
| `GenerationFailed(_)` | original context unchanged (FR-010) | draft, validated, `passed` | `Produced(ValidatedBriefing(attempt_count=2))` |
| `GenerationFailed(_)` | as above | draft, validated, not `passed` | `TerminalFailure(category="validation")` |
| `GenerationFailed(_)` | as above | `generate` raises non-`ConfigurationError` | `TerminalFailure(category="generation")` |
| either | any | `generate` raises `ConfigurationError` | **re-raises `ConfigurationError`** — never a `TerminalFailure`, never templated (spec Edge Cases; existing API/MCP handlers map it to 503) |

`run` never raises anything other than a propagated `ConfigurationError`; every other path
returns a `BriefingOutcome` (FR-005).

**Retry-request construction** (`retry_workflow.py`, private helper
`_retry_context(context, first_outcome) -> BriefingGenerationContext`):
- Returns a `context.model_copy(update={"composed_prompt": ...})` — same
  `student_deidentified_hash`, `prediction`, `features`, `instructions_id` (FR-006; factual
  content and provenance unchanged).
- For `ValidationFailed` with non-empty `failed_criteria` / `feedback`: `composed_prompt`
  becomes `context.composed_prompt` + a fixed, delimited block listing the failed criteria and
  the feedback verbatim. The wrapper text is a minimal Feature-002 constant that only **relays**
  what validation returned — it introduces **no substantive new briefing instructions**, does
  **not** duplicate the US-12 prompt design, and carries **no** US-14 criteria of its own. It
  is a single replaceable constant so that integrating the final US-12 instructions (or a US-13
  structured-feedback input) needs no change to `run` (approved decision 3).
- For `GenerationFailed`, or `ValidationFailed` with nothing to relay: `composed_prompt` is
  copied unchanged; nothing is fabricated (FR-008, FR-010).

`RetryNotConfigured` stays in the module as the "retry disabled" passthrough and as a test
double; Feature-001 orchestration tests that inject it keep passing.

### 2. `make_validated_briefing(...)` — shared factory (`models.py`, additive)

```
make_validated_briefing(*, student_hash: str, prediction: StudentPrediction, text: str,
                        validator_id: str, attempt_count: int,
                        generated_at: datetime | None = None) -> ValidatedBriefing
```

Builds the `ValidatedBriefing` from a `StudentPrediction` (risk %, at-risk flag, threshold,
`mlflow_run_id`, `scored_at`), `source="generated"`, `validated=True`, `generated_at` defaulting
to `datetime.now(UTC)`. `SingleRetryWorkflow` calls it with `attempt_count=2` using
`context.prediction`; `StudentService._build_validated` is refactored to call it with
`attempt_count=1`. One constructor, no divergence. Purely additive to `models.py`; the
`student_service.py` edit is covered by the existing `test_student_service.py` /
`test_briefing_orchestration.py`.

### 3. `StudentService` — unchanged orchestration

`_hand_off_to_retry` already: calls `retry_workflow.run(context, first_outcome)` once; on
`Produced` calls `self._persist(...)` and returns `result.briefing`; on `TerminalFailure` logs
`terminal_<category>` and raises `BriefingNotProducedError(category)`. Feature-002 changes
**none** of this. `attempt_count` flows out through the existing `_log_outcome(... attempt_count
= result.briefing.attempt_count ...)` and the existing `ValidatedBriefing` response model
(FR-019, FR-032). A `ConfigurationError` raised by `run` propagates through `_hand_off_to_retry`
(it is not inside the first-attempt `try/except ConfigurationError`) to the API/MCP layer's
existing `ConfigurationError → 503` handler.

Only edit: `_build_validated` becomes a one-line delegation to `make_validated_briefing`.

### 4. `VolumeBriefingStore` — the governed store (`briefing_store.py`)

```
VolumeBriefingStore(settings: Settings, files=None)   # files defaults to WorkspaceClient().files
    .has_validated(student_hash) -> bool
    .get_latest_validated(student_hash) -> ValidatedBriefing | None
    .save_validated(briefing: ValidatedBriefing) -> None      # raises BriefingStorageError on any failure
```

- **Layout**: `${BRIEFING_VOLUME}/<student_hash>/<generated_at:%Y%m%dT%H%M%S%fZ>-attempt<n>-<6-char token>.json`.
  `BRIEFING_VOLUME` is a `/Volumes/<catalog>/<schema>/<volume>[/<prefix>]` root.
- **Format**: the file body is `briefing.model_dump_json()` — exactly the `ValidatedBriefing`
  fields. No prompt, no separate feedback blob, no secret (FR-026, constitution X).
- **`save_validated`**: `files.upload(path, body, overwrite=False)`. New filename every call →
  never overwrites or replaces an earlier file (FR-023). Any SDK exception (auth, missing
  Volume, quota, network) → `raise BriefingStorageError(...) from exc`; nothing partial is left
  because a single `upload` is atomic per file (FR-024).
- **`get_latest_validated`**: `files.list_directory_contents(dir)`; if the directory is missing
  or empty → `None` (FR-022 "none available"); else pick the lexicographically greatest
  filename (timestamp prefix ⇒ chronological), `files.download` it, parse JSON →
  `ValidatedBriefing`, return it with `source` left as stored (the service applies
  `source="stored"` on the retrieval path, as it does today). A read failure other than
  not-found → `BriefingStorageError` (surfaces as the existing 503 "store unavailable", not
  "none available"; spec Edge Cases).
- **`has_validated`**: `True` iff the student directory lists ≥1 file; not-found → `False`.
- **Retention**: append-only — Feature-002 performs no pruning and no deletion of superseded
  files (approved decision 4; Clarification 2026-09-03). Only the latest is ever read.
- **Contract parity**: the same behavioural scenarios as `test_briefing_store.py` pass against
  `VolumeBriefingStore` with the fake Files client (SC-010).

`InMemoryBriefingStore` is unchanged and remains the local/mock/test store.

### 5. Configuration (`config.py`)

| Setting | Env var | Required? | Default / fallback |
|---|---|---|---|
| `briefing_volume` | `BRIEFING_VOLUME` | no | unset/blank → `None` → `build_service` uses `InMemoryBriefingStore` |

`validate_volume_path(path)` (mirrors `validate_table_identifier`): must start `/Volumes/`,
have at least catalog/schema/volume segments, each segment matching a safe-name pattern; raises
`ConfigurationError` otherwise. Called from `Settings.from_env` only when `BRIEFING_VOLUME` is
non-blank. No OpenAI settings (US-13).

### 6. Composition root (`main.py`)

```
retry_workflow = SingleRetryWorkflow(generation_provider=generation_provider, validator=validator)
store = VolumeBriefingStore(settings) if settings.briefing_volume else InMemoryBriefingStore()
```

`SingleRetryWorkflow` is wired **unconditionally**, with no retry feature flag (approved
decision 2) — until US-13, first-attempt generation raises `ConfigurationError`, which
`StudentService` surfaces before the hand-off, so `run` is simply never reached in production;
wiring it now needs no follow-up when US-13 lands.

### 7. Sync/async

Synchronous throughout, matching Feature-001 and the `WorkspaceClient` Files API. FastAPI routes
stay `def`.

## Test plan (proportionate — constitution XII)

Offline, no workspace. Doubles: `ScriptedGenerationProvider` (list of draft-or-exception,
one consumed per call, asserts it is not over-called), `ScriptedValidator` (list of
`ValidationOutcome`), `FakeFilesClient` (in-memory dict emulating
`upload` / `download` / `list_directory_contents` incl. not-found).

`tests/test_retry_workflow.py`:
- validation failure → retry generation ok, revalidation passes ⇒ `Produced`, `attempt_count == 2`.
- generation failure → retry generation ok, validation passes ⇒ `Produced`, `attempt_count == 2`.
- attempt-2 generation raises ⇒ `TerminalFailure(category="generation")`.
- attempt-2 draft fails revalidation ⇒ `TerminalFailure(category="validation")`.
- `generate` is called exactly once inside `run`; `validate` at most once — no third attempt.
- validation failure with `failed_criteria` + `feedback` ⇒ the attempt-2 context's
  `composed_prompt` contains both; `student_deidentified_hash` / `prediction` / `features` /
  `instructions_id` unchanged.
- validation failure with empty `failed_criteria` and `feedback is None` (interim validator) ⇒
  attempt-2 `composed_prompt` equals the original; nothing fabricated.
- generation failure ⇒ attempt-2 `composed_prompt` equals the original; no feedback block.
- attempt-2 `generate` raises `ConfigurationError` ⇒ `run` re-raises it (no `TerminalFailure`).

`tests/test_briefing_retry_integration.py` (through `StudentService`, real
`SingleRetryWorkflow`, `InMemoryBriefingStore`):
- validation-fail-then-pass ⇒ `request_briefing` returns `attempt_count == 2`; store holds it.
- two failures ⇒ `BriefingNotProducedError` with the correct `category`; store holds nothing new.
- regeneration that fails on both attempts for a student with a prior briefing ⇒ prior briefing
  still returned by `get_stored_briefing` (FR-018).
- no deterministic/template briefing is ever returned or stored on failure (FR-016/FR-017).
- metadata-only logging: `attempt_count=2`, outcome category present; no prompt/briefing text.

`tests/test_volume_briefing_store.py` (with `FakeFilesClient`):
- save then `get_latest_validated` returns an equal `ValidatedBriefing`; `has_validated` true.
- `get_latest_validated` for an unknown hash ⇒ `None`; `has_validated` false.
- two saves ⇒ the most-recent (later filename) is returned; the first file still exists
  (not required to be retrievable, but not deleted).
- `upload` raising ⇒ `BriefingStorageError`; a prior latest file is untouched.
- `download` / `list` raising a non-not-found error ⇒ `BriefingStorageError` (distinct from
  `None`).
- store-contract parity: the `test_briefing_store.py` scenarios pass against `VolumeBriefingStore`.
- `save_validated` writes only `ValidatedBriefing` JSON — no prompt text key, no secret.

`tests/test_config.py` (extend): valid `/Volumes/a/b/c` accepted; missing prefix, too few
segments, unsafe characters ⇒ `ConfigurationError`; blank ⇒ `briefing_volume is None`.

Existing suites (`test_briefing_orchestration.py`, `test_briefing_store.py`, `test_api.py`,
`test_mcp_tools.py`, `test_student_service.py`, `test_template_briefing.py`) must pass unchanged.

## Approved planning decisions (Renny Matis, 2026-09-03)

All five deferred decisions are approved as follows and are now binding on implementation:

1. **`BRIEFING_VOLUME` is a configurable Unity Catalog Volume path.** The plan adds the
   `BRIEFING_VOLUME` env key to `.env.example` and `app.yaml` with a **blank** value. No
   `/Volumes/...` deployment value is hard-coded or invented; the real value is supplied at
   deploy time once the target governed Volume is confirmed. `config.validate_volume_path`
   rejects a malformed value; a blank value selects `InMemoryBriefingStore`.
2. **`SingleRetryWorkflow` is wired unconditionally** in the normal application composition
   (`main.build_service`) once Feature-002 is implemented. No retry-enabled feature flag is
   added. It is inert until US-13 (first-attempt `ConfigurationError` is surfaced before the
   retry hand-off).
3. **The retry-feedback wrapper is a minimal Feature-002 constant** that incorporates only the
   failed acceptance criteria and Validation Feedback actually returned by validation. It
   introduces no substantive new briefing instructions, does not duplicate the US-12 prompt
   design, carries no US-14 criteria of its own, and is a single replaceable constant so it can
   be superseded cleanly when the final US-12 instructions are integrated.
4. **Validated-briefing storage is append-only.** Feature-002 performs no automatic pruning and
   no deletion of superseded valid briefings; every `save_validated` writes a new file and
   nothing is ever overwritten or removed. A retention policy, if ever needed, is a later story.
5. **One JSON file per validated briefing** in the governed Volume — the file body is
   `ValidatedBriefing.model_dump_json()`, keeping briefing content and required metadata
   structured and faithfully round-trippable on retrieval.

## Phase 0 / Phase 1 outputs

- `research.md` — the deferred planning decisions (retry placement, retry-request construction,
  attempt-2 briefing construction, `ConfigurationError` propagation, Volume access mechanism,
  store selection & config, sync/async, dependencies, test strategy), each with rationale and
  alternatives.
- `data-model.md` — reused Feature-001 types (unchanged), the two new classes, the shared
  factory, the stored-file model, and the new configuration.
- `contracts/retry-workflow.md`, `contracts/volume-briefing-store.md` — the internal contracts
  (no REST/MCP contract change).
- `quickstart.md` — offline validation of the retry and the governed store.

## Complexity Tracking

*No constitution violations. Table intentionally empty.*
