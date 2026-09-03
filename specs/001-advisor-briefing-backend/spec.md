# Feature Specification: Feature-001 — Databricks Application Backend (US-08)

**Feature Branch**: `001-advisor-briefing-backend`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: "Create the Feature-001 specification using the project constitution, the repository investigation findings, the confirmed answers to the unresolved product decisions, the referenced Physical Solution Design documentation, and the existing source code as implementation context only. Define WHAT Feature-001 must do and its observable behaviour, acceptance criteria, boundaries, dependencies, and failure behaviour, without prescribing implementation structure or inventing the unresolved briefing instructions or acceptance criteria." Corrected 2026-09-02 against the Product Backlog so that Feature-001 covers only US-08.

## Overview

Feature-001 is **US-08 — Databricks Application Backend**: *"As an academic advisor, I want to
use an application backend that retrieves risk data and coordinates briefing requests, so that
dashboard actions and the student briefing workflow operate reliably."*

Feature-001 delivers the backend responsibilities of the Structured Advisor Briefing workflow:

- retrieval of the selected student's existing data, attrition-risk result, and the 21 approved
  machine-learning feature values from the governed Delta tables;
- backend retrieval of at-risk students using the model's own risk flag;
- request processing and end-to-end orchestration of a briefing request — precondition checks,
  the existing-briefing check, the ordered invocation of the generation, validation, retry, and
  persistence steps, and the mapping of every outcome to an application response;
- the service, REST, and MCP interface surface that the advisor-facing stories call;
- the integration seams (interfaces / contracts) through which the later
  briefing-generation, validation, retry, and persistence capabilities are plugged in, plus
  minimal interim placeholder behaviour so the backend is runnable and testable now;
- explicit handling of each dependency's success and failure results.

Feature-001 does **not** implement the concrete generative integration, the final briefing
prompt/instructions, the real acceptance-criteria validation, the one-retry behaviour, the
concrete validated-briefing storage, or the advisor-facing dashboard. Those are separate
Product Backlog stories (see *Backlog Alignment* and *Out of Scope*). Feature-001 defines and
consumes the seams they attach to.

Briefing generation is gated by orchestration rules: a request is routed to generation only for
a student the model flags as at risk, and only when the student has no existing validated
briefing or the advisor explicitly asks for a fresh one. Otherwise a briefing request returns
the student's existing validated briefing without invoking the generation seam.

## Backlog Alignment

| Backlog story | Owns | Feature-001's relationship |
|---|---|---|
| **US-08** | Application backend: risk-data retrieval + briefing-request coordination | **This feature** |
| US-09 | Advisor-facing dashboard / frontend | Not in Feature-001 |
| US-10 | Advisor-facing display of at-risk students | Feature-001 provides the backend risk-data retrieval it consumes |
| US-11 | Advisor-facing student selection and briefing-request interaction | Feature-001 exposes the backend capability that receives the request |
| US-12 | Final reusable briefing prompt, instructions, sections, language guidance, acceptance-criteria content | Feature-001 provides only the instructions seam + a temporary placeholder |
| US-13 | Concrete Generative AI / OpenAI API implementation that generates a draft | Feature-001 invokes a provider seam and handles its result/failure; it does not implement the integration |
| US-14 | Actual acceptance-criteria validation behaviour | Feature-001 defines/uses the validator seam with temporary pass-through behaviour; it defines no acceptance criteria |
| US-15 | Concrete one-retry behaviour **and** validated-briefing storage behaviour | Feature-001 defines the retry and persistence seams only; the retry itself is Feature-002 |
| US-16 | Final end-to-end integration of all components | Feature-001 must be compatible with it but must not expand scope to complete it early |
| US-17 / US-18 | Broad application / dashboard and complete briefing-workflow testing | Feature-001 carries only proportionate tests of its own behaviour and seams |
| US-19 – US-23 | Later refinement, defect resolution, final delivery, documentation, handover | Not in Feature-001 |
| US-24 – US-26 | Solution-design, synthetic-data validation, UI/UX design | Not in Feature-001 |

## Clarifications

### Session 2026-09-02

- Q: When an advisor requests a briefing for a known student who is NOT flagged at risk by the
  model, should the backend generate a briefing or refuse? → A: Refuse. Only students whose
  model at-risk flag is set (probability ≥ 0.50) may be routed to generation; a request for a
  non-flagged known student returns an explicit "not flagged at risk" result and no generation
  is invoked.
- Q: When an advisor requests a briefing for a student who already has a stored validated
  briefing, should the workflow always generate fresh or return the existing one? → A: Return
  the existing most-recent validated briefing without invoking the generation seam. Producing a
  new one requires a separate explicit regeneration request, which routes through the full
  generation-and-validation seam sequence.

### Session 2026-09-02 (Product Backlog scope correction)

- Feature-001 was re-scoped to **US-08 only**. The concrete generative provider (US-13), the
  final briefing instructions (US-12), the real acceptance-criteria validation (US-14), the
  concrete one-retry behaviour and the concrete validated-briefing storage (US-15), and the
  advisor-facing dashboard (US-09/10/11) were removed from Feature-001 and reduced to
  integration seams plus minimal interim placeholder behaviour.
- Requirements previously written as "the workflow generates / validates / stores" were
  reframed as "the workflow invokes the corresponding seam and handles its result". The
  observable coordination behaviour is unchanged; what Feature-001 *implements* is narrowed to
  data retrieval, orchestration, and the seams.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coordinate a briefing request end-to-end through the integration seams (Priority: P1)

An academic advisor's request for a Structured Advisor Briefing for one selected student
reaches the backend (via the dashboard, US-11). For a student the model flags as at risk and
who has no existing validated briefing, the backend confirms the precondition, retrieves the
student's attrition-risk result and the 21 approved machine-learning feature values, assembles
the generation context (including instructions obtained from the instructions seam), invokes
the generation seam once, invokes the validation seam on the resulting draft, and — when the
validation seam reports a pass — hands the validated briefing to the persistence seam and
returns it as the successful result. Every step is an interface call; the concrete generation,
validation, and storage are supplied by US-12/13/14/15.

**Why this priority**: This coordination is the core of US-08 — it is what makes "dashboard
actions and the student briefing workflow operate reliably". Without it the downstream stories
have nothing to plug into.

**Independent Test**: With a mock repository, a stub generation seam, a stub validation seam
set to pass, and an in-memory persistence seam, a briefing request assembles a context
containing the risk result and all 21 feature values, calls the seams in the defined order, and
returns a validated briefing that the in-memory seam recorded. Swapping the stubs for
fail/return values exercises every other path without any concrete provider, validator, or
store.

**Acceptance Scenarios**:

1. **Given** a known deidentified student who is flagged at risk, has a stored attrition-risk
   result and available feature values, and has no existing validated briefing, **When** the
   backend receives a briefing request and the generation seam returns a draft that the
   validation seam passes, **Then** the backend hands the validated briefing to the persistence
   seam and returns it as the successful result.
2. **Given** the same request, **When** the backend assembles the generation context, **Then**
   the context contains the student's attrition-risk result and the student's values for all
   21 approved machine-learning model features (not only the reduced proof-of-concept subset).
3. **Given** the same request, **When** the backend determines whether the student is at risk,
   **Then** it uses the machine-learning model's existing at-risk flag and 0.50 probability
   threshold and does not compute a second independent threshold.
4. **Given** a returned validated briefing, **When** its risk figure is inspected, **Then** the
   risk percentage is carried through consistently with the documented model limitations (a
   relative ranking score, not a calibrated probability of attrition).
5. **Given** the assembled generation context, **When** it is inspected, **Then** the 21
   feature values are labelled as background context only and are not marked as causal drivers
   or per-student explanations of the risk result. (Framing of the generated briefing *text* is
   enforced by the US-12 instructions and the US-14 validation, not by Feature-001.)
6. **Given** a known student whose machine-learning at-risk flag is not set, **When** the
   backend receives a briefing request, **Then** it returns an explicit "not flagged at risk"
   result and performs no data assembly, context construction, or seam invocation for
   generation.
7. **Given** a student who already has a stored validated briefing, **When** the backend
   receives a briefing request that is not an explicit regeneration, **Then** it returns the
   existing most-recent validated briefing (read through the persistence seam) and does not
   invoke the generation seam.
8. **Given** a student who already has a stored validated briefing, **When** the backend
   receives an explicit regeneration request and the student is still flagged at risk, **Then**
   it routes the request through the full seam sequence again; on a seam-reported success the
   new validated briefing becomes the most-recent one, and on a terminal failure the previous
   validated briefing is left in place and remains the one returned.

---

### User Story 2 - Expose backend retrieval of a stored validated briefing (Priority: P2)

The backend exposes an operation that returns the most recent stored validated briefing for a
student, read through the persistence seam, without invoking generation. The advisor-facing
display of that briefing is US-10; Feature-001 provides the capability it calls.

**Why this priority**: US-10/US-11 need a backend read path that is independent of generation.
It is a small, separately testable slice.

**Independent Test**: With an in-memory persistence seam holding one validated briefing for a
student, the retrieval operation returns it; for a student with none it returns an explicit
"none available" result; drafts and failed briefings are never returned because only validated
briefings are ever handed to the seam.

**Acceptance Scenarios**:

1. **Given** a student with one stored validated briefing, **When** the retrieval operation is
   called, **Then** the validated briefing is returned.
2. **Given** a student with no stored validated briefing, **When** the retrieval operation is
   called, **Then** an explicit "none available" result is returned.
3. **Given** a student with more than one stored validated briefing, **When** the retrieval
   operation is called, **Then** the most recent validated briefing is returned.
4. **Given** a draft or a briefing that failed validation, **When** any retrieval runs, **Then**
   that content is never returned — the backend only ever hands validated briefings to the
   persistence seam.

---

### User Story 3 - Safe outcome handling when the first attempt does not yield a validated briefing (Priority: P3)

When the generation seam fails before a draft exists, or the validation seam reports a failure,
the backend does not fabricate a success and does not retry. It hands the first-attempt outcome
to the retry seam. When the retry seam concludes without a validated briefing, the backend maps
that to an explicit application-visible error and stores nothing new.

**Why this priority**: This protects the integrity of every briefing an advisor eventually
sees, and it defines the Feature-001 ↔ Feature-002 boundary. Lower priority only because it is
the exceptional path.

**Independent Test**: With the generation seam stubbed to fail, then separately the validation
seam stubbed to fail, the backend invokes the retry seam exactly once and performs no
generation itself; with the retry seam stubbed to conclude without a briefing, the backend
returns an explicit error and the in-memory persistence seam holds no new briefing for that
request.

**Acceptance Scenarios**:

1. **Given** a briefing request in a generation run, **When** the generation seam fails before
   a draft exists, **Then** the backend passes a "generation failed" outcome to the retry seam
   and performs no further generation attempt itself.
2. **Given** a briefing request in a generation run, **When** the validation seam reports a
   failure, **Then** the backend passes that validation outcome to the retry seam.
3. **Given** any first-attempt failure, **When** the backend responds, **Then** no
   deterministic or template briefing is returned or stored as a successful, validated
   Structured Advisor Briefing.
4. **Given** the retry seam concludes without a validated briefing, **When** the backend
   responds, **Then** it returns an explicit, application-visible error and stores no briefing
   as a validated output for that request.

---

### Edge Cases

- **Unknown or malformed student identifier**: the backend returns an explicit
  "not found / unavailable" result and does not assemble a context or invoke any seam.
- **No stored attrition-risk result for the student**: treated as unavailable; the backend
  stops before context assembly and returns an explicit result.
- **Some approved feature values legitimately absent in the synthetic data**: the backend
  proceeds and marks those values unavailable in the generation context; only a missing
  required attrition-risk result stops the request.
- **Risk data source or feature data source temporarily unavailable**: the backend returns an
  explicit error and does not invoke the generation seam on incomplete required data.
- **Generation seam fails or returns empty content on the first attempt**: handled as a
  first-attempt generation failure — the outcome is passed to the retry seam; no template
  substitution, no success reported.
- **Validation seam reports a failure**: the outcome is passed to the retry seam.
- **Interim development state with no final acceptance criteria configured**: the validation
  seam runs its clearly identified interim pass-through behaviour; the orchestration still runs
  and is testable with controlled pass/fail stubs.
- **The persistence seam reports that a validated briefing could not be stored**: the backend
  surfaces an explicit error and does not report the request as successful.
- **A briefing is requested for a known student who is not flagged as at risk**: the backend
  returns an explicit "not flagged at risk" result; no data assembly, context construction, or
  seam invocation for generation occurs.
- **A briefing is requested for a student who already has a validated briefing (no explicit
  regeneration)**: the existing most-recent validated briefing is returned via the persistence
  seam and the generation seam is not invoked.
- **An explicit regeneration is requested for a student who now has no at-risk flag**: the
  regeneration is refused with the "not flagged at risk" result; any previously stored
  validated briefing is left in place and still retrievable.
- **An explicit regeneration ends in terminal failure**: the previous validated briefing is not
  removed or superseded and remains the one returned, alongside the explicit error.
- **A project security, privacy, or platform constraint blocks supplying one or more of the 21
  approved features to the generation seam**: the backend surfaces the conflict for human
  review rather than silently dropping fields.

## Requirements *(mandatory)*

### Functional Requirements

#### Input and data retrieval

- **FR-001**: The backend MUST accept a single selected deidentified student identifier as the
  input that initiates a Structured Advisor Briefing request.
- **FR-002**: The backend MUST retrieve the student's current attrition-risk result — risk
  percentage on a 0–100 scale, at-risk flag, prediction threshold, model run identifier, and
  scored-at timestamp — from the machine-learning model's prediction Delta table, matched by
  the deidentified student identifier.
- **FR-003**: The backend MUST retrieve the student's values for all 21 approved
  machine-learning model features from the governed synthetic-data Delta tables, matched by the
  deidentified student identifier, rather than a reduced subset of them.
- **FR-004**: The backend MUST treat the prediction Delta table and the synthetic-data feature
  tables as read-only inputs and MUST NOT modify them or any other machine-learning or
  synthetic-data implementation.
- **FR-005**: The backend MUST use the machine-learning model's existing at-risk flag as the
  authoritative at-risk determination — a model probability of 0.50 or above (equivalently 50%
  or above on the 0–100 scale) is "at risk", below 0.50 is "not at risk" — and MUST NOT
  calculate a separate, independent application threshold. This applies both to a single-student
  request and to any backend retrieval of the set of at-risk students.
- **FR-006**: The backend MUST carry the risk percentage through consistently with the
  documented machine-learning model limitations (a relative ranking score, not a calibrated
  probability) and MUST NOT present or persist it as a calibrated probability of attrition.
- **FR-007**: Where one or more of the 21 approved feature values are legitimately absent for a
  student, the backend MUST proceed and mark those values unavailable in the generation
  context; only a missing required attrition-risk result MUST stop the request before context
  assembly.
- **FR-008**: The backend MUST assemble the full approved 21-feature set into every generation
  context — using `UNAVAILABLE` markers only for values genuinely absent from the source data —
  and MUST NOT silently exclude, filter, or reduce the approved features. If a configured
  constraint signals that an approved feature must not be supplied to the generation seam, the
  backend MUST surface that conflict for human review rather than dropping the field. The
  concrete source of such a constraint (for example an external-egress or data-sharing
  restriction) arrives with the US-13 generation seam; Feature-001 owns the non-reduction
  guarantee and the surfacing path.

#### Request preconditions and existing-briefing handling

- **FR-034**: A briefing request MAY be routed to generation only for a student whose
  machine-learning at-risk flag is set (model probability of 0.50 or above). A request for a
  known student whose at-risk flag is not set MUST return an explicit "not flagged at risk"
  result and MUST NOT assemble a context, invoke the generation seam, or invoke the retry seam.
- **FR-035**: When a validated briefing already exists for the student, a briefing request that
  is not an explicit regeneration MUST return the existing most-recent validated briefing (read
  through the persistence seam) and MUST NOT assemble a context or invoke the generation seam.
- **FR-036**: The backend MUST provide an explicit regeneration request that routes through the
  full generation-and-validation seam sequence for a student even when a validated briefing
  already exists. The at-risk precondition in FR-034 applies equally to a regeneration request.
- **FR-037**: When a regeneration ends in terminal failure, the backend MUST NOT ask the
  persistence seam to remove or replace the student's existing most-recent validated briefing;
  that briefing remains the one returned, alongside the explicit error. When a regeneration
  succeeds, the backend MUST hand the new validated briefing to the persistence seam as the new
  most-recent one.

#### Context assembly and the generation seam

- **FR-009**: The backend MUST assemble the generation context by combining the deidentified
  student identifier, the attrition-risk result, the 21 approved feature values, and the
  briefing instructions obtained from the instructions seam.
- **FR-010**: The backend MUST obtain briefing instructions through a replaceable instructions
  seam. In the interim it MAY use a minimal placeholder that reuses the existing safe
  proof-of-concept briefing instructions; it MUST NOT define the final instruction content,
  sections, or language guidance (owned by US-12). Adopting the final instructions later MUST
  NOT require changing the orchestration.
- **FR-011**: The generation context the backend assembles and passes to the generation seam
  MUST label the 21 feature values as background context only and MUST NOT mark any feature as a
  causal driver or a per-student explanation of the risk result. The framing of the generated
  briefing *text* is enforced by the US-12 instructions and the US-14 validation, not by
  Feature-001.
- **FR-013**: The backend MUST invoke the generation seam exactly once per generation or
  regeneration run and MUST NOT itself perform any additional generation attempt.
- **FR-014**: The generation seam MUST be a replaceable interface. Feature-001 MUST invoke it
  and handle both its success result (a draft) and its failure result (an error before a draft
  exists), and MUST NOT implement the concrete generative integration or select a specific
  provider — that is owned by US-13. Any interim placeholder generation seam MUST be clearly
  identified as non-final and MUST NOT be presented as a produced Structured Advisor Briefing.

#### The validation seam

- **FR-015**: When the generation seam returns a draft, the backend MUST invoke the validation
  seam on that draft and MUST make its outcome available to the rest of the orchestration.
- **FR-016**: The validation seam MUST be a replaceable interface that can run before the final
  acceptance criteria exist. Feature-001's interim behaviour MUST be a clearly identified
  pass-through that invents no acceptance criteria and MUST NOT be presented as the final
  Structured Advisor Briefing validation (owned by US-14). Supplying or extending the criteria
  later MUST NOT require changing the orchestration.
- **FR-017**: The backend's end-to-end orchestration MUST be exercisable using
  controlled/stubbed validation-seam outcomes (pass or fail) regardless of whether the final
  acceptance criteria are available.

#### Outcome handling and application response

- **FR-018**: When the validation seam reports a pass, the backend MUST hand the validated
  briefing to the persistence seam and MUST return it as the successful result. The concrete
  storage behaviour is owned by US-15.
- **FR-019**: When the generation seam fails before a draft exists, or the validation seam
  reports a failure, the backend MUST pass the first-attempt outcome to the retry seam and MUST
  NOT perform any retry itself.
- **FR-020**: The backend MUST NOT substitute a deterministic or template briefing for a failed
  generation or a failed validation, and MUST NOT report or store any such substitute as a
  successful, validated Structured Advisor Briefing.
- **FR-021**: When the retry seam concludes without a validated briefing, the backend MUST
  return an explicit, application-visible error and MUST NOT hand any briefing to the
  persistence seam as a validated output for that request.
- **FR-022**: The backend MUST produce an application-visible result for every terminal outcome
  — a validated briefing or an explicit error. No request may end with no result surfaced.
- **FR-023**: For a request with an unknown or malformed student identifier, or with no stored
  attrition-risk result for the student, the backend MUST return an explicit
  "not found / unavailable" result and MUST NOT assemble a context or invoke the generation
  seam.
- **FR-024**: When the persistence seam reports that a validated briefing could not be stored,
  the backend MUST surface an explicit error and MUST NOT report the request as successful.

#### Persistence and retrieval seams

- **FR-025**: The backend MUST hand only briefings that the validation seam has passed to the
  persistence seam, and MUST NOT hand it drafts or failed briefings. The concrete governed
  Databricks Unity Catalog Volume storage behaviour is owned by US-15; Feature-001 defines the
  persistence-seam interface and provides an in-memory implementation for its own tests.
- **FR-026**: The backend MUST NOT retain failed or draft briefing content beyond the request
  that produced it, and MUST NOT expose it through any retrieval path.
- **FR-028**: The backend MUST expose an operation that returns the most recent stored
  validated briefing for a student, read through the persistence seam, without invoking
  generation. The advisor-facing display of that briefing is owned by US-10.
- **FR-029**: Only validated briefings MUST be returned through the retrieval operation; drafts
  and failed briefings MUST never be returned.
- **FR-030**: When the persistence seam reports no validated briefing for a student, the
  retrieval operation MUST return an explicit "none available" result. When more than one
  validated briefing exists, the persistence-seam contract MUST return the most recent, and the
  backend MUST surface that one.

#### Logging and privacy

- **FR-031**: Full generation prompts and full generated or briefing text MUST NOT be written
  to general application logs. Validated briefing content MUST leave the backend only through
  the persistence seam and the retrieval operation.
- **FR-032**: Only the minimal workflow and error metadata necessary for operation, testing,
  traceability, or safe troubleshooting MUST be retained. Credentials, API keys, tokens, and
  other secrets MUST NOT be logged.

#### Orchestration and boundary

- **FR-033**: The backend MUST coordinate the end-to-end sequence — input, the at-risk
  precondition check (FR-034), the existing-validated-briefing check (FR-035), data retrieval,
  context assembly, one generation-seam invocation, one validation-seam invocation, and
  success-path persistence and response — and MUST hand off to the retry seam only at the
  single defined first-attempt failure point (reached only within a generation or regeneration
  run), without duplicating any retry logic.
- **FR-038**: The backend MUST expose its capabilities through the existing application's
  service layer and its REST and MCP interfaces, so that the advisor-facing stories (US-10,
  US-11) call the backend rather than the Delta tables or the seams directly.
- **FR-039**: Feature-001 MUST define the generation, instructions, validation, retry, and
  persistence seams such that US-12, US-13, US-14, and US-15 can supply their concrete
  implementations without changing the Feature-001 orchestration, and MUST NOT pre-implement
  those stories' behaviour.

### Key Entities *(include if feature involves data)*

- **Student Attrition-Risk Result**: the model's current output for one deidentified student —
  risk percentage (0–100), at-risk flag, prediction threshold, model run identifier, scored-at
  timestamp. One current result per student. Read-only input from the prediction Delta table.
- **Approved Model Feature Set**: the 21 model feature values for one deidentified student, from
  the governed synthetic-data Delta tables. Includes some sensitive / demographic attributes.
  Carried as background context only, never as a per-student causal explanation. Read-only
  input.
- **Briefing Generation Context**: the object the backend assembles and passes to the
  generation seam — the deidentified identifier, the attrition-risk result, the 21 feature
  values, and the instructions obtained from the instructions seam.
- **Validation Outcome**: the result the validation seam returns — at minimum a pass/fail
  signal, and, when available, failed-criteria identifiers and feedback for the retry seam to
  consume. Feature-001 defines the shape; US-14 populates it meaningfully.
- **First-Attempt Outcome**: what the backend hands to the retry seam — either "generation
  failed before a draft" or "validation failed" (carrying the Validation Outcome).
- **Validated Structured Advisor Briefing**: a briefing the validation seam has passed. The
  only briefing form the backend returns or hands to the persistence seam. A student has one
  most-recent validated briefing at a time; a successful explicit regeneration produces a newer
  one. The concrete stored form (location, format, retention) is owned by US-15.
- **Draft Briefing**: a briefing returned by the generation seam that has not passed
  validation. Transient. Never handed to the persistence seam, never returned by retrieval.
- **Workflow Metadata**: the minimal per-request metadata the backend records for logging and
  for the object handed to the persistence seam (deidentified identifier, timestamps, attempt
  count, outcome category, validator identifier). Feature-001 defines these fields; whether and
  how they are persisted alongside a stored briefing is owned by US-15.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a known synthetic student, 100% of generation runs assemble the context from
  the current attrition-risk result plus all 21 approved feature values; 0% of requests reach
  the generation seam without a required attrition-risk result.
- **SC-002**: 100% of briefings the backend returns or hands to the persistence seam have a
  passing validation-seam outcome; 0 drafts or failed briefings are returned by any path.
- **SC-003**: 0 occurrences of a deterministic or template briefing being returned or persisted
  as a successful, validated Structured Advisor Briefing.
- **SC-004**: 100% of briefing requests reach an application-visible terminal outcome — a
  validated briefing or an explicit error; 0 requests end with no result surfaced.
- **SC-005**: 0 full generation prompts and 0 full briefing texts appear in general application
  logs; 0 credentials, keys, or tokens appear in logs.
- **SC-006**: Requests that do not run generation — not-found, not-flagged-at-risk, and
  return-existing — complete in under 1 second in the backend orchestration (excluding any
  downstream seam latency), measured against the mock repository and in-memory persistence
  seam.
- **SC-007**: The final instructions (US-12) and the final acceptance criteria (US-14) can be
  adopted by swapping the instructions-seam and validation-seam implementations with no change
  to the backend orchestration — verified by substituting them and re-running the same
  acceptance scenarios.
- **SC-008**: 100% of validated briefings are handed to the persistence seam; 100% of
  persistence-seam failures are surfaced as explicit errors and 0 are reported as success.
- **SC-009**: 100% of first-attempt failures (generation-seam failure or validation-seam
  failure) result in the first-attempt outcome being passed to the retry seam, with 0 retries
  performed by the backend orchestration itself.
- **SC-010**: 0 requests for students whose at-risk flag is not set reach the generation seam;
  100% of such requests return an explicit "not flagged at risk" result.
- **SC-011**: When a validated briefing already exists and the request is not an explicit
  regeneration, 100% of such requests return the existing briefing with 0 generation-seam
  invocations.
- **SC-012**: The generation, instructions, validation, retry, and persistence seams each have
  a defined interface and at least one Feature-001-supplied placeholder or in-memory
  implementation, and the full orchestration passes its acceptance scenarios with those
  placeholders and no concrete provider, validator, or Volume store.

## Assumptions

- Feature-001 extends the existing Databricks application rather than creating a parallel
  backend, reusing the established data-retrieval, interface, and error-handling patterns
  already present in the codebase (per constitution principles on reuse and minimal change).
  The existing proof-of-concept application is the base being extended.
- The machine-learning prediction data and the governed synthetic-data feature tables are
  available, are keyed by the deidentified student identifier, and are strictly read-only
  inputs owned by other team components.
- The "21 approved machine-learning model features" are those recorded as approved in the
  machine-learning model documentation. Retrieving all of them is a deliberate extension of the
  narrower proof-of-concept snapshot subset.
- "Selected student information" for a deidentified student consists of the deidentified
  identifier, the attrition-risk result, and the 21 feature values. No personally identifiable
  information exists in the data or is retrieved.
- Being flagged at risk by the model is a hard precondition for routing a request to generation
  (see Clarifications 2026-09-02 and FR-034). Briefing requests are expected to originate from
  the dashboard's at-risk list (US-11); a request for a known but non-flagged student is
  refused rather than routed.
- A briefing request for a student who already has a validated briefing returns that existing
  briefing without invoking the generation seam; a new briefing is produced only through an
  explicit regeneration request (see Clarifications 2026-09-02 and FR-035, FR-036).
- Where some of the 21 feature values are legitimately absent in the synthetic data, the
  backend proceeds and marks them unavailable; only a missing required attrition-risk result
  halts the request before context assembly.
- The most recent validated briefing for a student is the one surfaced on retrieval and on a
  non-regeneration request; the persistence-seam contract is responsible for "most recent", and
  US-15 implements it.
- Timing model (synchronous versus asynchronous), exact interface routes and methods,
  pagination details, seam signatures, and internal module structure are determined during
  `/speckit-plan` by inspecting and extending the existing architecture. A technical choice that
  would materially change user-visible behaviour or feature scope is flagged for human approval
  rather than decided silently.
- The concrete generative integration (US-13), the final briefing instructions and
  acceptance-criteria content (US-12), the real validation behaviour (US-14), the concrete
  one-retry behaviour and the concrete validated-briefing storage (US-15), the advisor-facing
  dashboard (US-09/10/11), and final end-to-end integration (US-16) are delivered by their own
  Product Backlog stories. Feature-001 provides the seams and minimal interim placeholders they
  attach to and must not pre-implement them.

## Dependencies

- The machine-learning model's prediction Delta table (risk percentage, at-risk flag, 0.50
  threshold, model run identifier, scored-at timestamp), keyed by the deidentified student
  identifier — read-only input.
- The governed synthetic-data Delta tables holding the 21 approved model feature values, keyed
  by the deidentified student identifier — read-only input.
- **US-12** — the final Default Structured Briefing Prompt, instructions, sections, language
  guidance, and acceptance-criteria content; consumed later through the instructions and
  validation seams.
- **US-13** — the concrete Generative AI / OpenAI API implementation; supplied later through the
  generation seam.
- **US-14** — the real acceptance-criteria validation behaviour; supplied later through the
  validation seam.
- **US-15** — the concrete one-retry behaviour and the concrete governed validated-briefing
  storage; supplied later through the retry and persistence seams. The retry portion is
  Feature-002.
- **Feature-002** — the exceptional single-retry workflow, invoked through the retry seam when
  the first attempt does not yield a validated briefing.
- The existing Databricks application environment and its security, secret-management, and
  Unity Catalog governance mechanisms.

## Out of Scope

- The concrete generative / OpenAI API integration and any provider selection or credential
  handling for it — **US-13**.
- The final briefing prompt, instructions, sections, language guidance, and acceptance-criteria
  content — **US-12**.
- The real Structured Advisor Briefing acceptance-criteria validation behaviour — **US-14**.
- The concrete one-retry behaviour and the concrete governed Unity Catalog Volume storage of
  validated briefings (path, format, naming, retention, most-recent selection) — **US-15**; the
  retry behaviour is **Feature-002**.
- The advisor-facing dashboard / frontend, the at-risk student display, and the
  student-selection and briefing-request interaction — **US-09, US-10, US-11**. Feature-001
  changes the shared Streamlit screen only as far as needed to keep it working against the
  changed service; its advisor-facing behaviour is those stories' concern.
- Final end-to-end integration of the ML, application, generative, validation, retry, and
  storage components — **US-16**.
- Broad application / dashboard testing and complete briefing-workflow testing — **US-17,
  US-18**. Feature-001 carries only proportionate tests of its own orchestration and seams.
- Later refinement, defect resolution, final delivery, documentation, and handover — **US-19
  through US-23**.
- Separate solution-design, synthetic-data validation, and UI/UX design work — **US-24, US-25,
  US-26**.
- Changes to the machine-learning model, the synthetic-data generation process, or any other
  team-owned notebooks or components.
- Automated intervention decisions or any automated contact with students.
- Model promotion governance, retraining, drift monitoring, or scheduled deployment.
