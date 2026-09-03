# Phase 0 Research: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

Resolves the implementation-level choices the approved spec deliberately deferred to
`/speckit-plan`. No `NEEDS CLARIFICATION` items remain: the spec is approved and clarified
(Session 2026-09-03), the Feature-001 seams are merged, and the Physical Solution Design text
was read for the retry narrative.

Format per decision: **Decision / Rationale / Alternatives considered**.

## R1. Where the single-retry workflow lives and how it is composed

**Decision**: Add `SingleRetryWorkflow` to `retry_workflow.py`, beside the retained
`RetryNotConfigured`. It implements the existing `ports.RetryWorkflow` protocol unchanged:
`run(context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome) -> BriefingOutcome`.
It is constructed in `main.build_service` with the **same** `GenerationProvider` and
`BriefingValidator` instances passed to `StudentService`, so US-13 / US-14 implementations flow
into the retry automatically.

**Rationale**: Feature-001 designed `RetryWorkflow` precisely as the Feature-001↔Feature-002
boundary (`ports.py`, `contracts/internal-seams.md`, `research.md` R5). `StudentService._hand_off_to_retry`
already calls `run` once, persists a `Produced` result, and raises `BriefingNotProducedError`
on `TerminalFailure` — so the entire feature drops in behind the protocol with zero
orchestration change (constitution IV, V). Sharing the module with the placeholder mirrors the
Feature-001 pattern (`InterimValidator` beside the future US-14 validator, etc.).

**Alternatives considered**:
- *New `retry/` sub-package or a `retry_service.py`*: rejected — module sprawl for two small
  classes; violates VI and the Feature-001 flat-module convention.
- *Put retry logic back inside `StudentService`*: rejected — Feature-002 would then edit
  Feature-001 orchestration code, breaking the boundary the merged feature established.
- *Give `SingleRetryWorkflow` its own generation/validation instances from settings*: rejected —
  it must use whatever the service uses so US-13/US-14 stay swap-in (FR-034); double-wiring
  invites drift.

## R2. How the attempt-2 request is constructed

**Decision**: A private helper `_retry_context(context, first_outcome) -> BriefingGenerationContext`
returns `context.model_copy(update={"composed_prompt": <possibly augmented>})`. For a
`ValidationFailed` whose `outcome.failed_criteria` or `outcome.feedback` is non-empty, the
original `composed_prompt` is suffixed with a fixed, delimited **revision-feedback block** that
lists the failed criteria and quotes the feedback. For a `GenerationFailed`, or a
`ValidationFailed` with nothing to relay, `composed_prompt` is copied unchanged.
`student_deidentified_hash`, `prediction`, `features`, and `instructions_id` are always copied
verbatim.

**Rationale**: `BriefingGenerationContext.composed_prompt` is already the single string the
generation seam consumes (`ports.GenerationProvider.generate`), so expressing the retry request
as an augmented context needs no new type and no change to the generation boundary. The
Physical Solution Design describes the retry input as *"original instructions and validation
feedback combined into a regenerated retry prompt"* and *"a revised prompt containing the
Validation Feedback and failed acceptance criteria"* — i.e. context + criteria + feedback, not a
revision of the rejected draft. Keeping `instructions_id` unchanged preserves US-12 ownership of
instruction provenance (spec FR-006). Only relaying validator-provided values honours FR-007 /
FR-008 (nothing fabricated).

**Alternatives considered**:
- *Add a `compose_retry(context, outcome)` method to the `BriefingInstructions` seam*: rejected
  — widens a seam owned by US-12; Feature-002 must not expand another story's interface.
- *Add structured `retry_feedback` fields to `BriefingGenerationContext`*: rejected for now —
  changes a Feature-001 shared model that US-13 has not asked for; the `composed_prompt` string
  is the established contract. Recorded as a future option if US-13 wants structured input.
- *Feed the rejected draft text into attempt 2 for line-edit-style revision*: rejected — not
  described by the Solution Design, and the spec frames attempt 2 as regeneration; would also
  require carrying draft text further than the request that produced it (Feature-001 FR-026).
- *Fixed wrapper wording deferred to US-12*: rejected — the retry cannot run without *some*
  wrapper. Approved (planning decision 3, 2026-09-03) as a minimal Feature-002 constant that
  only relays the validator's `failed_criteria` / `feedback`: it adds no substantive briefing
  instructions, does not duplicate the US-12 prompt design, and is a single replaceable constant
  so the final US-12 instructions supersede it without changing `run`.

## R3. Building the attempt-2 `ValidatedBriefing` and `attempt_count`

**Decision**: Add an additive factory `make_validated_briefing(*, student_hash, prediction,
text, validator_id, attempt_count, generated_at=None)` to `models.py`.
`SingleRetryWorkflow` calls it with `attempt_count=2`, `prediction=context.prediction`,
`validator_id` from the attempt-2 `ValidationOutcome`, `text` from the attempt-2 draft.
`StudentService._build_validated` is refactored to call the same factory with
`attempt_count=1` (behaviour identical; guarded by existing tests).

**Rationale**: `BriefingGenerationContext` already carries the full `StudentPrediction`, so the
retry workflow has every field the validated-briefing model needs (risk %, at-risk flag,
threshold, `mlflow_run_id`, `scored_at`) without a second repository read or a `StudentService`
callback. One factory prevents two divergent constructors of the same Pydantic model
(constitution V, VI). `attempt_count` then flows out unchanged through the existing
`_hand_off_to_retry` logging and the existing `ValidatedBriefing` REST/MCP response — no new
field, no advisor-visible label (spec FR-032).

**Alternatives considered**:
- *`SingleRetryWorkflow` calls back into `StudentService._build_validated`*: rejected — inverts
  the dependency (service owns the retry seam, not vice versa) and risks an import cycle.
- *Duplicate the ~10-line constructor in the retry workflow*: rejected — divergence risk; the
  factory is the minimal shared change.
- *Have the retry workflow return only `text` and let the service build the briefing*: rejected
  — the `RetryWorkflow` contract returns `BriefingOutcome`/`Produced(ValidatedBriefing)`
  (`models.py`, `contracts/internal-seams.md`); changing it would edit the merged boundary.

## R4. `ConfigurationError` on the retry attempt

**Decision**: If `generation_provider.generate` raises `ConfigurationError` during attempt 2,
`SingleRetryWorkflow.run` lets it propagate unchanged — it is never converted to
`TerminalFailure` and never templated. It travels through `StudentService._hand_off_to_retry`
(which is outside the first-attempt `try/except ConfigurationError`) to the existing
`ConfigurationError → 503` handlers in `api.py` and `mcp_server.py`.

**Rationale**: The confirmed decision and spec keep `ConfigurationError` permanently
non-retryable and *surfaced as-is*; Feature-001 already routes only non-`ConfigurationError`
first-attempt failures into the retry (`student_service.request_briefing`). Treating a
config error surfacing mid-retry as a terminal *generation* failure would misreport an
environment/config problem as a model failure and change the status code from 503 to 502.

**Alternatives considered**:
- *Map it to `TerminalFailure(category="generation")`*: rejected — wrong status semantics
  (R9 of Feature-001: 503 is "backend/infra/config unavailable", 502 is "dependency failed to
  produce a valid briefing").
- *Catch and re-wrap in a Feature-002 error type*: rejected — unnecessary new exception; the
  existing handlers already do the right thing.

## R5. Unity Catalog Volume access mechanism for `VolumeBriefingStore`

**Decision**: Use the Databricks SDK **Files API for Volumes** via
`databricks.sdk.WorkspaceClient().files` — `upload(path, contents, overwrite=False)`,
`download(path)`, `list_directory_contents(path)`. `VolumeBriefingStore(settings, files=None)`
defaults `files` to `WorkspaceClient().files`; tests inject an in-memory fake. One JSON file per
validated briefing; `briefing.model_dump_json()` is the body.

**Rationale**: `databricks-sdk>=0.50` is already a project dependency (`pyproject.toml`) and is
already used for unified auth in `databricks_client.py`, so there is **no new dependency** and
existing Unity Catalog governance / secret-management applies unchanged (constitution VIII, X).
A file-per-briefing model matches the Solution Design (*"Unity Catalog Volume stores validated
briefing documents so they can be reopened"*) and the seam contract (validated-only,
most-recent, none-available). A single `upload` per briefing is naturally append-only and
atomic per file (FR-023, FR-024).

**Alternatives considered**:
- *`databricks-sql-connector` + a Delta table of briefings*: rejected — US-15 and the Solution
  Design name a **Volume**; a table is a different storage architecture and a parallel design
  (constitution V, VI). It also complicates "reopen the document".
- *Mount path / local `dbutils.fs`*: rejected — not available outside a notebook/job context;
  the app runs under Uvicorn.
- *`WorkspaceClient().dbfs`*: rejected — DBFS is not the governed UC Volume surface.
- *One JSON file per student, rewritten on each save (holding a list/history)*: rejected —
  rewrite = replace, which risks losing the current briefing on a failed write and conflicts
  with the append-only intent; per-briefing files keep "never lose the current one" trivially
  true.

## R6. Store selection, configuration, and filename scheme

**Decision**: Add one setting `briefing_volume` (`BRIEFING_VOLUME` env) plus
`validate_volume_path` in `config.py` (mirrors `validate_table_identifier`: must start
`/Volumes/`, have catalog/schema/volume segments, safe names; `ConfigurationError` otherwise;
only validated when non-blank). `main.build_service` selects
`VolumeBriefingStore(settings)` when `settings.briefing_volume` is set, else
`InMemoryBriefingStore()`. No `/Volumes/...` value is hard-coded — `.env.example` and `app.yaml`
carry the key blank and the deployment value is set once the governed Volume is confirmed
(planning decision 1, 2026-09-03). Files are named
`<generated_at:%Y%m%dT%H%M%S%fZ>-attempt<n>-<6-char token>.json` under
`${BRIEFING_VOLUME}/<student_hash>/`; "most recent" = lexicographically greatest filename.
Storage is append-only: Feature-002 performs no pruning and no deletion of superseded briefings
(planning decision 4; a retention policy is a later story).

**Rationale**: Feature-001's `data-model.md` already earmarked `BRIEFING_VOLUME` and
"Volume-identifier validation" for US-15, and the `USE_MOCK_DATA` / optional-table pattern is
the established way this app degrades to a local implementation. A microsecond-precision UTC
timestamp prefix plus a short random token makes filenames sort chronologically and avoids
same-instant collisions, so "latest" needs only a directory listing and a string max — no
metadata index. The clarified spec requires only that the most-recent briefing be retrievable.

**Alternatives considered**:
- *Reuse `USE_MOCK_DATA` to pick the store*: rejected — a deployment could want mock Delta reads
  but a real Volume, or vice versa; an explicit `BRIEFING_VOLUME` is clearer and matches how
  `DATABRICKS_*` tables are configured.
- *Sequence numbers / a manifest file for ordering*: rejected — a manifest is extra state that
  can desync; timestamped filenames are self-ordering.
- *`ulid`/`uuid7` filenames*: equivalent, but adds a dependency or hand-rolled code; the
  timestamp+token string is sufficient and dependency-free.

## R7. Synchronous vs asynchronous

**Decision**: Synchronous. `SingleRetryWorkflow.run`, `VolumeBriefingStore`, and the
`WorkspaceClient` Files API are all synchronous; FastAPI routes stay `def`.

**Rationale**: Feature-001 is entirely synchronous (`StudentService`, repository, seams). The
workload is advisor-interactive and low-concurrency (spec Assumptions). Introducing async here
would fork the call style for no throughput need (constitution VI).

**Alternatives considered**:
- *Async Volume I/O*: rejected — the SDK Files client is sync; wrapping in a thread pool is
  complexity without a measured need.

## R8. Legacy providers and dependencies

**Decision**: `TemplateBriefingProvider` and `DatabricksModelBriefingProvider` in
`briefing_provider.py` are left untouched and unwired. `StubGenerationProvider` is unchanged. No
change to `pyproject.toml` / `uv.lock` / the `app.yaml` command. `app.yaml` gains only a
`BRIEFING_VOLUME` env entry with a **blank** value (the deployment value is set later — planning
decision 1).

**Rationale**: Spec FR-031 and constitution II/XVI. `databricks-sdk` already covers the Volume
need (R5), so no dependency is added.

**Alternatives considered**:
- *Delete the unwired legacy providers while here*: rejected — unrelated cleanup, out of scope
  (spec, constitution IV).

## R9. Test strategy and doubles

**Decision**: Offline pytest only. New doubles: `ScriptedGenerationProvider` (ordered list of
draft-or-exception, one per `generate`, over-call is an assertion failure), `ScriptedValidator`
(ordered `ValidationOutcome`s), `FakeFilesClient` (in-memory dict emulating
`upload`/`download`/`list_directory_contents`, including not-found). New test files:
`test_retry_workflow.py`, `test_briefing_retry_integration.py`, `test_volume_briefing_store.py`;
extend `test_config.py`. All existing Feature-001 test files must pass unchanged. Gate:
`uv run ruff check .` and `uv run pytest`.

**Rationale**: Constitution XII and the Feature-001 convention (`research.md` R7): the full
behaviour must be verifiable with no network, no workspace, and no concrete US-13/US-14
implementation (spec FR-034, SC-011). Scripted doubles make "exactly one retry / no third
attempt" and the terminal-category matrix directly assertable.

**Alternatives considered**:
- *Integration test against a real Volume*: rejected for the merge gate — needs a workspace;
  belongs to US-16 end-to-end testing.
- *Extend `test_briefing_orchestration.py` instead of new files*: rejected — that file is the
  Feature-001 orchestration suite; a separate file per Feature-002 concern matches the existing
  layout and keeps blast radius clear.
