# Feature Specification: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Feature Branch**: `feat/feature-003-briefing-workflow-testing`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Create the Feature-003 specification for US-18: Structured Advisor Briefing Workflow Testing using the project constitution v1.1.0, the approved Product Backlog US-18 user story, the confirmed Feature-003 repository investigation and scope decisions, and the merged Feature-001 (US-08) and Feature-002 (US-15) artifacts and source as implementation context only. Feature-003 is a test-architecture story only; it adds no production component. Define WHAT Feature-003 must verify — observable testing behaviour, acceptance criteria, boundaries, dependencies, failure behaviour and traceability — without inventing Structured Advisor Briefing acceptance criteria, duplicating behaviour already verified by Feature-001 or Feature-002, or promoting test filenames, fixture classes or harness structure into the specification."

## Overview

Feature-003 is **Product Backlog US-18 — Structured Advisor Briefing Workflow Testing**, and it
completes that story in full. The approved story states:

> As a Digital Business Solutions Team, I want to have the briefing generation, validation, retry
> and storage workflow tested, so that the solution handles both successful and failed briefing
> outcomes correctly.
>
> **Acceptance Criteria**: Given the complete Structured Advisor Briefing workflow and its test
> cases are available, when the workflow tests are executed, then generation, validation, retry,
> error handling and valid-briefing storage behave according to the approved design.

Feature-003 establishes verified, traceable confidence that the Structured Advisor Briefing
workflow behaves as specified across every outcome an advisor request can reach. The story's
phrase "according to the approved design" is load-bearing: where the delivered implementation
differs from an approved specification, the specification governs and the difference is recorded
as a defect rather than accepted as the expected behaviour.

Feature-003 is a **test-architecture feature only**. It introduces no new application capability
and changes no application behaviour. The briefing generation, validation, retry, error-handling
and validated-storage architecture is already delivered and merged by Feature-001 (US-08) and
Feature-002 (US-15). Feature-003 verifies that delivered architecture; it does not extend it.

Feature-003 delivers four things:

- **Complete outcome coverage.** Every outcome the briefing workflow can reach — a validated
  briefing on the first attempt, a validated briefing after the single retry, each terminal
  failure, each refusal, and each retrieval path — is verified against the behaviour the
  approved Feature-001 and Feature-002 specifications require.
- **Verification of workflow properties that outcome testing alone cannot show.** The order in
  which the workflow engages its boundaries, the propagation of validation feedback into the
  retry request, the number of times a validated briefing is written, and the absence of
  briefing content from operational records.
- **Consistency across the boundaries advisors and tools reach the workflow through.** Workflow
  outcomes are confirmed to surface coherently at the application-service, REST and
  tool-interface boundaries — by tracking the verification Feature-001 already provides as
  re-verification, and adding new verification only where a boundary's observable result differs
  and is not already covered.
- **Traceability, including honest recording of gaps.** Each verified scenario is traceable to
  the requirement, success criterion or backlog story it satisfies, and criteria that remain
  unverified are recorded with the reason rather than left silently unresolved.

Feature-003 **consumes and does not redefine** anything. It defines no Structured Advisor
Briefing acceptance criteria (US-14), no briefing prompt content (US-12), and no generative
integration behaviour (US-13). Where the workflow's behaviour depends on those unfinished
stories, Feature-003 supplies controlled outcomes at the established boundaries so that the
workflow's own behaviour can be verified without them.

## Backlog Alignment

| Backlog story | Owns | Feature-003's relationship |
|---|---|---|
| US-08 | Application backend: risk-data retrieval + briefing-request coordination | Delivered by Feature-001 (merged). Feature-003 verifies its orchestration and closes a criterion its own tasks left unverified. |
| US-12 | Final briefing prompt, instructions, sections, language guidance | Feature-003 asserts nothing about prompt content. |
| US-13 | Concrete Generative AI implementation that generates a draft | Feature-003 supplies controlled generation outcomes at this boundary; it does not implement or verify the integration. |
| US-14 | Actual acceptance-criteria validation behaviour and Validation Feedback content | Feature-003 supplies controlled validation outcomes at this boundary; it defines and asserts no criteria. |
| US-15 | Concrete single-retry behaviour and governed validated-briefing storage | Delivered by Feature-002 (merged). Feature-003 verifies workflow properties its tests did not assert, and re-verifies nothing they already cover. |
| US-16 | Final end-to-end integration of all components | Feature-003 must be compatible with it but must not expand scope to complete it. |
| US-17 | Broad application and advisor-facing dashboard testing | Not in Feature-003. All advisor-facing presentation is out of scope. |
| **US-18** | Complete Structured Advisor Briefing workflow testing | **This feature** |
| US-19 – US-23 | Later refinement, defect resolution, final delivery, documentation, handover | Feature-003 records the defects it surfaces; it resolves none of them. |

## Clarifications

### Session 2026-09-16 (confirmed Feature-003 scope decisions)

The following decisions were settled with the product owner from the Feature-003 repository
investigation and are authoritative for this specification.

- Feature-003's scope is the Structured Advisor Briefing workflow only — generation, validation,
  retry, error handling and validated storage — across the application-service, REST and
  tool-interface boundaries. The non-briefing service surface (health reporting, the high-risk
  student list, and student-profile retrieval) is out of scope.
- Feature-003 is purely additive. It changes no production source file, changes no Feature-001 or
  Feature-002 verification artifact, and adds no coverage that duplicates behaviour those suites
  already verify adequately. Behaviour those suites already verify accurately is treated as
  **complete**, not as a gap to re-cover, even where it falls inside Feature-003's subject area.
- Controlled generation and validation outcomes are the approved verification approach, not a
  workaround. Feature-001 SC-012 and Feature-002 SC-011 both certify that the workflow's
  scenarios pass with controlled outcomes and no US-13 or US-14 implementation present.
- Feature-003 invents no Structured Advisor Briefing acceptance criteria. Any acceptance-criteria
  value a controlled outcome requires must be visibly synthetic so it can never be mistaken for
  approved US-14 content.
- Feature-002 specifies that briefing content with no substance produced on the retry attempt is
  treated as a generation failure. The delivered implementation does not enforce this: such a
  briefing is currently returned as validated and stored. Feature-003 records the **specified**
  behaviour as a single expected-fail verification and raises the mismatch as a defect. It does
  not change the implementation.
- Feature-001 SC-006 (non-generation requests completing within the stated time budget) was never
  verified by any Feature-001 task or test. Feature-003 closes it.
- Feature-001 SC-007 (adopting the final instructions and acceptance criteria by substituting the
  corresponding boundaries, verified by re-running the same scenarios) is **out of scope**. The
  US-12 and US-14 work is expected to be delivered outside that boundary, so the substitution the
  criterion describes is not anticipated during Feature-003. The deferral is recorded with its
  reason so the criterion is not left silently unresolved, and it can be closed later if a real
  implementation is substituted at that boundary.
- Concurrent briefing requests for the same student are out of scope. Feature-002 explicitly
  declares this behaviour not specially handled.
- Advisor-facing presentation is out of scope and belongs to US-17.

### Session 2026-09-16 (US-18 story text supplied; scope resolutions)

The approved Product Backlog US-18 story text was supplied after the initial draft and is quoted
in the Overview. It confirms the derived scope rather than changing it: the story names
generation, validation, retry, error handling and valid-briefing storage, which are precisely the
areas this specification covers. Two open questions were resolved with the product owner.

- Q: Does the approved US-18 story require a broader or narrower scope than this specification's
  four user stories? → A: Neither. User Stories 1 through 4 are within scope and encompass
  precisely what is required to complete Feature-003 for US-18.
- Q: How much cross-boundary repetition does US-18 require, given Feature-001 already verifies
  briefing outcomes at the REST and tool-interface boundaries? → A: Repeated verification MUST
  NOT be re-implemented; doing so would add weight to the overall design for no additional
  assurance. Instead, Feature-001's existing cross-boundary verification of briefing outcomes is
  **tracked within Feature-003 as re-verification**, inclusive of the boundaries whose observable
  results differ. New verification is added only where an outcome's observable result differs
  between boundaries and is not already covered.

### Session 2026-09-16 (clarification pass)

- Q: Where should Feature-003 record the defects it discovers, such as the blank-content
  mismatch? → A: In both the expected-fail verification's own annotation, which is the source of
  truth and cannot drift from the verification it describes, and the traceability record, which
  aggregates recorded defects so a reviewer sees all findings in one place. This choice was made
  after confirming that Feature-001's traceability table cites five verification names that no
  longer exist, demonstrating that a prose-only record of verification-linked facts goes stale
  unnoticed in this repository.
- Q: Should Feature-003's traceability record be required to stay accurate automatically, or is a
  hand-maintained document acceptable? → A: A hand-maintained document, accompanied by a
  verification that confirms every verification name the record cites still resolves. This makes
  the existing traceability requirement testable rather than adding new capability, and closes
  the drift that left Feature-001's traceability table pointing at renamed verifications.

### Session 2026-09-16 (second clarification pass)

- Q: When the workflow is exercised against governed storage instead of the default store, which
  outcomes must be re-run? → A: The six storage-decision outcomes described in User Story 3 only.
  Outcomes that neither read nor write storage are not re-run against governed storage, because
  they cannot vary by store and doing so would add verification beyond what the approved criteria
  require. This resolves an inconsistency between User Story 3's seventh scenario, which scoped
  the re-run to that story's own outcomes, and FR-031, which had described it without
  qualification.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm every briefing outcome behaves as specified (Priority: P1)

A reviewer needs assurance that every outcome a briefing request can reach — success, refusal,
each kind of failure, and each retrieval path — produces exactly the result the approved
specifications require, and that no request can end without a result.

**Why this priority**: This is the core of US-18 and the minimum that makes the story valuable.
Without it there is no evidence that the delivered briefing workflow behaves as specified. It
stands alone: complete outcome coverage is useful even if nothing else in Feature-003 is built.

**Independent Test**: With controlled generation and validation outcomes driving each case, every
outcome named in the requirements is exercised and confirmed to produce the specified result,
with no access to any external service.

**Acceptance Scenarios**:

1. **Given** a student the model flags at risk with no stored briefing, **When** a briefing is
   requested and generation and validation both succeed, **Then** a validated briefing is
   returned recording that it passed validation and was produced on the first attempt.
2. **Given** a student the model does not flag at risk, **When** a briefing is requested, **Then**
   an explicit refusal is returned and no generation is attempted.
3. **Given** an unknown student, **When** a briefing is requested, **Then** an explicit not-found
   result is returned and no generation is attempted.
4. **Given** a student with a stored validated briefing, **When** a briefing is requested without
   explicitly asking for a fresh one, **Then** the stored briefing is returned and no generation
   is attempted.
5. **Given** a student with a stored validated briefing, **When** a fresh briefing is explicitly
   requested and succeeds, **Then** the new briefing is returned and becomes the one retrieval
   surfaces.
6. **Given** generation is not configured, **When** a briefing is requested, **Then** the
   configuration failure is surfaced unchanged, no retry is attempted, and no substitute briefing
   of any kind is returned.
7. **Given** any briefing request, **When** the request completes by any path, **Then** exactly
   one explicit outcome is surfaced — a validated briefing or an explicit failure — and never an
   absent or ambiguous result.

---

### User Story 2 - Confirm the exceptional retry path is correct and bounded (Priority: P2)

A reviewer needs assurance that the single-retry path engages the workflow's boundaries in the
correct order, carries the validation feedback it is required to carry, and can never exceed one
additional attempt.

**Why this priority**: The retry path is the workflow's most intricate behaviour and the one where
an ordering or propagation defect would be least visible from outcomes alone. It is independently
valuable and independently testable once controlled outcomes exist.

**Independent Test**: With controlled outcomes scripted to fail then succeed, and separately to
fail twice, the boundary engagement order, the content carried into the second request, and the
total number of attempts are each confirmed directly.

**Acceptance Scenarios**:

1. **Given** a first attempt whose briefing fails validation, **When** the retry produces a
   briefing that passes validation, **Then** a validated briefing recording a second attempt is
   returned.
2. **Given** a first attempt that fails to produce a briefing for a retryable reason, **When** the
   retry produces a briefing that passes validation, **Then** a validated briefing recording a
   second attempt is returned.
3. **Given** a validation failure that reported failed acceptance criteria and feedback, **When**
   the retry request is constructed, **Then** exactly that reported content is carried into the
   retry request and nothing is added or invented.
4. **Given** a validation failure that reported neither failed criteria nor feedback, **When** the
   retry request is constructed, **Then** the retry request is unchanged from the original.
5. **Given** any briefing request, **When** the workflow runs to completion by any path, **Then**
   the workflow's boundaries are engaged in the specified order, and generation is attempted at
   most twice.
6. **Given** both attempts fail, **When** the request completes, **Then** no third attempt is made
   and an explicit terminal failure identifying the last failure kind is surfaced.
7. **Given** a configuration failure arising during the retry attempt, **When** the request
   completes, **Then** it is surfaced unchanged rather than reported as a terminal failure.

---

### User Story 3 - Confirm validated briefings are stored only when they should be (Priority: P3)

A reviewer needs assurance that a briefing is written to storage exactly when the specification
requires it, never when it does not, and that a failure never destroys a student's existing
validated briefing.

**Why this priority**: Storage is where an error becomes durable and advisor-visible. It is
independently testable and valuable on its own.

**Independent Test**: Each outcome from the preceding stories is run while observing how many
times a validated briefing is written, confirming the count matches the specification for that
outcome.

**Acceptance Scenarios**:

1. **Given** a briefing that passes validation on either attempt, **When** the request completes,
   **Then** it is written to storage exactly once.
2. **Given** any terminal failure, refusal, not-found result, or configuration failure, **When**
   the request completes, **Then** nothing is written to storage.
3. **Given** a request that returns an existing stored briefing, **When** the request completes,
   **Then** nothing is written to storage.
4. **Given** a student with a stored validated briefing, **When** a fresh request fails at any
   point, **Then** the previously stored briefing remains the one retrieval surfaces.
5. **Given** storage reports that a validated briefing could not be written, **When** the request
   completes, **Then** an explicit storage failure is surfaced, the request is not reported
   successful, and any previously stored briefing is intact.
6. **Given** a briefing that has not passed validation, **When** any workflow path completes,
   **Then** it is never stored and never surfaced as a validated briefing.
7. **Given** the workflow running against governed storage rather than the default store, **When**
   the outcomes above are exercised, **Then** each behaves identically.

---

### User Story 4 - Make verification traceable and record what remains unverified (Priority: P4)

A reviewer needs to see which requirement or criterion each verified scenario satisfies, and to
see an honest record of any approved criterion that remains unverified together with the reason.

**Why this priority**: It converts the preceding stories from a body of tests into reviewable
evidence, and it prevents approved criteria from being silently orphaned as happened in
Feature-001. It is valuable only once there is verification to trace, so it comes last.

**Independent Test**: The traceability record is inspected and each verified scenario is confirmed
to name what it satisfies, with every unverified criterion in scope carrying a recorded reason.

**Acceptance Scenarios**:

1. **Given** the completed verification work, **When** the traceability record is reviewed,
   **Then** each verified scenario names the requirement, success criterion or backlog story it
   satisfies.
2. **Given** an approved criterion in scope that Feature-003 does not verify, **When** the record
   is reviewed, **Then** the criterion is listed with the reason it was not verified.
3. **Given** briefing content with no substance, **When** the specified behaviour is verified,
   **Then** the verification records the specified behaviour, is marked as expected to fail
   against the current implementation, and is registered as a defect rather than corrected.
4. **Given** requests that do not invoke generation, **When** the stated time budget is verified,
   **Then** they are confirmed to complete within it under the approved measurement conditions.

---

### Edge Cases

- **A verified behaviour conflicts with the delivered implementation**: the approved specified
  behaviour is preserved and the implementation mismatch is recorded as a defect. The requirement
  is never rewritten to match the code.
- **Behaviour already verified adequately by Feature-001 or Feature-002**: treated as complete.
  Feature-003 adds no second verification of it.
- **An outcome is observable at more than one boundary**: it is verified where its observable
  result is distinct, rather than repeated identically at every boundary.
- **A controlled outcome would require an acceptance-criteria value**: a visibly synthetic value is
  used. No plausible-looking criterion text is introduced.
- **The recorded expected-fail verification begins passing**: the underlying defect has been
  resolved elsewhere; the record is updated and the expectation removed.
- **Governed storage is unreachable while reading**: verified as an explicit failure, distinct from
  the result meaning no briefing is available.
- **A workflow outcome exists that no approved requirement describes**: recorded as an unspecified
  behaviour for clarification, not verified against an invented expectation.

## Requirements *(mandatory)*

### Functional Requirements

#### Scope and non-duplication

- **FR-001**: Feature-003 MUST verify the Structured Advisor Briefing workflow only — generation,
  validation, retry, error handling and validated storage.
- **FR-002**: Feature-003 MUST NOT verify the non-briefing service surface, including health
  reporting, the high-risk student list, and student-profile retrieval.
- **FR-003**: Feature-003 MUST NOT change any production source file.
- **FR-004**: Feature-003 MUST NOT change any Feature-001 or Feature-002 verification artifact.
- **FR-005**: Feature-003 MUST NOT duplicate behaviour already verified adequately by Feature-001
  or Feature-002; such behaviour MUST be treated as already satisfied.
- **FR-006**: Feature-003 MUST reuse the established verification conventions and controlled
  outcome mechanisms already present in the project rather than introducing parallel equivalents.

#### Controlled outcomes

- **FR-007**: Feature-003 MUST drive every scenario using controlled generation and validation
  outcomes, with no access to any external service, workspace or network.
- **FR-008**: Controlled outcomes MUST be able to represent, at the generation boundary, a produced
  briefing, a retryable failure, and a configuration failure.
- **FR-009**: Controlled outcomes MUST be able to represent, at the validation boundary, a pass and
  a failure, with and without reported failed criteria and feedback.
- **FR-010**: Feature-003 MUST NOT define, assert, or imply any Structured Advisor Briefing
  acceptance criterion. Any acceptance-criteria value required by a controlled outcome MUST be
  visibly synthetic.
- **FR-011**: Feature-003 MUST NOT assert anything about the content of the briefing prompt.

#### Outcome coverage

- **FR-012**: Feature-003 MUST verify a validated briefing produced and stored on the first
  attempt.
- **FR-013**: Feature-003 MUST verify a validation failure followed by a successful retry.
- **FR-014**: Feature-003 MUST verify a terminal failure in which no briefing could be produced.
- **FR-015**: Feature-003 MUST verify a terminal failure in which a briefing was produced but never
  passed validation.
- **FR-016**: Feature-003 MUST verify a configuration failure, including that it is surfaced
  unchanged and never triggers a retry.
- **FR-017**: Feature-003 MUST verify a storage failure.
- **FR-018**: Feature-003 MUST verify the refusal returned for a student the model does not flag at
  risk, including that generation is not attempted.
- **FR-019**: Feature-003 MUST verify the result returned for an unknown student, including that
  generation is not attempted.
- **FR-020**: Feature-003 MUST verify that an existing validated briefing is returned without
  generation when a fresh briefing is not explicitly requested.
- **FR-021**: Feature-003 MUST verify explicit regeneration, both when it succeeds and when it
  fails.
- **FR-022**: Feature-003 MUST verify that every briefing request reaches exactly one explicit
  outcome.

#### Workflow properties beyond outcomes

- **FR-023**: Feature-003 MUST verify the order in which the workflow engages its boundaries, not
  only how many times each is engaged.
- **FR-024**: Feature-003 MUST verify that the failed acceptance criteria and feedback a validation
  failure reported are carried into the retry request exactly as reported.
- **FR-025**: Feature-003 MUST verify that when a validation failure reported neither failed
  criteria nor feedback, the retry request is unchanged and nothing is fabricated.
- **FR-026**: Feature-003 MUST verify that generation is attempted at most twice for any single
  request.
- **FR-027**: Feature-003 MUST verify that the retry path does not itself store a briefing, and that
  a briefing produced by retry is stored exactly once.

#### Storage decisions

- **FR-028**: Feature-003 MUST verify, for every outcome in FR-012 through FR-021, how many times a
  validated briefing is written, and that the count matches the specified behaviour.
- **FR-029**: Feature-003 MUST verify that no briefing which has not passed validation is stored or
  surfaced as validated.
- **FR-030**: Feature-003 MUST verify that a previously stored validated briefing survives every
  failing outcome.
- **FR-031**: Feature-003 MUST verify that the storage-decision outcomes described in User Story 3
  behave identically when the workflow runs against governed storage rather than the default
  store, using controlled storage infrastructure. Outcomes that neither read nor write storage
  MUST NOT be re-run against governed storage, because they cannot vary by store and re-running
  them would add verification beyond what the approved criteria require.

#### Boundary consistency and observability

- **FR-032**: Feature-003 MUST establish cross-boundary coverage of briefing outcomes at the
  application-service, REST and tool-interface boundaries **without re-implementing verification
  that already exists**. Feature-001's existing verification of briefing outcomes at the REST and
  tool-interface boundaries MUST be tracked in Feature-003's traceability record as
  re-verification satisfying this requirement, inclusive of the boundaries whose observable
  results differ.
- **FR-033**: Feature-003 MUST add new boundary verification only where an outcome's observable
  result differs between boundaries and is not already covered, including the failure result each
  outcome maps to at each boundary.
- **FR-034**: Feature-003 MUST verify that operational records of the workflow carry only metadata,
  and contain no briefing text, no prompt text, no acceptance-criteria content, and no secrets.

#### Recorded gaps and traceability

- **FR-035**: Feature-003 MUST record the specified treatment of briefing content with no substance
  as a single expected-fail verification, MUST register the mismatch with the delivered
  implementation as a defect, and MUST NOT correct the implementation.
- **FR-036**: Each recorded defect MUST be carried in the annotation of the expected-fail
  verification that demonstrates it, which is the authoritative record, and MUST also be
  aggregated into the traceability record so that all findings are reviewable in one place. A
  defect recorded only in prose, with no verification carrying it, does not satisfy this
  requirement.
- **FR-037**: Feature-003 MUST verify that requests which do not invoke generation complete within
  the time budget Feature-001 SC-006 states, under the measurement conditions that criterion names.
- **FR-038**: Feature-003 MUST record the deferral of Feature-001 SC-007 together with its reason,
  rather than leaving the criterion unresolved without explanation.
- **FR-039**: Feature-003 MUST produce a traceability record connecting each verified scenario to
  the requirement, success criterion or backlog story it satisfies.
- **FR-040**: The traceability record MUST be accompanied by a verification confirming that every
  verification the record cites still exists. A record citing a verification that no longer
  resolves MUST cause that confirming verification to fail, so the record cannot silently drift
  out of step with the work it describes.
- **FR-041**: Feature-003 MUST record any approved criterion within its scope that it does not
  verify, together with the reason.

### Key Entities

- **Workflow scenario**: One complete briefing request exercised from a defined starting state to
  exactly one explicit outcome. Carries the starting state, the controlled outcomes that drive it,
  the expected result, and what it is traceable to.
- **Controlled outcome**: A predetermined result supplied at the generation or validation boundary
  in place of an implementation that does not yet exist. Represents a success or a specific kind of
  failure, and for validation may carry visibly synthetic criteria and feedback.
- **Traceability record**: The connection between verified scenarios and the requirements, success
  criteria and backlog stories they satisfy, including criteria recorded as unverified with their
  reasons.
- **Recorded defect**: A mismatch between approved specified behaviour and delivered behaviour,
  captured by Feature-003 for resolution elsewhere.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the briefing-workflow outcomes named in FR-012 through FR-021 have at least
  one verifying scenario; 0 remain unverified.
- **SC-002**: 100% of briefing requests exercised reach exactly one explicit outcome; 0 end with no
  result surfaced.
- **SC-003**: 0 production source files and 0 Feature-001 or Feature-002 verification artifacts are
  changed by Feature-003.
- **SC-004**: 0 scenarios added by Feature-003 duplicate behaviour already verified adequately by
  Feature-001 or Feature-002.
- **SC-005**: 100% of Feature-003's scenarios run with no access to any external service, workspace
  or network.
- **SC-006**: 0 invented Structured Advisor Briefing acceptance criteria appear anywhere in
  Feature-003; 100% of acceptance-criteria values used are visibly synthetic.
- **SC-007**: For every outcome exercised, the number of times a validated briefing is written
  matches the specified behaviour; 0 outcomes store a briefing that has not passed validation.
- **SC-008**: 100% of failing outcomes leave a student's previously stored validated briefing
  intact.
- **SC-009**: The order in which the workflow engages its boundaries is verified for both the
  first-attempt and retry paths; 0 requests attempt generation more than twice.
- **SC-010**: For validation failures that reported failed criteria or feedback, 100% of retry
  requests carry exactly that reported content; for those that reported neither, 100% of retry
  requests are unchanged.
- **SC-011**: 0 briefing texts, prompt texts, acceptance-criteria contents or secrets appear in the
  workflow's operational records.
- **SC-012**: 100% of Feature-003's verified scenarios are traceable to a requirement, success
  criterion or backlog story; 100% of approved criteria in scope that remain unverified are
  recorded with a reason; 100% of recorded defects are carried by an expected-fail verification
  and aggregated in the traceability record.
- **SC-013**: Requests that do not invoke generation are confirmed to complete within the time
  budget Feature-001 SC-006 states.
- **SC-014**: The full verification suite, including every pre-existing Feature-001 and Feature-002
  scenario, completes successfully.
- **SC-015**: 100% of briefing outcomes observable at more than one boundary are accounted for in
  the traceability record, either by tracked Feature-001 re-verification or by new verification
  where the observable result differs; 0 outcomes are verified twice for the same observable
  result at the same boundary.
- **SC-016**: 100% of the verifications cited by the traceability record resolve to a verification
  that exists, confirmed automatically rather than by manual inspection.

## Assumptions

- The approved Product Backlog US-18 story text, quoted in the Overview, was supplied by the
  product owner and confirmed to match this specification's scope. It names generation,
  validation, retry, error handling and valid-briefing storage, which are precisely the areas
  covered here, and the product owner confirmed that User Stories 1 through 4 require neither
  broadening nor narrowing.
- "Verified adequately" means an existing scenario asserts the same observable behaviour from the
  same starting state. Where an existing scenario asserts an outcome but not a workflow property
  such as boundary ordering or write count, that property is treated as unverified and is in scope.
- Store behaviour parity at the storage-contract level is already verified by Feature-002 and is
  therefore complete. What FR-031 requires is different and additional: User Story 3's
  storage-decision outcomes exercised at the *workflow* level against governed storage, rather
  than the storage contract in isolation.
- Feature-001 SC-006's time budget is verified against the measurement conditions that criterion
  names — the mock data source and the default in-memory store — and not against any deployed
  environment.
- The expected-fail verification required by FR-034 remains in place until the underlying defect is
  resolved by a later story, at which point it is expected to be removed rather than retained.
- Feature-003's verification is offline by construction, so it neither requires nor exercises
  credentials, workspace access, or any governed resource.
- No new tooling or dependency is required; the project's existing verification tooling is
  sufficient.

## Dependencies

- **Feature-001 (US-08)** — merged. Supplies the orchestration, the boundary definitions, the
  outcome types and the error taxonomy that Feature-003 verifies.
- **Feature-002 (US-15)** — merged. Supplies the single-retry behaviour and the governed storage
  that Feature-003 verifies, together with the controlled-outcome conventions Feature-003 reuses.
- **The approved Feature-001 and Feature-002 specifications** — the source of truth for every
  behaviour Feature-003 verifies. Where the delivered implementation differs, the specification
  governs and the difference is recorded as a defect.
- **The approved Product Backlog US-18 story** — supplied by the product owner and quoted in the
  Overview. It is the authoritative statement of what Feature-003 must achieve, and its
  acceptance criterion requires the workflow to behave "according to the approved design".
- **Feature-001's existing boundary verification** — Feature-003 depends on it remaining in place
  and passing, because FR-032 satisfies cross-boundary coverage by tracking it as re-verification
  rather than re-implementing it. Should that verification be removed or weakened, Feature-003's
  cross-boundary coverage would lapse with it.

Unavailable dependencies, which bound what Feature-003 can verify:

- The concrete generative integration — **US-13**. Real provider behaviour cannot be exercised.
- The final briefing prompt and instructions — **US-12**. Prompt content cannot be asserted.
- The real acceptance-criteria validation — **US-14**. Briefing quality cannot be assessed.
- A governed storage environment and end-to-end integration — **US-16** and deployment
  infrastructure.

## Out of Scope

- The non-briefing service surface: health reporting, the high-risk student list, and
  student-profile retrieval.
- Any change to production behaviour, including fixing defects Feature-003 surfaces — **US-19
  through US-23**.
- Any change to Feature-001 or Feature-002 verification artifacts, including consolidating
  duplication between them.
- Advisor-facing presentation and broad application testing — **US-17**.
- Concurrent briefing requests for the same student — Feature-002 declares this not specially
  handled.
- Semantic assessment of briefing quality and any acceptance-criteria content — **US-14**.
- Assertions about final briefing prompt content — **US-12**.
- Real generative-provider behaviour: latency, non-determinism, rate limiting, content filtering,
  and token cost — **US-13**.
- Live governed-storage verification and full end-to-end component integration — **US-16** and
  deployment infrastructure.
- Verification of Feature-001 SC-007 by substituting the final instructions and acceptance criteria
  at their boundaries. The US-12 and US-14 work is expected to be delivered outside that boundary,
  so the substitution that criterion describes is not anticipated during Feature-003. Recorded
  under FR-036 rather than left unresolved, and able to be closed later if a real implementation is
  substituted.
- Changes to the machine-learning model, the synthetic-data generation process, or any other
  team-owned notebooks or components.
