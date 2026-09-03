# Feature Specification: Feature-002 — Briefing Retry and Validated Briefing Storage (US-15)

**Feature Branch**: `002-briefing-retry-and-storage`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "Create the Feature-002 specification for Product Backlog US-15: Briefing Retry and Validated Briefing Storage. Use the amended project constitution v1.1.0, the Feature-002 repository investigation and confirmed design decisions, the merged Feature-001 artifacts, Product Backlog US-15 and the Physical Solution Design, and the existing source code as implementation context only. Define WHAT Feature-002 must accomplish — observable behaviour, acceptance criteria, boundaries, dependencies, and failure behaviour — without prescribing implementation structure or inventing the unresolved US-13 generation details, US-14 validation criteria, or exact retry-prompt wording."

## Overview

Feature-002 is **Product Backlog US-15 — Briefing Retry and Validated Briefing Storage**, and it
completes that story in full. It supplies the two concrete capabilities that Feature-001 (US-08)
defined as integration boundaries and shipped only as placeholders:

- **The exceptional single-retry workflow.** When the first attempt at a Structured Advisor
  Briefing does not produce a validated briefing — the generated briefing failed validation, or
  generation failed with a retryable error before any draft existed — the backend performs
  exactly one further generation attempt, revalidates its result, and either returns the
  now-validated briefing or terminates with an explicit briefing-failure result.
- **The governed validated-briefing storage.** The validated-briefing store gains its concrete
  implementation backed by the project's Databricks Unity Catalog Volume storage, replacing the
  in-memory placeholder in deployed environments while honouring the existing store boundary
  unchanged.

Feature-002 **consumes and does not redefine** the boundaries established by Feature-001. The
concrete generative integration is US-13; the concrete Structured Advisor Briefing
acceptance-criteria and validation rules are US-14. Feature-002 invokes the generation and
validation boundaries and consumes their results; it defines neither. It also does not define
the exact wording or structure of the retry request handed to the generation boundary — only
what that request must be derived from.

## Backlog Alignment

| Backlog story | Owns | Feature-002's relationship |
|---|---|---|
| US-08 | Application backend: risk-data retrieval + briefing-request coordination | Delivered by Feature-001 (merged). Feature-002 fills its retry and persistence boundaries without changing its orchestration. |
| US-12 | Final briefing prompt, instructions, sections, language guidance, acceptance-criteria content | Feature-002 consumes the instructions provenance carried in the generation context; it defines no instruction content. |
| US-13 | Concrete Generative AI / OpenAI implementation that generates a draft | Feature-002 invokes the generation boundary for the retry attempt and handles its result/failure; it does not implement the integration. |
| US-14 | Actual acceptance-criteria validation behaviour and Validation Feedback content | Feature-002 invokes the validation boundary on the retry briefing and consumes its outcome (failed criteria, feedback); it defines no criteria. |
| **US-15** | The concrete single-retry behaviour **and** the concrete governed validated-briefing storage | **This feature** |
| US-16 | Final end-to-end integration of all components | Feature-002 must be compatible with it but must not expand scope to complete it. |
| US-17 / US-18 | Broad application and complete briefing-workflow testing | Feature-002 carries only proportionate tests of its own behaviour. |

## Clarifications

### Session 2026-09-03 (confirmed Feature-002 product decisions)

The following decisions were settled with the product owner from the Feature-002 repository
investigation and are authoritative for this specification.

- Feature-002 completes US-15 in full: the exceptional single-retry workflow **and** the
  concrete governed Unity Catalog Volume-backed implementation of the existing briefing-store
  boundary.
- US-14 owns the concrete acceptance-criteria and validation rules. Feature-002 consumes the
  existing validation boundary and its outcome rather than defining or duplicating validation
  logic.
- Exactly one retry is permitted, after either an Attempt 1 validation failure or a retryable
  generation failure. A retryable generation failure is any failure from the generation
  boundary other than a configuration error. A configuration error is never retried and is
  surfaced unchanged.
- For a validation-failure retry, the retry request is built from the original
  briefing-generation context together with the failed acceptance criteria and Validation
  Feedback **where the validation boundary provided them**. Missing criteria or feedback are
  never fabricated. For a generation-failure retry, the retry uses the original context and no
  validation feedback exists to carry.
- Attempt 2 is always final. Generation failure on Attempt 2 → terminal generation failure;
  a briefing that fails validation on Attempt 2 → terminal validation failure; a briefing that
  passes validation on Attempt 2 → a successful validated briefing with an attempt count of 2.
  No third generation attempt is ever performed.
- After a terminal failure the backend returns the existing application-visible briefing-failure
  result, substitutes no deterministic or template briefing, stores nothing as a validated
  output, and leaves any previously stored validated briefing in place.
- Feature-001's persistence orchestration is preserved: a validated retry result is returned
  through the existing successful-outcome path and persisted by the existing service/store
  workflow. The retry workflow does not duplicate persistence responsibility.
- No new advisor-visible indication that a briefing came from Attempt 2 is required; the
  existing attempt-count metadata is sufficient.
- The currently unwired legacy provider classes (the template briefing provider and the
  Databricks managed-model briefing provider) are left unchanged. Feature-002 undertakes no
  unrelated cleanup.
- Feature-002 must be independently specifiable and testable using controlled/stub generation
  and validation outcomes and the existing store contract. The final US-13 and US-14
  implementations are not prerequisites for specifying or testing it.

### Session 2026-09-03

- Q: Must the governed store retain superseded validated briefings as retrievable history, or
  only guarantee that the most-recent validated briefing per student stays available? → A:
  Most-recent only. The store never removes or corrupts a student's current most-recent
  validated briefing, but superseded briefings need not be retained or individually
  retrievable, and a concrete retention or pruning policy for superseded briefings is out of
  Feature-002 scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recover from a first-attempt failure with a single retry (Priority: P1)

An academic advisor's briefing request for an at-risk student reaches the backend and the first
attempt does not produce a validated briefing. Either the generated briefing failed validation,
or generation failed with a retryable error before any draft existed. The backend performs
exactly one further generation attempt. For a validation failure it derives the retry request
from the original generation context plus any failed acceptance criteria and Validation Feedback
the validation boundary reported. For a generation failure it retries from the original context.
The resulting briefing is validated again; if it passes, it is returned as the successful result
and persisted through the existing success path, recording an attempt count of 2.

**Why this priority**: This is the defining purpose of Feature-002 — the only part that turns an
otherwise-failed briefing request into a briefing the advisor can use. Every other part of the
feature exists to make this safe or to persist its result.

**Independent Test**: With a stub generation boundary set to fail once then return a draft, and a
stub validation boundary set to fail once then pass, a single briefing request produces exactly
two generation attempts and returns a validated briefing with an attempt count of 2. Repeating
with the generation boundary raising a retryable error on the first call exercises the
generation-failure retry path. No concrete generative provider or final validator is required.

**Acceptance Scenarios**:

1. **Given** an at-risk student with no stored validated briefing, **When** the first generated
   briefing fails validation and the second generated briefing passes validation, **Then** the
   backend returns the second briefing as the successful result with an attempt count of 2 and
   it becomes the student's most-recent stored validated briefing.
2. **Given** the same request, **When** the first attempt fails validation with failed
   acceptance criteria and feedback available from the validation boundary, **Then** the retry
   request incorporates those failed criteria and that feedback together with the original
   generation context.
3. **Given** the same request under the interim pass-through validator, **When** the first
   attempt is treated as failed with no failed criteria and no feedback available, **Then** the
   retry request is constructed from the original generation context alone and no criteria or
   feedback are fabricated.
4. **Given** an at-risk student, **When** the first generation attempt fails with a retryable
   error before any draft exists and the second attempt produces a briefing that passes
   validation, **Then** the backend returns that briefing with an attempt count of 2.
5. **Given** any retry, **When** the retry request is assembled, **Then** it carries the same
   student identifier, attrition-risk result, approved feature values, and instructions
   provenance as the first attempt, with no change to their factual content.
6. **Given** a retry that produces a briefing, **When** the briefing is produced, **Then** the
   same validation boundary is invoked on it before any success is reported.
7. **Given** a first attempt that failed with a configuration error from the generation
   boundary, **When** the backend responds, **Then** no retry is attempted and the
   configuration error is surfaced unchanged.
8. **Given** a successful retry, **When** the validated briefing is handed to the persistence
   boundary, **Then** it is persisted through the same path as a first-attempt success and the
   retry workflow does not itself perform a separate persistence step.

---

### User Story 2 - Fail safely when the retry also does not produce a valid briefing (Priority: P2)

The single retry attempt also fails — generation fails again, or the second briefing fails
validation. The backend stops. It performs no third attempt, returns the existing
application-visible briefing-failure result carrying the last-failure category, substitutes no
template or deterministic briefing, stores nothing as a validated output, and leaves any
previously stored validated briefing for that student untouched.

**Why this priority**: This protects the integrity of every briefing an advisor eventually sees
and bounds the exceptional path. Lower than P1 because, without the retry in P1, it only
reproduces Feature-001's existing "fail cleanly" behaviour.

**Independent Test**: With the generation and validation stubs set to fail on both attempts, a
briefing request performs exactly two generation attempts, ends in the existing briefing-failure
error with the correct category, and the persistence boundary holds no new briefing. With a
prior validated briefing seeded for the student, that briefing is still returned by the
retrieval path after the terminal failure.

**Acceptance Scenarios**:

1. **Given** a failed first attempt, **When** the retry attempt also fails during generation,
   **Then** the backend returns the existing briefing-failure result with category "generation"
   and performs no third attempt.
2. **Given** a failed first attempt, **When** the retry produces a briefing that fails
   validation, **Then** the backend returns the existing briefing-failure result with category
   "validation" and performs no third attempt.
3. **Given** any terminal failure after the retry, **When** the backend responds, **Then** no
   template, deterministic, or otherwise unvalidated briefing is returned or stored as a
   successful validated briefing.
4. **Given** any terminal failure after the retry, **When** the backend responds, **Then** no
   briefing content from either attempt is stored as a validated output or retained beyond the
   request.
5. **Given** a student who already has a stored validated briefing, **When** a regeneration
   request ends in terminal failure after the retry, **Then** the previously stored validated
   briefing is unchanged and remains the one returned by retrieval and by a later
   non-regeneration request, alongside the explicit error.
6. **Given** a terminal failure, **When** the backend maps it to an application response,
   **Then** it uses the existing briefing-failure response and status mapping and introduces no
   new failure response shape.

---

### User Story 3 - Persist validated briefings in governed Unity Catalog Volume storage (Priority: P3)

The validated-briefing store gains its concrete governed implementation, backed by the project's
Databricks Unity Catalog Volume storage, replacing the in-memory placeholder in deployed
environments. It implements the existing store boundary unchanged: it stores only validated
briefings, reports whether a student has one, returns the most-recent validated briefing,
returns an explicit "none available" result when there is none, never loses or corrupts the
student's current most-recent validated briefing (superseded briefings need not be retained),
and signals an explicit error when a briefing cannot be stored.

**Why this priority**: It completes the persistence half of US-15 and makes validated briefings
durable across sessions and deployments. It is independent of the retry workflow and can be
delivered and verified on its own against the existing store contract.

**Independent Test**: The governed store is exercised through the existing store-contract
scenarios — save a validated briefing then retrieve it; retrieve for a student with none; save a
second and confirm the most-recent is the one returned and that a subsequent failed run does not
lose it; simulate a storage failure and confirm the explicit error — with no retry workflow
involved and no change to the service or orchestration.

**Acceptance Scenarios**:

1. **Given** a validated briefing for a student, **When** it is handed to the governed store and
   later retrieved, **Then** the same validated briefing is returned and the student is reported
   as having a stored validated briefing.
2. **Given** a student with no stored validated briefing, **When** the retrieval path runs,
   **Then** an explicit "none available" result is returned and no generation occurs.
3. **Given** a student for whom a newer validated briefing has been stored after an earlier one,
   **When** the retrieval path runs, **Then** the most-recent validated briefing is returned;
   retaining or exposing the earlier briefing is not required.
4. **Given** a draft briefing or a briefing that failed validation, **When** storage is
   attempted, **Then** it is not stored — only validated briefings are ever accepted.
5. **Given** the governed store cannot write a briefing, **When** the save is attempted,
   **Then** an explicit storage error is surfaced, the request is not reported successful, and
   no partial briefing is left stored.
6. **Given** the governed store replaces the in-memory placeholder, **When** the existing
   service and retry orchestration run against it, **Then** their observable behaviour and
   acceptance scenarios are unchanged.

---

### Edge Cases

- **First attempt failed validation with no criteria and no feedback** (interim validator): the
  retry runs from the original generation context only; nothing is fabricated.
- **The retry's generation attempt returns empty content**: treated as a generation failure for
  Attempt 2 and therefore a terminal generation failure; no third attempt.
- **The retry produces a briefing identical to the rejected first briefing**: it is still
  validated again and returned only if it passes; there is no special-casing.
- **A configuration error surfaces from the generation boundary on the retry attempt itself**:
  no third attempt; the configuration error is surfaced unchanged rather than converted into a
  terminal generation failure.
- **The persistence boundary fails when storing the validated retry briefing**: the existing
  explicit storage-error result is surfaced and the request is not reported successful.
- **Terminal failure on a regeneration for a student who already has a validated briefing**:
  the student's existing most-recent validated briefing is retained and still returned by
  retrieval and by a later non-regeneration request.
- **A newer validated briefing supersedes an earlier one for a student**: the retrieval path
  returns the most-recent; the store need not retain the superseded briefing, and it never
  loses or corrupts the current most-recent one.
- **The governed store is unreachable at read time**: the retrieval path surfaces an explicit
  error, distinct from the "none available" result.
- **A first-attempt outcome that is neither a generation failure nor a validation failure
  reaches the retry workflow**: out of scope as an input; the workflow is specified only for the
  two defined first-attempt outcomes.
- **Concurrent briefing requests for the same student**: not specially handled; the
  most-recent-wins store contract from Feature-001 is retained (see Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

#### Retry trigger and scope

- **FR-001**: Feature-002 MUST supply the concrete retry workflow behind the retry boundary
  defined by Feature-001. It MUST be invoked exactly once per briefing generation or
  regeneration run, only at the single first-attempt failure hand-off point Feature-001 already
  defines, and it MUST NOT change the Feature-001 orchestration or that hand-off point.
- **FR-002**: The retry workflow MUST perform at most one additional briefing-generation attempt
  ("Attempt 2") per run. A third generation attempt MUST never occur.
- **FR-003**: The retry workflow MUST act on both first-attempt failure kinds it can receive:
  a first attempt whose generated briefing did not pass validation, and a first attempt that
  failed with a retryable generation error before any draft existed.
- **FR-004**: A "retryable" generation error MUST be defined as any failure reported by the
  generation boundary other than a configuration error. A configuration error MUST NOT trigger a
  retry and MUST be surfaced unchanged; Feature-002 MUST preserve the Feature-001 rule that a
  configuration error is never routed into the retry workflow.
- **FR-005**: The retry workflow MUST conclude every run it is given with exactly one outcome —
  a validated briefing or a terminal failure — and MUST NOT leave a request without an outcome
  or propagate an unexpected error past its boundary.

#### Validation-failure retry

- **FR-006**: For a validation-failure retry, the retry workflow MUST reuse the original
  briefing-generation context from the first attempt — the same student identifier,
  attrition-risk result, approved feature values, and instructions provenance — and MUST NOT
  rebuild it from source or alter its factual content.
- **FR-007**: For a validation-failure retry, the retry request MUST incorporate the failed
  acceptance criteria from the first attempt's validation outcome where the validation boundary
  provided them, and the Validation Feedback where the validation boundary provided it.
- **FR-008**: The retry workflow MUST NOT invent, infer, or fabricate failed acceptance criteria
  or Validation Feedback that the validation boundary did not provide. When the first attempt's
  validation outcome carries neither, the retry MUST proceed from the original context alone.
- **FR-009**: When Attempt 2 of a validation-failure retry produces a briefing, the retry
  workflow MUST invoke the same validation boundary on that briefing and decide the run's
  outcome from its result.

#### Generation-failure retry

- **FR-010**: For a generation-failure retry, the retry workflow MUST perform Attempt 2 using
  the original briefing-generation context and MUST NOT fabricate validation feedback or failed
  criteria, none of which exist because the first attempt produced no draft.
- **FR-011**: When Attempt 2 of a generation-failure retry produces a briefing, the retry
  workflow MUST invoke the validation boundary on it and decide the run's outcome from its
  result.

#### Attempt 2 outcomes

- **FR-012**: When Attempt 2 fails during generation, the run MUST terminate as a generation
  failure, carrying the last-failure category "generation". No further attempt is made.
- **FR-013**: When Attempt 2 produces a briefing that does not pass validation, the run MUST
  terminate as a validation failure, carrying the last-failure category "validation". No further
  attempt is made.
- **FR-014**: When Attempt 2 produces a briefing that passes validation, the retry workflow MUST
  return it as a validated briefing in the existing successful-outcome form, carrying an attempt
  count of 2, so that the existing orchestration returns and persists it exactly as it does a
  first-attempt success.

#### Terminal failure

- **FR-015**: On a terminal failure the retry workflow MUST hand back the existing
  terminal-failure outcome carrying the last-failure category, which the existing orchestration
  maps to the current application-visible briefing-failure result and its established status
  mapping. Feature-002 MUST introduce no new failure response shape or status code.
- **FR-016**: On a terminal failure the backend MUST NOT substitute a deterministic, template,
  or otherwise unvalidated briefing, and MUST NOT report or store any such substitute as a
  successful validated briefing.
- **FR-017**: On a terminal failure no briefing content from either attempt may be stored as a
  validated output, and briefing content from the failed attempts MUST NOT be retained beyond
  the request that produced it.
- **FR-018**: A terminal failure MUST leave any previously stored validated briefing for that
  student in place — still the most-recent one returned by the retrieval path and by a
  subsequent non-regeneration request — alongside the explicit error.

#### Persistence of the retry result

- **FR-019**: A validated briefing produced by Attempt 2 MUST be persisted through the existing
  service-and-store persistence path that already handles a produced retry result. The retry
  workflow MUST NOT duplicate persistence orchestration, call the persistence boundary directly
  for the success path, or introduce a second persistence code path.
- **FR-020**: When the persistence boundary reports that the validated retry briefing could not
  be stored, the existing explicit storage-error result MUST be surfaced and the request MUST
  NOT be reported as successful.

#### Governed validated-briefing storage

- **FR-021**: Feature-002 MUST provide the concrete governed implementation of the existing
  briefing-store boundary, backed by the project's governed Databricks Unity Catalog Volume
  storage, and it MUST be usable in place of the in-memory placeholder in deployed environments.
- **FR-022**: The governed store MUST honour the established store contract without change: it
  accepts only validated briefings for storage; it reports whether a student has any stored
  validated briefing; it returns the most-recent stored validated briefing for a student; and it
  returns an explicit "none available" result when the student has none.
- **FR-023**: Once a validated briefing has been stored for a student, the governed store MUST
  always be able to return that student's most-recent validated briefing, and a later failed run
  MUST NOT remove or corrupt it (consistent with Feature-001). When a newer validated briefing
  is stored it becomes the most-recent. The store is NOT required to retain previously
  superseded validated briefings or keep them individually retrievable; a concrete retention or
  pruning policy for superseded briefings is out of Feature-002 scope. How "most recent" is
  determined is owned by the store.
- **FR-024**: When the governed store cannot store a validated briefing, it MUST report that
  failure through the existing storage-error signal so the orchestration surfaces an explicit
  error; it MUST NOT fail silently and MUST NOT leave a partially written briefing.
- **FR-025**: The governed store MUST be substitutable for the in-memory placeholder with no
  change to the Feature-001 orchestration, the service layer, or the retry workflow — the store
  boundary MUST remain the only integration point.
- **FR-026**: The governed store MUST hold only validated briefing outputs and their associated
  workflow metadata. It MUST NOT store draft or failed briefings, full generation prompts, or
  secrets.
- **FR-027**: The governed store MUST use the existing Databricks Unity Catalog governance and
  secret-management mechanisms for its storage location, credentials, and access. No credentials
  may be hard-coded and no storage service parallel to the existing store boundary may be
  introduced.

#### Boundaries and non-duplication

- **FR-028**: Feature-002 MUST reuse the generation, instructions, validation, retry, and
  persistence boundaries and the shared workflow types established by Feature-001, and MUST NOT
  redesign them, fork them, or create parallel equivalents.
- **FR-029**: Feature-002 MUST NOT define, implement, or duplicate the concrete Structured
  Advisor Briefing acceptance criteria or validation logic, which are owned by US-14. It
  consumes the validation boundary and its outcome only.
- **FR-030**: Feature-002 MUST NOT define the concrete generative integration, which is owned by
  US-13, or the exact wording and structure of the retry request handed to the generation
  boundary. The specification fixes only what that request MUST be derived from; the
  request-construction mechanism is a planning concern.
- **FR-031**: Feature-002 MUST leave the currently unwired legacy provider classes — the
  template briefing provider and the Databricks managed-model briefing provider — unchanged, and
  MUST NOT undertake unrelated refactoring or cleanup.
- **FR-032**: Feature-002 MUST NOT introduce a new advisor-visible indication that a returned
  briefing came from a second attempt. The existing attempt-count workflow metadata is the only
  record of the retry.

#### Observability and privacy

- **FR-033**: Feature-002 workflow logging MUST remain metadata-only, consistent with
  Feature-001 — no full prompts, no full briefing text, no secrets — and MUST record enough
  metadata (student identifier, attempt count, outcome category, validator provenance) to trace
  a retried request and its result.

#### Independence and testability

- **FR-034**: The retry workflow and the governed store MUST each be independently specifiable
  and testable — the retry workflow using controlled/stub generation and validation outcomes,
  the governed store using the existing store-contract scenarios — without the final US-13
  generation implementation or the final US-14 validation implementation being present.

### Key Entities *(include if feature involves data)*

- **Retry Request**: the input to Attempt 2. Always derived from the first attempt's original
  briefing-generation context; for a validation-failure retry it additionally carries the failed
  acceptance criteria and Validation Feedback that the validation boundary reported, and nothing
  it did not. Its factual content matches the first attempt. The concrete construction mechanism
  is a planning decision.
- **First-Attempt Outcome** (defined by Feature-001, consumed here): either "generation failed
  before a draft" or "validation failed", the latter carrying the validation outcome with any
  failed criteria and feedback. Feature-002 consumes this shape and does not redefine it.
- **Retry Outcome** (the existing briefing-outcome type): either a produced validated briefing
  or a terminal failure carrying a last-failure category of "generation" or "validation".
  Feature-002 populates the produced path for Attempt 2 and the terminal path when Attempt 2
  fails.
- **Validated Structured Advisor Briefing** (defined by Feature-001): the only briefing form
  returned to a caller or handed to the store. Its attempt count is 2 when produced by the
  retry. Feature-002 adds no fields.
- **Attempt Count**: workflow metadata — 1 for a first-attempt success, 2 for a retry success.
  Not surfaced as a distinct advisor-facing label.
- **Governed Validated-Briefing Store**: the concrete Unity Catalog Volume-backed implementation
  of the existing store boundary — validated-only, a guaranteed retrievable most-recent
  validated briefing per student, explicit "none available", explicit storage-failure signal;
  superseded briefings need not be retained. Concrete location, file format, and naming are
  planning decisions bounded by the existing governance; a retention or pruning policy for
  superseded briefings is out of scope.
- **Terminal Briefing Failure**: the existing application-visible "briefing could not be
  produced" result, carrying a last-failure category of "generation" or "validation" and mapped
  by the existing status convention. Feature-002 introduces no new failure result.
- **Workflow Metadata** (defined by Feature-001): student identifier, timestamps, attempt count,
  outcome category, validator identifier. Metadata-only; never briefing text, prompts, or
  secrets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every first-attempt failure eligible for retry (a validation failure, or a
  retryable generation failure), exactly one additional generation attempt is performed — never
  zero, never two or more; 0 runs reach a third generation attempt.
- **SC-002**: 100% of retried runs end with exactly one application-visible outcome — a
  validated briefing or an explicit briefing-failure error; 0 end with no result surfaced.
- **SC-003**: 100% of briefings returned or stored from a retried run have a passing validation
  outcome; 0 unvalidated, template, or deterministic briefings are returned or stored as a
  successful validated briefing after a retry.
- **SC-004**: A configuration error from the generation boundary results in 0 retry attempts and
  is surfaced unchanged in 100% of cases.
- **SC-005**: When Attempt 2 succeeds, the returned validated briefing reports an attempt count
  of 2 in 100% of cases and is persisted through the same path as a first-attempt success, with
  0 separate persistence paths invoked by the retry workflow.
- **SC-006**: For validation-failure retries where failed criteria and/or feedback were
  available, 100% of retry requests carry them; across all retries, 0 retry requests contain
  failed criteria or feedback the validation boundary did not report.
- **SC-007**: After a terminal failure following Attempt 2, the student's previously stored
  validated briefing (if any) is unchanged and is still the one returned by retrieval in 100% of
  cases; 0 failed or draft briefings are stored.
- **SC-008**: The governed store returns the most-recent validated briefing in 100% of
  retrievals where at least one exists, and an explicit "none available" result in 100% where
  none exists; 0 drafts or failed briefings are ever returned.
- **SC-009**: 100% of governed-store write failures are surfaced as an explicit storage error;
  0 are reported as success and 0 leave a partially written briefing.
- **SC-010**: The governed store passes the same store-contract acceptance scenarios as the
  in-memory placeholder with no change to the service or retry orchestration, verified by
  substituting it and re-running those scenarios.
- **SC-011**: The retry workflow's acceptance scenarios all pass using controlled/stub
  generation and validation outcomes, with no US-13 or US-14 final implementation present.
- **SC-012**: 0 full prompts, full briefing texts, or secrets appear in application logs or in
  the governed store's retained metadata for retried requests.

## Assumptions

- Feature-002 attaches to the retry and persistence boundaries exactly as Feature-001 defined
  them. The application's composition point swaps the real retry workflow and the governed store
  in place of the `RetryNotConfigured` and in-memory placeholders with no orchestration change.
- The first-attempt outcome handed to the retry workflow already distinguishes a generation
  failure from a validation failure and, for the latter, carries the validation outcome
  including any failed criteria and feedback. Feature-002 relies on that shape rather than
  re-deriving it.
- Under the interim pass-through validator a validation outcome carries no failed criteria and
  no feedback, so a validation-failure retry proceeds from the original context alone. When
  US-14 lands, the same retry consumes whatever criteria and feedback it reports, with no
  Feature-002 change.
- "Exactly one retry" is a deliberate product limit for the exceptional path, not a configurable
  count. Backoff, scheduling, and asynchronous retry are out of scope.
- The governed store is backed by the project's existing Databricks Unity Catalog Volume
  storage. Concrete path, file format, and naming are planning decisions bounded by the existing
  Unity Catalog governance. The store guarantees only that the most-recent validated briefing
  per student is retrievable; retaining or pruning superseded briefings is out of Feature-002
  scope (see Clarifications, Session 2026-09-03).
- Briefing requests are advisor-interactive and low-concurrency; the most-recent-wins store
  contract from Feature-001 is retained rather than adding locking or de-duplication.
- Timing model (synchronous versus asynchronous), module and class structure,
  dependency-injection wiring, retry-request construction and context-copy mechanics, the Volume
  path, file format and naming, configuration names, logging helper details, and test placement
  are determined during `/speckit-plan` by extending the existing architecture with the minimum
  necessary change. A technical choice that would materially change user-visible behaviour or
  feature scope is flagged for human approval rather than decided silently.
- The machine-learning model, the synthetic-data generation notebooks, and other team-owned
  components are not modified.

## Dependencies

- **Feature-001 (merged)** — the retry and persistence boundaries; the shared workflow types
  (briefing-generation context, validation outcome, first-attempt outcome, briefing outcome,
  validated briefing); the orchestration call order; the metadata-only logging convention; and
  the application-visible failure mapping. Feature-002 fills the retry and storage boundaries
  without changing that orchestration.
- **US-13** — the concrete generative implementation behind the generation boundary. Feature-002
  invokes the boundary for Attempt 2 and handles its result and failure but does not implement
  it. Feature-002 must remain specifiable and testable with a stub in its place.
- **US-14** — the concrete acceptance-criteria validation behind the validation boundary,
  including the failed-criteria identifiers and Validation Feedback it populates. Feature-002
  invokes it on the retry briefing and consumes its outcome but does not implement it, and must
  remain specifiable and testable with a stub in its place.
- **The existing Databricks environment** and its Unity Catalog governance and
  secret-management mechanisms — for the governed validated-briefing storage.
- **US-16** — final end-to-end integration of all components. Feature-002 must be compatible
  with it but must not expand scope to complete it.

## Out of Scope

- The concrete acceptance-criteria and validation rules, and the Validation Feedback content —
  **US-14**.
- The concrete generative integration, provider selection, and its credential handling —
  **US-13**.
- The exact wording and structure of the retry request handed to the generation boundary — a
  `/speckit-plan` and US-12/US-13 concern; Feature-002 fixes only what the retry request is
  derived from.
- More than one retry, a configurable retry count, retry backoff, or scheduled or asynchronous
  retry.
- A retention, archival, or pruning policy for superseded validated briefings, and any
  history-retrieval capability — the governed store guarantees only that the most-recent
  validated briefing per student is retrievable.
- Any new advisor-facing UI or dashboard, and any visible "second attempt" label — **US-09,
  US-10, US-11**.
- Changes to the first-attempt orchestration, the at-risk precondition, or the existing-briefing
  get-or-create behaviour — **Feature-001**.
- Migration or back-fill of previously stored briefings into the governed Volume, and any
  dual-write between the in-memory and governed stores.
- Changes to the legacy unwired provider classes and any unrelated refactoring or cleanup.
- Changes to the machine-learning model, the synthetic-data generation process, or any other
  team-owned notebooks or components.
- Final end-to-end integration of all components — **US-16**.
- Broad application and full briefing-workflow testing beyond Feature-002's own behaviour —
  **US-17, US-18**.
