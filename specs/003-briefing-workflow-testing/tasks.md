---
description: "Task list for Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)"
---

# Tasks: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Input**: Design documents from `specs/003-briefing-workflow-testing/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` (all approved 2026-09-16)

**Tests**: Feature-003 **is** a verification feature. Every implementation task below produces
verification code or a verification record. There are no separate "tests for the tests".

**Organization**: Tasks are grouped by the four user stories in `spec.md`, plus one cross-cutting
phase for the boundary and observability requirements (FR-032–FR-034), which belong to no single
user story. US1 (P1) is the MVP.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` / `[US4]` for user-story phases only

## Scope guardrails (from the approved plan — do not exceed)

- **No production source file is modified.** Not one.
- **No Feature-001 or Feature-002 verification file is modified**, including `tests/doubles.py`.
- Behaviour those suites already verify accurately is **complete**. It is recorded as tracked
  re-verification in `traceability.md`, never re-implemented (spec Edge Cases; FR-005, FR-032).
- No `conftest.py`, plugin, fixture framework or base class (research R1, R10).
- No tasks for US-12 prompt content, US-13 generative behaviour, US-14 semantic validation, US-16
  end-to-end integration, the advisor-facing interface, concurrency, Feature-001 SC-007
  substitution, or fixing any defect this feature records.
- No invented acceptance criteria. Fixture criteria values are visibly synthetic (FR-010).
- No Git or GitHub write operations.

## Files touched (per `plan.md` § Project Structure)

| Action | Path |
|---|---|
| NEW | `student_attrition_risk_app/tests/workflow_doubles.py` |
| NEW | `student_attrition_risk_app/tests/test_briefing_workflow_outcomes.py` |
| NEW | `student_attrition_risk_app/tests/test_briefing_workflow_retry.py` |
| NEW | `student_attrition_risk_app/tests/test_briefing_workflow_storage.py` |
| NEW | `student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py` |
| NEW | `student_attrition_risk_app/tests/test_briefing_workflow_traceability.py` |
| NEW | `specs/003-briefing-workflow-testing/traceability.md` |
| READ-ONLY | Every file under `student_attrition_risk_app/src/student_attrition_risk/` |
| READ-ONLY | All twelve pre-existing files under `student_attrition_risk_app/tests/`, including `doubles.py` |

---

## Phase 1: Setup

**Purpose**: Establish the pre-change baseline that Feature-003 must not disturb.

- [X] T001 From `student_attrition_risk_app/`, run `uv sync --dev`, then `uv run ruff check .` and `uv run pytest`; record in the task notes that the pre-existing suite is green (84 passing across 12 files) before any Feature-003 file is added, per `quickstart.md` § Baseline.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The controlled-outcome support module every user story depends on.
**⚠️ No user story work may begin until this phase is complete.**

All Phase 2 tasks write to the same file, so none are parallelisable.

- [X] T002 Create `student_attrition_risk_app/tests/workflow_doubles.py` importing `ScriptedGenerationProvider`, `ScriptedValidator` and `FakeFilesClient` from the existing `tests/doubles.py` (import only — that file is read-only), and define the visibly synthetic acceptance-criteria constants required by FR-010 per `contracts/workflow-doubles.md` § Synthetic criteria constants.
- [X] T003 Add the prompt-aware generation double to `student_attrition_risk_app/tests/workflow_doubles.py`: satisfies the `GenerationProvider` protocol, returns a different draft depending on whether the received `composed_prompt` carries the retry revision block, records every received context for identity-field assertions, and returns deterministic visibly synthetic text (research R3; `contracts/workflow-doubles.md`). (depends on T002)
- [X] T004 Add the seam call recorder to `student_attrition_risk_app/tests/workflow_doubles.py`: thin wrappers for the generation, validation, retry and store boundaries that all append to **one shared ordered list**, each entry naming the boundary and the attempt, delegating unchanged to the wrapped boundary (research R2). (depends on T002)
- [X] T005 Add the write-counting store wrapper and its raising variant to `student_attrition_risk_app/tests/workflow_doubles.py`: satisfies the `BriefingStore` protocol by delegating to a real store while counting validated-briefing writes; the variant raises the existing storage error on write. Do not import Feature-002's file-local equivalent (`contracts/workflow-doubles.md`). (depends on T002)
- [X] T006 Add the composition helper to `student_attrition_risk_app/tests/workflow_doubles.py`: assembles a `StudentService` from a scenario's controlled outcomes, chosen store and optional recorder using existing public constructors only, passing the **same** generation and validation instances to both the service and the retry workflow as the composition root does; optionally exposes the service through the REST or tool boundary. (depends on T003, T004, T005)

**Checkpoint**: Controlled outcomes, recorder, write counter and composition helper ready.

---

## Phase 3: User Story 1 — Confirm every briefing outcome behaves as specified (Priority: P1) 🎯 MVP

**Goal**: Every outcome a briefing request can reach is accounted for — either by an existing
verification recorded as tracked re-verification, or by a new Feature-003 verification for the
gaps — and no request can end without exactly one explicit outcome.

**Independent Test**: The outcome inventory shows every outcome in FR-012–FR-021 accounted for,
and the single-explicit-outcome guarantee passes across the whole matrix with no external service.

- [X] T007 [US1] Create `specs/003-briefing-workflow-testing/traceability.md` with the four sections defined in `contracts/traceability-record.md`, then inventory the service-boundary coverage of FR-012 through FR-021 against `tests/test_briefing_orchestration.py` and `tests/test_briefing_retry_integration.py`; record each already-covered outcome under **Tracked re-verification** citing the existing verification by file and name, and list the genuine gaps in the task notes. Do not re-implement anything already covered (FR-005; spec Edge Cases).
- [X] T008 [US1] Create `student_attrition_risk_app/tests/test_briefing_workflow_outcomes.py` covering **only the outcome gaps identified in T007**, driving `StudentService.request_briefing` and `get_stored_briefing` with controlled outcomes from `tests/workflow_doubles.py` and the existing mock-repository fixtures. Add a Tracked-re-verification or Scenario-map entry in `traceability.md` for each. (depends on T006, T007)
- [X] T009 [US1] Add the FR-022 guarantee to `student_attrition_risk_app/tests/test_briefing_workflow_outcomes.py`: across the full outcome matrix, every briefing request reaches **exactly one** explicit outcome — a validated briefing or an explicit failure — and never an absent or ambiguous result. This is a matrix-wide property no existing verification asserts. (depends on T008)
- [X] T010 [US1] From `student_attrition_risk_app/`, run `uv run ruff check .` and `uv run pytest tests/test_briefing_workflow_outcomes.py`, then `uv run pytest` to confirm all pre-existing verifications still pass.

**Checkpoint**: Outcome coverage complete and accounted for; MVP is demonstrable.

---

## Phase 4: User Story 2 — Confirm the exceptional retry path is correct and bounded (Priority: P2)

**Goal**: The retry path engages the workflow's boundaries in the specified order, carries the
reported validation feedback into the second attempt, and can never exceed one additional attempt.

**Independent Test**: With controlled outcomes scripted to fail then succeed, and separately to
fail twice, boundary order, second-request content and total attempts are each confirmed directly.

All Phase 4 tasks write to the same file, so none are parallelisable within the phase.

- [X] T011 [US2] Create `student_attrition_risk_app/tests/test_briefing_workflow_retry.py` verifying FR-023: using the seam call recorder, the workflow engages its boundaries in the order defined by Feature-001 `contracts/internal-seams.md` lines 102–120, for both the first-attempt-success path and the retry path. Assert the **order**, not only counts — no existing verification does. (depends on T006)
- [X] T012 [US2] Add FR-024 to `student_attrition_risk_app/tests/test_briefing_workflow_retry.py`: when a validation failure reported failed criteria and feedback, exactly that reported content reaches the second generation attempt. Use the prompt-aware double so second-attempt success is **conditional on propagation**, and assert the reported values appear verbatim with nothing added (research R3). (depends on T011)
- [X] T013 [US2] Add FR-025 to `student_attrition_risk_app/tests/test_briefing_workflow_retry.py`: when a validation failure reported neither failed criteria nor feedback, and separately for a generation-failure retry, the second request's composed prompt is **identical** to the first and the identity fields — student hash, prediction, features, instructions provenance — are preserved. (depends on T011)
- [X] T014 [US2] Add FR-026 to `student_attrition_risk_app/tests/test_briefing_workflow_retry.py`: across every retry-reachable scenario, generation is attempted **at most twice**, relying on the scripted double's over-call error as the third-attempt guard. (depends on T011)
- [X] T015 [US2] Add FR-027 to `student_attrition_risk_app/tests/test_briefing_workflow_retry.py`: the retry path performs no persistence of its own, and a briefing produced by retry is written exactly once, by the service. Use the write-counting wrapper. (depends on T011)
- [X] T016 [US2] From `student_attrition_risk_app/`, run `uv run ruff check .` and `uv run pytest tests/test_briefing_workflow_retry.py`, then the full suite; add the Scenario-map entries for T011–T015 to `specs/003-briefing-workflow-testing/traceability.md`.

**Checkpoint**: Retry ordering, propagation and bounding verified; US1 and US2 both pass independently.

---

## Phase 5: User Story 3 — Confirm validated briefings are stored only when they should be (Priority: P3)

**Goal**: A briefing is written exactly when the specification requires, never when it does not, a
failure never destroys an existing briefing, and the governed store behaves identically.

**Independent Test**: Every outcome is run while observing the write count, and the six
storage-decision outcomes behave identically against the governed store.

All Phase 5 tasks write to the same file, so none are parallelisable within the phase.

- [X] T017 [US3] Create `student_attrition_risk_app/tests/test_briefing_workflow_storage.py` verifying FR-028 with the write-counting wrapper: exactly one write for a briefing validated on either attempt; **zero** writes for every terminal failure, refusal, not-found result, configuration failure and get-or-create return. Assert counts, not only final state. (depends on T006)
- [X] T018 [US3] Add FR-029 to `student_attrition_risk_app/tests/test_briefing_workflow_storage.py`: no briefing that has not passed validation is ever stored or surfaced as validated, on any path. (depends on T017)
- [X] T019 [US3] Add FR-030 to `student_attrition_risk_app/tests/test_briefing_workflow_storage.py`: a previously stored validated briefing survives every failing outcome and remains the one retrieval surfaces, including after a failed explicit regeneration and after a storage failure. (depends on T017)
- [X] T020 [US3] Add FR-031 to `student_attrition_risk_app/tests/test_briefing_workflow_storage.py`: compose the workflow against `VolumeBriefingStore`, constructed with a directly-built `Settings` carrying a briefing volume and the existing `FakeFilesClient` injected, and re-run **only the six storage-decision outcomes** from User Story 3 — not any other scenario (approved clarification; research R4). Outcomes that neither read nor write storage must not be re-run. (depends on T017)
- [X] T021 [US3] From `student_attrition_risk_app/`, run `uv run ruff check .` and `uv run pytest tests/test_briefing_workflow_storage.py`, then the full suite; add the Scenario-map entries for T017–T020 to `specs/003-briefing-workflow-testing/traceability.md`.

**Checkpoint**: Storage decisions and governed-store parity verified.

---

## Phase 6: Cross-Cutting — Boundary consistency and observability (FR-032–FR-034)

**Purpose**: The boundary and log-hygiene requirements, which belong to no single user story.
Placed before User Story 4 because the traceability record aggregates their results.

**Independent Test**: The REST boundary is recorded as tracked re-verification with no new
verification written for it; the three uncovered tool-interface outcomes pass; every failure-path
operational record is confirmed metadata-only.

- [X] T022 Inventory the REST and tool-interface coverage against the outcome matrix and record the result in `specs/003-briefing-workflow-testing/traceability.md` under **Tracked re-verification**, per FR-032. Planning established that `tests/test_api.py` already covers the REST **write** outcomes — success, configuration failure, not-flagged, unknown student, get-or-create with regeneration, terminal failure with category, storage failure, and stored retrieval including none-available — so **no REST verification is written for those**; cite each existing verification by file and name (research R8). **Corrected after independent review**: a storage outage during retrieval is *not* covered by `test_api.py`, and is verified by Feature-003 under FR-033 — see the remediation note below.
- [X] T023 Create `student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py` verifying FR-033 for the tool interface: **terminal failure** produces the expected tool error carrying the failure category. Use the same async marker `tests/test_mcp_tools.py` uses and add no configuration file (research R9). This outcome has no existing coverage at that boundary. (depends on T006, T022)
- [X] T024 Add the remaining two FR-033 gaps to `student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py`: **storage failure** and **configuration failure** at the tool interface. Neither has existing coverage there. Do not re-verify registration, get-or-create, not-at-risk, not-found or stored retrieval — `tests/test_mcp_tools.py` already covers those. (depends on T023)
- [X] T025 Add FR-034 to `student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py`: capture the workflow's operational records for every **failure** path — terminal generation, terminal validation, storage error, not-at-risk, not-found and none-available — and confirm each carries metadata only, with no briefing text, prompt text, acceptance-criteria content or secret. The two existing hygiene verifications assert only the success path, so every failure path is unasserted. (depends on T023)
- [X] T026 From `student_attrition_risk_app/`, run `uv run ruff check .` and `uv run pytest tests/test_briefing_workflow_boundaries.py`, then the full suite; add the Scenario-map entries for T023–T025 to `specs/003-briefing-workflow-testing/traceability.md`.

**Checkpoint**: Boundary coverage complete without duplicating REST; failure-path log hygiene verified.

---

## Phase 7: User Story 4 — Make verification traceable and record what remains unverified (Priority: P4)

**Goal**: Every scenario traces to what it satisfies, blank generation content is verified as
rejected, the SC-006 timing criterion is closed, and the record cannot silently drift.

**Independent Test**: The traceability record names what each scenario satisfies, lists every
unverified criterion with a reason, and its self-check passes.

- [X] T027 [US4] Create `student_attrition_risk_app/tests/test_briefing_workflow_traceability.py` with the blank-content verification (FR-035): assert that a generation response carrying no substance — empty and whitespace-only — is surfaced as a generation failure with nothing stored, on both the first and the retry attempt. This is an **ordinary** verification and must pass: the defect it originally recorded was resolved before implementation, so no expectation marker is used. Do not change production behaviour. (depends on T006)
- [X] T028 [US4] Add the FR-037 timing verification to `student_attrition_risk_app/tests/test_briefing_workflow_traceability.py`: measure the three non-generation request paths — unknown student, not-flagged student, and a get-or-create request returning an existing briefing — against the mock repository and in-memory store, and confirm each completes within the one-second budget Feature-001 SC-006 states. Use those measurement conditions exactly; introduce no tighter threshold and no benchmarking dependency (research R7). (depends on T027)
- [X] T029 [US4] Complete `specs/003-briefing-workflow-testing/traceability.md`: finish the **Scenario map** so every Feature-003 scenario appears exactly once with its requirement, success criterion and backlog story; record the blank-content defect in **Recorded defects** as resolved, naming its resolution and the T027 verification that now covers the behaviour ordinarily; and populate **Unverified criteria** including Feature-001 SC-007 with its specific reason — the US-12/US-14 work is expected to be delivered outside the seam boundary, so the substitution that criterion describes is not anticipated (FR-038, FR-039, FR-041). (depends on T007, T016, T021, T026, T027, T028)
- [X] T030 [US4] Add the FR-040 self-check to `student_attrition_risk_app/tests/test_briefing_workflow_traceability.py`: read `specs/003-briefing-workflow-testing/traceability.md`, extract every cited verification name from **all** sections including tracked re-verification, resolve each against the verification files' syntax trees, and fail naming any that no longer resolves. Resolve the record path from the repository root; use no runner internals and no new dependency (research R6). (depends on T029)
- [X] T031 [US4] From `student_attrition_risk_app/`, run `uv run ruff check .` and `uv run pytest tests/test_briefing_workflow_traceability.py`, confirming every verification passes — none is expected to fail — and that the self-check passes.

**Checkpoint**: All four user stories and the cross-cutting phase complete and independently verifiable.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T032 From `student_attrition_risk_app/`, run the full merge gate: `uv run ruff check .` and `uv run pytest`. Confirm every pre-existing verification still passes (SC-014), no verification reports as failed or expected-fail, and the suite completes successfully.
- [X] T033 Confirm SC-003 by inspecting the working tree: only files under `student_attrition_risk_app/tests/` and `specs/003-briefing-workflow-testing/` differ, and none of the twelve pre-existing verification files or any production source file is modified.
- [X] T034 Walk the seventeen checks in `specs/003-briefing-workflow-testing/quickstart.md` § Validating the feature and confirm each holds, including the offline re-run with the network disconnected (SC-005).

---

## Dependencies & Execution Order

### Phase order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** → **Phase 3 (US1)** → **Phase 4 (US2)** →
  **Phase 5 (US3)** → **Phase 6 (Cross-cutting)** → **Phase 7 (US4)** → **Phase 8 (Polish)**.
- Phase 2 blocks everything: every story consumes `tests/workflow_doubles.py`.
- Phase 7 is last because `traceability.md` aggregates the results of all preceding phases. Each
  earlier phase contributes its own entries as it completes, so the aggregation in T029 is a
  completion step rather than a rewrite.

### Key task dependencies

- T002 → T003, T004, T005 → T006
- T006 → T008, T011, T017, T023, T027
- T007 → T008 → T009 → T010
- T011 → T012, T013, T014, T015 → T016
- T017 → T018, T019, T020 → T021
- T022 → T023 → T024, T025 → T026
- T027 → T028; T007 + T016 + T021 + T026 + T027 + T028 → T029 → T030 → T031

### Parallel opportunities

Parallelism here is at **phase level, not task level**. Each phase writes to a single file, so
tasks within a phase are sequential by construction — there are no `[P]` markers, and adding them
would invite write conflicts.

Once Phase 2 is complete, three work streams are genuinely independent and can be taken by
different contributors, because they touch different files:

- **Stream A**: Phase 3 (US1) — `test_briefing_workflow_outcomes.py`
- **Stream B**: Phase 4 (US2) — `test_briefing_workflow_retry.py`
- **Stream C**: Phase 5 (US3) — `test_briefing_workflow_storage.py`, and Phase 6 —
  `test_briefing_workflow_boundaries.py`

Phase 7 requires all three streams to have finished. The only shared file across streams is
`traceability.md`, which each stream appends to at its checkpoint task (T016, T021, T026) — so
stagger those checkpoints or resolve the appends together.

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 (T001) → Phase 2 (T002–T006) → Phase 3 (T007–T010).
2. **Stop and validate**: every outcome in FR-012–FR-021 is accounted for, either by a tracked
   existing verification or a new one, and the single-explicit-outcome guarantee holds.

### Incremental delivery

1. Setup + Foundational → controlled outcomes ready.
2. US1 → outcome coverage accounted for (MVP).
3. US2 → retry ordering, propagation and bounding.
4. US3 → storage decisions and governed-store parity.
5. Cross-cutting → tool-boundary gaps and failure-path log hygiene.
6. US4 → traceability, defect record, timing criterion, self-check.
7. Polish → merge gate, scope confirmation, quickstart walk.

## Notes

- `[P]` = different files, no dependency on an incomplete task. None apply here; see Parallel
  opportunities for why.
- Each phase's checkpoint task appends that phase's entries to `traceability.md`, so the record
  grows with the work instead of being reconstructed at the end.
- Feature-002's tasks proved the value of verifying that a new verification fails before its
  subject exists. That does not transfer here: Feature-003 verifies **already-delivered**
  behaviour, so every verification is expected to pass on first run, T027 included. T027 was
  originally an exception — a strict expected-fail against a defect — but that defect was
  resolved before implementation, so it is now an ordinary verification like the rest.
- If any task appears to require changing a production file or a pre-existing verification file,
  **stop and raise it** rather than proceeding — that would contradict the approved plan's conflict
  check, which found no such requirement.
- No Git or GitHub operations at any point.


---

## Remediation after independent adversarial review (2026-09-17)

An independent review conducted in a separate session, with only artifacts supplied, returned
**request changes** with six P2 findings. It used fault injection rather than inspection: three
injected faults each left all 143 tests passing.

The tasks below remain **complete**, and their checkboxes are unchanged. Each is annotated with
what the remediation added, because a tick alone would not show that the original work needed a
second pass. The full report is at
`docs/AI Agent Software Development Implementation Documentation/T115_Feature_003_Independent_Review.md`.

| Task | Why it needed a second pass | What completed it |
|---|---|---|
| **T012** (FR-024 feedback propagation) | Substring assertions could not reject a fabricated criterion, and the conditional double keyed on the wrapper header rather than the reported values — so it passed even when the payload was removed | Set-equality assertions over relayed payload values; the double now keys on the reported values; parametrised criteria-only, feedback-only and both, plus a converse scenario |
| **T020** (FR-031 governed-storage parity) | The six entries split the success category in two and omitted the failed-write category entirely; no entry set `fail_upload` while the workflow used the governed store | A governed failed-write scenario: seed a prior briefing, drive a valid result, fail the upload, assert the storage failure, confirm the prior briefing survived |
| **T022** (FR-032 boundary inventory) | The inventory concluded that `test_api.py` covers every REST outcome. It covers every **write** outcome; a read outage was unverified, and a mutation reporting one as a 404 absence survived the whole suite | Seven read-outage scenarios across the service, REST and tool boundaries, each asserted distinct from genuine absence; the traceability record's REST claim narrowed to writes |
| **T025** (FR-034 log hygiene) | The privacy helper joined `record.getMessage()` only, so a record whose rendered traceback carried the briefing sentinel was approved | Log output rendered through a formatter including exception information and structured fields, plus a verification of the check itself |
| **T029** (FR-039 traceability record) | The scenario map held 25 of 34 verifications, and tracked re-verification used sibling shorthand that the self-check could not guard | All forty verifications mapped; sibling shorthand replaced with explicit citations; a second self-check added guarding *exists implies mapped* |

Suite after remediation: **153 passed**, ruff clean. Every injected fault now fails. No production
source file and none of the thirteen pre-existing test files was modified by either pass.
