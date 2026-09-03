# Phase 1 Data Model: Feature-001 (US-08)

Entities, fields, relationships, and state for the backend. Read-only inputs come from
team-owned Delta tables. Feature-001 defines the seam objects and the validated-briefing model;
the concrete persisted form is US-15. Types are described behaviourally; concrete Pydantic edits
land in `models.py` at implementation time.

## Read-only inputs (not modified by this feature)

### StudentPrediction (existing model — unchanged)

Source: `workspace.student_aggregate.student_attrition_risk_prediction`, one row per
`student_deidentified_hash`.

| Field | Type | Notes |
|---|---|---|
| `student_deidentified_hash` | str | the only student identifier used |
| `attrition_risk_percentage` | float 0–100 | **relative ranking score, not a calibrated probability** (spec FR-006) |
| `attrition_risk_flag` | bool | authoritative at-risk determination (probability ≥ 0.50) — spec FR-005/FR-034 |
| `prediction_threshold` | float 0–1 | stored constant 0.50 |
| `mlflow_run_id` | str \| null | traceability |
| `scored_at` | datetime \| null | traceability |

Validation: a missing row → `StudentNotFoundError` (spec FR-023). `attrition_risk_flag` false →
`StudentNotAtRiskError` (spec FR-034).

### ApprovedModelFeatureValues (new — the briefing-context feature set)

The 21 approved feature values for one student, assembled from the fact table plus two
dimension left-joins (`research.md` R1 has the full table and join keys). An ordered mapping
`feature_name -> value | UNAVAILABLE`. This is a **new, separate** retrieval used only to build
the `BriefingGenerationContext`; it does not replace the existing 11-field `StudentSnapshot`
used by the unchanged `GET /api/students/{hash}` profile endpoint.

- 16 fact-owned columns; 4 from `dwh_curriculum__course` (join `course_key_hash`); 1 from
  `dwh_learning_and_teaching__teaching_period` (join `teaching_period_key_hash`).
- Sensitive attributes (`socioeconomic_status`, `regional_remote_status`, `student_gender`,
  `student_is_international_student`, `student_is_first_nations_student`) are carried as context
  only and are never labelled causal (spec FR-011).
- Validation: a source column absent from `information_schema` → that feature is `UNAVAILABLE`;
  the request still proceeds (spec FR-007). Identifiers, join keys, the target, and leakage
  columns are never included.

### StudentRiskProfile (existing model — unchanged by Feature-001)

`{ prediction: StudentPrediction, snapshot: StudentSnapshot | None }` — unchanged. The 21
approved feature values are retrieved separately by `StudentRepository.get_model_features` and
assembled directly into the `BriefingGenerationContext`; they are **not** added to
`StudentRiskProfile` or to the existing `GET /api/students/{hash}` response by Feature-001.
Exposing the 21 features on the profile endpoint, if a later story such as US-10 needs it, is
out of Feature-001 scope.

## Seam objects (defined by Feature-001, imported by US-12/13/14/15 and Feature-002)

### BriefingGenerationContext

The assembled input handed to the generation seam.

| Field | Type | Notes |
|---|---|---|
| `student_deidentified_hash` | str | |
| `prediction` | StudentPrediction | risk result carried verbatim |
| `features` | ApprovedModelFeatureValues | all 21, with `UNAVAILABLE` markers as needed; labelled non-causal (FR-011) |
| `instructions_id` | str | which `BriefingInstructions` implementation composed the prompt |
| `composed_prompt` | str | output of `BriefingInstructions.compose`; never logged in full (FR-031) |

### ValidationOutcome

Returned by the validation seam.

| Field | Type | Notes |
|---|---|---|
| `passed` | bool | |
| `failed_criteria` | list[str] | empty in the interim; populated by US-14; consumed by Feature-002 |
| `feedback` | str \| null | interim null; populated by US-14; consumed by Feature-002 |
| `validator_id` | str | e.g. `"interim-pass-through"`; distinguishes interim from final (FR-016) |

### FirstAttemptOutcome (discriminated union — the retry-seam input)

- `GenerationFailed { category: str }` — the generation seam failed before a draft (FR-019).
- `ValidationFailed { outcome: ValidationOutcome }` — a draft was produced but did not pass.

### BriefingOutcome (discriminated union — the retry-seam output)

- `Produced { briefing: ValidatedBriefing }` — a validated briefing (from attempt 1, or from
  Feature-002's attempt 2).
- `TerminalFailure { category: "generation" | "validation" }` — no validated briefing; the
  backend returns an explicit error and stores nothing new (spec FR-021).

## Briefing entities

### DraftBriefing

A briefing returned by the generation seam that has not passed validation. Transient. Never
handed to the persistence seam, never returned by retrieval (spec FR-026, FR-029).

### ValidatedBriefing (returned to callers; handed to the persistence seam)

| Field | Type | Notes |
|---|---|---|
| `student_deidentified_hash` | str | |
| `text` | str | the briefing body |
| `source` | str | `"generated"` on a fresh run; `"stored"` when returned from the persistence seam without regeneration |
| `validated` | bool | always true for anything returned to a caller (spec FR-029) |
| `validator_id` | str | provenance of the validation decision |
| `generated_at` | datetime (UTC) | |
| `attempt_count` | int | 1 for a Feature-001-only success; 2 when Feature-002 produced it |
| `mlflow_run_id` | str \| null | risk-result traceability snapshot |
| `risk_percentage` | float | snapshot at generation time |
| `at_risk_flag` | bool | |
| `prediction_threshold` | float | |
| `scored_at` | datetime \| null | |

Feature-001 defines these fields. **How they are persisted (file/table, path, format, naming,
retention) is US-15.** Feature-001's `InMemoryBriefingStore` holds `ValidatedBriefing` objects
directly.

Rules (Feature-001 orchestration): only an object with a passing `ValidationOutcome` is passed
to `save_validated` (FR-025); a persistence-seam failure raises `BriefingStorageError` and
leaves any previous validated briefing untouched (FR-024/FR-037).

### BriefingWorkflowLogRecord (transient — not persisted as a table)

Metadata-only log line: `student_deidentified_hash`, `outcome`
(`generated` | `returned_existing` | `not_at_risk` | `not_found` | `terminal_generation` |
`terminal_validation` | `storage_error`), `attempt_count`, `validator_id`, timestamps,
`exception_class` when applicable. **Never** contains prompt text, briefing text, or secrets
(spec FR-031/FR-032).

## State — validated briefing per student

```
(no validated briefing)
      │  request (flagged at risk)  →  precondition → context assembly → generation seam → validation seam
      │                                pass ⇒ persistence seam.save_validated ⇒ return                 (FR-018)
      ▼
[most-recent validated briefing]  ── request (no regenerate) ──▶ persistence seam.get_latest_validated ⇒ return, no generation seam call   (FR-035)
      │                              ── retrieve (GET / MCP) ───▶ persistence seam.get_latest_validated ⇒ return                            (FR-028)
      │
      │  request with regenerate=true, still flagged at risk                                            (FR-036)
      ▼
   generation seam → validation seam
      │ pass            ⇒ persistence seam.save_validated ⇒ new most-recent                             (FR-037)
      │ terminal failure⇒ explicit error; previous most-recent left in place                           (FR-037)
```

Not flagged at risk at any request → explicit "not flagged at risk", no state change, no seam
calls for generation (spec FR-034). "Most recent" is a persistence-seam contract implemented by
US-15.

## Configuration (new keys in `config.Settings`)

| Setting | Env var | Required? | Default / fallback |
|---|---|---|---|
| `course_table` | `DATABRICKS_COURSE_TABLE` | no | `workspace.student_aggregate.dwh_curriculum__course`; blank disables the course-dimension features |
| `teaching_period_table` | `DATABRICKS_TEACHING_PERIOD_TABLE` | no | `workspace.student_aggregate.dwh_learning_and_teaching__teaching_period`; blank disables `teaching_period` |

Both go through the existing `validate_table_identifier`. **No OpenAI or Volume settings are
added by Feature-001** — `OPENAI_*` arrives with US-13 and `BRIEFING_VOLUME` (plus any
Volume-identifier validation) with US-15.
