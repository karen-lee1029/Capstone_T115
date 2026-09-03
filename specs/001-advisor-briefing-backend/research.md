# Phase 0 Research: Feature-001 (US-08)

Resolves the implementation-level choices that remain **inside US-08** after the 2026-09-02
scope correction. Choices that belong to US-12/13/14/15 are recorded here only as "deferred,
seam defined by Feature-001". No open `NEEDS CLARIFICATION` items remain.

## R1. Where the 21 approved model features are read from (US-08)

**Status**: Approved 2026-09-03 (Option A — application-side retrieval/join). The maintenance
exposure is recorded as accepted technical risk **TR-1** in `plan.md`: the application
reconstructs the approved 21-feature input set from the existing tables rather than consuming a
dedicated ML feature-projection table, and the app-side join logic may need updating if the ML
feature set or source-table relationships change later. Mitigations: the 21-feature contract
below is authoritative; retrieval/join logic is isolated behind
`StudentRepository.get_model_features`; no ML transformation logic is duplicated (raw values
only); a future canonical projection table can replace the join via a different repository
implementation without changing Feature-001 orchestration.

**Decision**: Read them at request time with an app-side query: the 16 fact-owned columns from
`workspace.student_aggregate.rpt_student_management__fact__all_enrolment_eftsl__deidentified`,
`LEFT JOIN workspace.student_aggregate.dwh_curriculum__course` on `course_key_hash` for the 4
course-dimension columns, and `LEFT JOIN
workspace.student_aggregate.dwh_learning_and_teaching__teaching_period` on
`teaching_period_key_hash` for `teaching_period`. Single row, filtered by
`student_deidentified_hash`, parameterised. Availability of each column is checked per source
table via `information_schema.columns`; an absent column becomes an "unavailable" marker for
its feature (spec FR-007).

**Rationale**: The ML notebook's Phase 1 assembly (`FEATURE_MANIFEST`, cells 22–31) shows the
21 approved features come from exactly these three tables with exactly these two join keys, and
the model persists **only** the 6-column prediction table. An app-side join is the only way to
obtain all 21 without changing ML-owned code (constitution II, XVI). It is a bounded two-join
single-row lookup.

**Alternatives considered**:
- *Fact-only subset*: rejected — narrows the approved "all 21" scope (FR-003).
- *Ask the ML notebook to persist a canonical 21-feature projection table*: cleaner long-term,
  but a team-owned-notebook change — **not adopted** (decision 2 approved 2026-09-03 in favour
  of the app-side join; modifying the ML implementation is outside Feature-001 scope). A future
  projection table can still replace the join behind the same repository seam.
- *Re-run the model's preprocessing in the app*: rejected — out of scope; the briefing context
  needs raw values, not encoded vectors.

### The 21 features (final names, role, source)

| # | Feature | Role | Source table |
|---|---|---|---|
| 1 | `age_at_census` | numeric | fact |
| 2 | `socioeconomic_status` | categorical (sensitive) | fact |
| 3 | `regional_remote_status` | categorical (sensitive) | fact |
| 4 | `student_gender` | categorical (sensitive) | fact |
| 5 | `student_is_international_student` | categorical/bool (sensitive) | fact |
| 6 | `student_is_first_nations_student` | categorical/bool (sensitive) | fact |
| 7 | `attendance_mode` | categorical | fact |
| 8 | `eftsl` | numeric | fact |
| 9 | `commencing_continuing` | categorical | fact |
| 10 | `commencing_continuing_period` | categorical | fact |
| 11 | `course_admission_load_category` | categorical | fact |
| 12 | `enrolment_year` | numeric | fact |
| 13 | `cumulative_credit_points_enrolled` | numeric | fact |
| 14 | `cumulative_credit_points_passed` | numeric | fact |
| 15 | `cumulative_credit_points_failed` | numeric | fact |
| 16 | `cumulative_credit_points_withdrawn` | numeric | fact |
| 17 | `course_group` | categorical | `dwh_curriculum__course` |
| 18 | `broad_primary_field_of_education` | categorical | `dwh_curriculum__course` |
| 19 | `narrow_primary_field_of_education` | categorical | `dwh_curriculum__course` |
| 20 | `detailed_primary_field_of_education` | categorical | `dwh_curriculum__course` |
| 21 | `teaching_period` | categorical | `dwh_learning_and_teaching__teaching_period` |

Join keys carried on the fact table: `course_key_hash`, `teaching_period_key_hash` (ML notebook
cell 24). Identifiers, join keys, the target, and leakage columns are never placed in the
briefing context.

## R2. Generation seam — concrete provider deferred to US-13

**Decision**: Feature-001 defines a `GenerationProvider` protocol (a draft-returning operation
over the `BriefingGenerationContext`, raising on a pre-draft failure) and ships
`StubGenerationProvider`, which raises "generation not configured". `student_service` invokes
the seam once per run and maps a failure to `FirstAttemptOutcome.GenerationFailed`. The
concrete OpenAI API implementation, the `openai` dependency, provider credentials, and the
egress/data-sharing approval are **US-13**.

**Rationale**: US-08 is "coordinate briefing requests", not implement the generative
integration. A protocol plus a fail-fast stub keeps the backend runnable and fully testable now
and gives US-13 a drop-in point with no orchestration change (spec FR-014, FR-039). The
existing `BriefingProvider` protocol shape and `DatabricksModelBriefingProvider` remain in the
codebase as a reference for US-13.

**Alternatives considered**:
- *Build the OpenAI adapter now*: rejected — it is US-13 and would pull egress approval, secret
  handling, and cost controls into US-08.
- *No generation seam, call a provider directly from the service*: rejected — couples the
  orchestration to a provider and breaks the US-13 boundary.

## R3. Instructions seam — final content deferred to US-12

**Decision**: `BriefingInstructions` protocol with `compose(context) -> str` and an
`instructions_id`. Feature-001 ships `InterimInstructions` reusing the existing safe PoC
`_prompt` text (neutral, forbids causal/longitudinal claims and sensitive inferences),
rendering the 21 feature values as labelled context. Final prompt content, sections, and
language guidance are **US-12**.

**Rationale**: Spec FR-010 permits a minimal interim placeholder and forbids defining final
content. A one-method seam lets US-12 swap in the final instructions with no orchestration
change.

**Alternatives considered**:
- *Leave prompt construction in the provider*: rejected — couples instruction content to the
  provider and blocks clean replacement by US-12.
- *Load instructions from a file/Volume now*: premature — no final content exists.

## R4. Validation seam — real behaviour deferred to US-14

**Decision**: `BriefingValidator` protocol: `validate(draft, context) -> ValidationOutcome`
(`passed`, optional `failed_criteria`, optional `feedback`, `validator_id`). Feature-001 ships
`InterimValidator` — always `passed`, `validator_id="interim-pass-through"`, surfaced as interim
in logs and stored metadata. Tests use `StubValidator` with a configurable outcome. Real
acceptance-criteria validation is **US-14**.

**Rationale**: Spec FR-015–FR-017 require an initiated, replaceable validation step that runs
before final criteria exist and can be exercised with controlled pass/fail. A pass-through
interim keeps the path runnable; the explicit `validator_id` prevents it being mistaken for
final validation.

**Alternatives considered**:
- *No validation step until US-14*: rejected — FR-015 requires the step now, and the retry seam
  needs the `ValidationOutcome` shape.
- *A heuristic interim validator*: rejected — that would be inventing criteria.

## R5. Retry seam — concrete retry deferred to Feature-002 / US-15

**Decision**: `RetryWorkflow` protocol: `run(context, first_outcome) -> BriefingOutcome`, where
`first_outcome` is `GenerationFailed(category)` or `ValidationFailed(ValidationOutcome)` and
`BriefingOutcome` is `Produced(validated_briefing)` or `TerminalFailure(category)`. Feature-001
ships `RetryNotConfigured` which does no generation and returns
`TerminalFailure(first_outcome.category)`. `student_service` calls the seam once, only within a
generation/regeneration run, only on a failed attempt 1.

**Rationale**: Spec FR-019/FR-033 keep all retry logic out of Feature-001 while still requiring
a defined hand-off. Feature-002 (retry) and US-15 (storage of the retry's result) supply the
real implementation. Shared types are defined once by Feature-001.

**Alternatives considered**:
- *Inline "no retry yet, just fail" in the service*: rejected — Feature-002 would then modify
  Feature-001 orchestration code.
- *Event/queue hand-off*: rejected — unnecessary infrastructure for a synchronous single
  retry.

## R6. Persistence seam — governed Volume storage deferred to US-15

**Decision**: `BriefingStore` protocol: `has_validated(hash) -> bool`,
`get_latest_validated(hash) -> ValidatedBriefing | None`, `save_validated(briefing) -> None`.
Feature-001 ships `InMemoryBriefingStore` (dict of ordered lists) as its test / local double
and defines the fields carried on the validated-briefing object. The concrete governed Unity
Catalog Volume storage — path, file format, naming, retention policy, most-recent selection,
`BRIEFING_VOLUME` config, and any Volume-identifier validation — is **US-15**.

**Rationale**: Spec FR-025/FR-028/FR-030 fix the seam contract (validated-only, most-recent,
none-available); US-15 owns "the concrete one-retry behaviour and validated-briefing storage
behaviour" per the Product Backlog. Feature-001 only needs a seam it can test against.

**Alternatives considered**:
- *Implement a JSON-per-briefing Volume writer now*: rejected — it is US-15's named
  responsibility.
- *A temp-directory file store for local mode*: `InMemoryBriefingStore` is simpler and
  sufficient for US-08 verification.

## R7. Local / test operation with placeholder seams

**Decision**: `main.build_service` wires `StubGenerationProvider`, `InterimInstructions`,
`InterimValidator`, `RetryNotConfigured`, and `InMemoryBriefingStore` by default. A generation
request on this default configuration fails fast with an explicit "generation not configured"
error — never a template success. Tests use `MockStudentRepository` (with not-at-risk and
has-existing-briefing fixtures), `InMemoryBriefingStore`, `StubGenerationProvider` /
`StubValidator`.

**Rationale**: Constitution XII and the existing test convention require an offline suite. The
placeholder seams make the full FR-033 orchestration testable with no network, no Delta, and no
concrete downstream story.

## R8. Request semantics for the briefing endpoint (US-08 orchestration)

**Status**: Approved 2026-09-03 (Option A — get-or-create). An existing validated briefing is
returned without invoking the generation seam; a fresh briefing occurs only via an explicit
regeneration request. Feature-001 owns only the routing; concrete generation/validation/retry/
storage stay with US-13/US-14/US-15/Feature-002.

**Decision**: `POST /api/students/{hash}/briefing` becomes "get-or-create": returns the
existing latest validated briefing if one exists, otherwise routes to the generation seam;
`?regenerate=true` forces a fresh seam run. New `GET /api/students/{hash}/briefing` returns the
latest validated briefing or 404 "none available". MCP `generate_student_briefing` gains
`regenerate: bool = false`; new MCP `get_student_briefing` for retrieval.

**Rationale**: Clarification 2 (2026-09-02) requires return-existing by default and an explicit
regeneration path; FR-028 requires a retrieval capability. Reusing the route/tool names keeps
the interface stable except for the one intended behaviour change.

**Alternatives considered**:
- *Separate `:regenerate` sub-resource*: heavier than a boolean flag.
- *`POST` always generates, client checks `GET` first*: pushes the FR-035 guarantee onto every
  client.

## R9. HTTP status conventions (US-08 interface)

**Status**: Approved 2026-09-03. Approved set only, consistent with the existing FastAPI
application:

| Code | Use |
|---|---|
| `404` | The requested student / resource does not exist (unknown or malformed hash; no prediction row; no validated briefing on retrieval). |
| `409` | A valid request conflicts with application state — including a briefing request for a student who is not flagged at risk (FR-034). |
| `422` | Request / input validation only, via the existing FastAPI / Pydantic behaviour. |
| `502` | An invoked downstream briefing-generation dependency fails to produce a valid briefing — covers a retry-seam `TerminalFailure` whether the last cause was generation or its validation gate; the category is in the safe detail text, not a separate code (FR-021). |
| `503` | Required Databricks / data / backend infrastructure is unavailable — Delta source down, the generation seam unconfigured (until US-13), the persistence seam unavailable, or a feature blocked pending human review (FR-008, FR-014, FR-024). |

No additional status codes are introduced. External error bodies stay safe and concise;
internal typed exceptions and `raise ... from exc` chaining are preserved. Earlier drafts split
retry-terminal failures into `502` (generation) and `422` (validation); that split is dropped —
`422` is reserved for FastAPI/Pydantic request validation.
