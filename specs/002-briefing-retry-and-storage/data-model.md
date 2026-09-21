# Phase 1 Data Model: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

Feature-002 adds **no new shared domain type and no new persisted field**. It consumes the
Feature-001 workflow types unchanged, adds two concrete seam implementations, one additive model
factory, one configuration setting, and a stored-file layout for the Unity Catalog Volume.

## Reused Feature-001 types (unchanged — imported, not redefined)

### `BriefingGenerationContext`
The assembled generation input (`models.py`). Feature-002 reuses it as the **attempt-2 request
carrier**: `SingleRetryWorkflow` produces a `context.model_copy(update={"composed_prompt": …})`
with `student_deidentified_hash`, `prediction`, `features`, and `instructions_id` copied
verbatim (spec FR-006). No field added.

### `ValidationOutcome`
`{ passed: bool, failed_criteria: list[str], feedback: str | None, validator_id: str }`
(`models.py`). Feature-002 **reads** `failed_criteria` and `feedback` from a first-attempt
`ValidationFailed` and includes them in the retry request only when non-empty (FR-007/FR-008).
Under the interim validator both are empty/`None`, so the retry request equals the original
context.

### `FirstAttemptOutcome` = `GenerationFailed | ValidationFailed`
The retry-seam input (`models.py`). Consumed as-is; `GenerationFailed.category == "generation"`,
`ValidationFailed.category == "validation"`, `ValidationFailed.outcome` is the `ValidationOutcome`.

### `BriefingOutcome` = `Produced | TerminalFailure`
The retry-seam output (`models.py`). Feature-002 now exercises both:
- `Produced(briefing: ValidatedBriefing)` — attempt 2 passed validation; `briefing.attempt_count == 2`.
- `TerminalFailure(category: "generation" | "validation")` — attempt 2 failed; `category` is the
  **last** failure cause (FR-012/FR-013), independent of what the first attempt failed on.

### `ValidatedBriefing`
The only briefing form returned or stored (`models.py`). Feature-002 sets `attempt_count = 2`
for a retry success and `source = "generated"`; all other fields are derived from
`context.prediction` exactly as a first-attempt success. No field added. The retrieval path
still stamps `source = "stored"` (existing `StudentService` behaviour).

## New implementation types (not shared domain types)

### `SingleRetryWorkflow` (`retry_workflow.py`) — concrete `ports.RetryWorkflow`

| Member | Shape | Notes |
|---|---|---|
| `__init__(generation_provider, validator)` | `GenerationProvider`, `BriefingValidator` | the same instances `StudentService` holds (wired in `main.build_service`) |
| `run(context, first_outcome) -> BriefingOutcome` | protocol method | exactly one `generation_provider.generate`; at most one `validator.validate`; never raises except a propagated `ConfigurationError` |
| `_retry_context(context, first_outcome) -> BriefingGenerationContext` | private | copy of `context`; `composed_prompt` augmented with the revision-feedback block only for `ValidationFailed` carrying non-empty `failed_criteria`/`feedback` |

Outcome matrix: see `contracts/retry-workflow.md`.

### `VolumeBriefingStore` (`briefing_store.py`) — concrete `ports.BriefingStore`

| Member | Shape | Notes |
|---|---|---|
| `__init__(settings, files=None)` | `Settings`, optional Files client | `files` defaults to `WorkspaceClient().files`; tests inject a fake |
| `has_validated(student_hash) -> bool` | protocol method | `True` iff the student directory lists ≥1 file; not-found ⇒ `False` |
| `get_latest_validated(student_hash) -> ValidatedBriefing \| None` | protocol method | greatest filename ⇒ `download` ⇒ parse JSON; empty/missing dir ⇒ `None`; non-not-found read error ⇒ `BriefingStorageError` |
| `save_validated(briefing) -> None` | protocol method | `files.upload(path, briefing.model_dump_json(), overwrite=False)`; any failure ⇒ `BriefingStorageError` |

Retains `InMemoryBriefingStore` unchanged as the local/mock/test store.

### `make_validated_briefing(...)` (`models.py`, additive)

```
make_validated_briefing(*, student_hash: str, prediction: StudentPrediction, text: str,
                        validator_id: str, attempt_count: int,
                        generated_at: datetime | None = None) -> ValidatedBriefing
```
Single constructor for `ValidatedBriefing` from a `StudentPrediction`. Used by
`SingleRetryWorkflow` (`attempt_count=2`) and `StudentService._build_validated`
(`attempt_count=1`). `source="generated"`, `validated=True`, `generated_at` defaults to
`datetime.now(UTC)`.

## Stored-file model (Unity Catalog Volume)

| Aspect | Value |
|---|---|
| Root | `${BRIEFING_VOLUME}` — a `/Volumes/<catalog>/<schema>/<volume>[/<prefix>]` path |
| Per-student directory | `${BRIEFING_VOLUME}/<student_deidentified_hash>/` |
| File name | `<generated_at:%Y%m%dT%H%M%S%fZ>-attempt<attempt_count>-<6-char token>.json` |
| File body | `ValidatedBriefing.model_dump_json()` — exactly the model fields; no prompt, no feedback blob, no secret (FR-026) |
| Write | `upload(overwrite=False)` — new file each save; never overwrites/deletes (FR-023) |
| "Most recent" | lexicographically greatest file name in the directory (timestamp prefix ⇒ chronological) |
| "None available" | directory missing or empty (FR-022) |
| Retention | append-only — Feature-002 performs no pruning and no deletion of superseded files (planning decision 4, 2026-09-03; Clarification 2026-09-03). A retention policy is a later story. |
| Failure | any Files-API error on write, or a non-not-found error on read ⇒ `BriefingStorageError` (FR-024) |

## Configuration (new key in `config.Settings`)

| Setting | Env var | Required? | Default / fallback |
|---|---|---|---|
| `briefing_volume` | `BRIEFING_VOLUME` | no | unset/blank ⇒ `None` ⇒ `build_service` uses `InMemoryBriefingStore` |

`validate_volume_path(path) -> str` (new, `config.py`): must start `/Volumes/`, have ≥3
segments after it (catalog/schema/volume), each segment a safe name; raises `ConfigurationError`
otherwise. Invoked from `Settings.from_env` only when `BRIEFING_VOLUME` is non-blank. No OpenAI
settings (US-13).

## State — validated briefing per student (extends Feature-001, unchanged in shape)

```
(no validated briefing)
   │ request (flagged at risk, none stored) → generation seam → validation seam
   │        pass ⇒ save_validated(attempt_count=1) ⇒ return                                    (FR-001 F-001)
   │        first-attempt failure ⇒ RetryWorkflow.run(context, first_outcome)                  (Feature-002)
   │             Attempt 2 pass          ⇒ Produced(attempt_count=2) ⇒ StudentService._persist ⇒ return   (FR-014/FR-019)
   │             Attempt 2 fail (gen)    ⇒ TerminalFailure("generation") ⇒ 502, nothing stored (FR-012/FR-016/FR-017)
   │             Attempt 2 fail (valid.) ⇒ TerminalFailure("validation") ⇒ 502, nothing stored (FR-013)
   │             ConfigurationError      ⇒ propagates ⇒ 503, nothing stored                    (R4)
   ▼
[most-recent validated briefing]  ── request (no regenerate) ─▶ get_latest_validated ⇒ return, no generation  (Feature-001 FR-035)
   │                               ── retrieve (GET / MCP) ────▶ get_latest_validated ⇒ return                 (Feature-001 FR-028)
   │
   │ regenerate=true, still at risk
   ▼ generation seam → validation seam → (retry as above)
        Attempt 2 pass            ⇒ save_validated(attempt_count=2) ⇒ new most-recent
        terminal failure / storage error ⇒ explicit error; previous most-recent left in place  (FR-018, Feature-001 FR-037)
```

"Most recent" is the store's responsibility; for `VolumeBriefingStore` it is the greatest
timestamped filename. Superseded briefings are not removed but need not be retrievable
(Clarification 2026-09-03).
