# Implementation Plan: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Branch**: `feat/feature-003-briefing-workflow-testing` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-briefing-workflow-testing/spec.md`

## Summary

Feature-003 verifies the delivered Structured Advisor Briefing workflow — generation, validation,
retry, error handling and validated storage — without adding or changing any application
behaviour. It is delivered entirely as new verification files plus one new record document.

The approach is governed by three constraints that shape every decision below: **nothing
production changes**, **nothing already verified is verified again**, and **generation and
validation outcomes are supplied under test control** because US-13 and US-14 do not exist.

Planning inspection confirms the specification is satisfiable within those constraints. **No
conflict was found that would require modifying production source or any Feature-001/Feature-002
verification file.** The single largest planning finding is that the REST boundary's briefing
**write** outcomes are already verified by Feature-001 while the tool interface's are not, which
converts a large part of the cross-boundary requirement from new work into tracked
re-verification.

**Corrected after independent review (2026-09-17).** As first written, that finding claimed the
REST boundary was comprehensively verified. It holds for the write outcomes only: Feature-001 does
not exercise a storage outage during *retrieval*, and a mutation reporting one as a 404 absence
survived the entire suite. The remediation adds read-outage verification at the service, REST and
tool boundaries. Paragraphs below are annotated where they overstated the existing coverage.

## Technical Context

**Language/Version**: Python 3.11–3.13 (`requires-python = ">=3.11,<3.14"`)

**Primary Dependencies**: No new dependency. Existing dev group supplies `pytest>=8`,
`pytest-asyncio`, `ruff>=0.8`; runtime supplies `fastapi` (its test client), `fastmcp`,
`pydantic`, and `databricks-sdk` (its `NotFound` error type, used by the existing fake files
client).

**Storage**: None introduced. Verification exercises the existing in-memory store and the
existing Volume-backed store through a controlled in-memory files client.

**Testing**: `pytest`, run as `uv run pytest` from `student_attrition_risk_app/`.

**Target Platform**: Developer workstation and CI. Offline by construction — no network, no
workspace, no credentials.

**Project Type**: Additive verification suite over an existing Python backend.

**Performance Goals**: Feature-001 SC-006 — non-generation briefing requests complete within one
second against the mock repository and in-memory store. No goal is introduced for Feature-003's
own suite beyond remaining comparable to the current baseline.

**Constraints**: No production source change. No change to any Feature-001/Feature-002
verification file. No duplication of behaviour those suites already verify. No invented
acceptance criteria. Line length 110, ruff rules `E`, `F`, `I`, `UP`.

**Scale/Scope**: Baseline before this feature is 84 passing verifications across 12 files.
Feature-003 adds 5 verification files, 1 support module and 1 record document.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — result unchanged.*

| Principle | Assessment |
|---|---|
| I. Specification-Driven Development | PASS — every planned file traces to numbered requirements in the approved spec. Where delivered behaviour contradicts an approved specification, the specification is preserved and the difference recorded, never the reverse. The blank-content mismatch followed exactly that course and was resolved separately before implementation. |
| II. Strict Scope Containment | PASS — the files-touched table below is exhaustive and read-only entries are explicit. No Feature-001/Feature-002 artifact and no production file is modified. |
| III. Read Broadly, Write Narrowly | PASS — planning inspected the whole application and both prior features; writing is confined to new files. |
| IV. Minimal Necessary Change | PASS — no consolidation of the duplicated doubles across existing suites, despite the duplication being known. That cleanup is explicitly excluded by approved decision H3. |
| V. Reuse and Extend Existing Architecture | PASS — the new support module extends the established `tests/doubles.py` convention rather than replacing it; existing scripted doubles and the fake files client are reused unchanged. No parallel harness. |
| VI. No Unnecessary Complexity | PASS — no test framework, plugin, fixture-injection layer or `conftest.py` is introduced. Support code is a plain importable module, matching what already works. |
| VII. Plan-Defined Implementation Structure | PASS — the specification named no file; this plan names them all. |
| VIII. Application Technology Compatibility | PASS — Python and the existing tooling only; the governed store is exercised through its existing injection point. |
| IX. Separation of Responsibilities and Modularity | PASS — one verification file per specification concern; support code separate from scenarios. |
| X. Security and Privacy | PASS — deidentified synthetic hashes only, from the existing mock repository. No credential is required or referenced. Log-hygiene verification asserts the absence of briefing text, prompt text and secrets. |
| XI. Input Validation and Explicit Error Handling | PASS — the plan verifies the existing explicit error taxonomy rather than altering it. |
| XII. Proportionate Testing | PASS — the largest single planning decision is a subtraction: the REST boundary is already covered and is tracked rather than re-verified, and governed-storage parity re-runs six outcomes rather than the whole suite. Every planned scenario targets a property no existing verification asserts. |
| XIII. Human Review of AI-Generated Development Work | PASS — the plan is submitted for review before tasks; the traceability record exists to make review possible. |
| XIV. Documentation and Implementation Traceability | PASS — this feature's central deliverable is traceability, including a self-checking record that closes the drift found in Feature-001's equivalent table. |
| XV. Completion Means Specification Satisfaction | PASS — completion is the 41 functional requirements and 16 success criteria, nothing more. |
| XVI. Preserve Team Contributions | PASS — no file authored by another contributor is modified. The advisor-facing interface is untouched and excluded. |
| XVII. Human-Controlled Version Control | PASS — no Git or GitHub write operation is planned or performed. |

**No violations. Complexity Tracking is therefore empty and omitted.**

## Project Structure

### Documentation (this feature)

```text
specs/003-briefing-workflow-testing/
├── spec.md              # Approved and clarified specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── workflow-doubles.md
│   └── traceability-record.md
├── traceability.md      # DELIVERABLE created during implementation (FR-038/FR-039)
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks output — not created here
```

### Source Code (repository root)

```text
student_attrition_risk_app/
├── src/student_attrition_risk/          # READ-ONLY — every file
│   ├── api.py                           #   REST boundary under verification
│   ├── mcp_server.py                    #   tool boundary under verification
│   ├── student_service.py               #   orchestration under verification
│   ├── retry_workflow.py                #   retry under verification
│   ├── briefing_store.py                #   both stores under verification
│   ├── briefing_provider.py             #   generation boundary (controlled in test)
│   ├── briefing_validation.py           #   validation boundary (controlled in test)
│   ├── briefing_instructions.py         #   used as-is; content never asserted
│   ├── models.py, ports.py, config.py   #   types and settings used by scenarios
│   ├── student_repository.py            #   mock repository supplies fixtures
│   ├── ui.py, streamlit_host.py         #   EXCLUDED from scope entirely
│   ├── databricks_client.py, main.py    #   not exercised
└── tests/
    ├── doubles.py                       # READ-ONLY — reused, not modified
    ├── test_api.py                      # READ-ONLY — REST coverage tracked
    ├── test_briefing_orchestration.py   # READ-ONLY
    ├── test_briefing_retry_integration.py  # READ-ONLY
    ├── test_briefing_seams.py           # READ-ONLY
    ├── test_briefing_store.py           # READ-ONLY
    ├── test_config.py                   # READ-ONLY
    ├── test_mcp_tools.py                # READ-ONLY — gaps covered in new file
    ├── test_retry_workflow.py           # READ-ONLY
    ├── test_streamlit_proxy.py          # READ-ONLY
    ├── test_student_service.py          # READ-ONLY
    ├── test_template_briefing.py        # READ-ONLY
    │
    ├── workflow_doubles.py              # NEW — support module
    ├── test_briefing_workflow_outcomes.py      # NEW — User Story 1
    ├── test_briefing_workflow_retry.py         # NEW — User Story 2
    ├── test_briefing_workflow_storage.py       # NEW — User Story 3
    ├── test_briefing_workflow_boundaries.py    # NEW — FR-032/033/034
    └── test_briefing_workflow_traceability.py  # NEW — User Story 4
```

### Structure Decision

Six new files in `student_attrition_risk_app/tests/`, plus one record document in the feature
folder. Verification files map one-to-one onto specification concerns so a reviewer can find the
evidence for any user story without searching.

Three structural choices, each recorded with its rationale in `research.md`:

- **A plain importable support module, not a `conftest.py`.** `tests/doubles.py` already
  establishes that a plain module imported by bare name works here, because pytest places the
  tests directory on the import path. A `conftest.py` would apply implicitly to all 84 existing
  verifications, which risks affecting files this feature must not disturb.
- **Support code extends rather than replaces `doubles.py`.** `ScriptedGenerationProvider`,
  `ScriptedValidator` and `FakeFilesClient` are imported and reused unchanged. The new module
  adds only what does not exist: a prompt-aware generation double, a seam-call recorder, and a
  write-counting store wrapper.
- **The traceability record lives with the specification, not the tests.** It is a review
  artifact. Its self-check resolves the path from the repository root.

## Design

### 1. Controlled outcomes — `tests/workflow_doubles.py`

Reused unchanged from `tests/doubles.py`: `ScriptedGenerationProvider` (ordered draft-or-raise,
over-call is an error — this is how "no third attempt" stays provable), `ScriptedValidator`
(ordered outcomes), `FakeFilesClient` (in-memory files surface with a not-found error).

Added, because nothing equivalent exists:

- **A prompt-aware generation double.** Returns a different draft depending on whether the
  received composed prompt carries the retry revision block. This makes second-attempt success
  *conditional on feedback having propagated*, which is a stronger guarantee than matching a
  substring, and it reproduces the behavioural shape of a model responding to revision feedback
  with no model involved.
- **A seam-call recorder.** Thin wrappers around the generation, validation, retry and store
  boundaries that append an entry to one shared ordered list. This is what makes FR-023's call
  *order* observable; every existing verification asserts counts or outcomes only.
- **A write-counting store wrapper.** Feature-002 has a file-local equivalent, which this feature
  may not modify or import across, so an equivalent is provided here for write-count assertions
  across the full outcome matrix.
- **Synthetic criteria constants.** Visibly synthetic acceptance-criteria values, so no fixture
  can be mistaken for approved US-14 content (FR-010).

Generated draft text is deterministic and visibly synthetic, so a fixture briefing can never be
mistaken for a real one in a log or a stored document.

### 2. Outcome coverage — `tests/test_briefing_workflow_outcomes.py` (User Story 1)

Drives `StudentService.request_briefing` and `get_stored_briefing` through every outcome, with
controlled generation and validation. Covers the ten outcomes in FR-012 through FR-021 and the
single-explicit-outcome guarantee in FR-022, using the existing mock repository fixtures
(`synthetic-student-001` flagged, `-002` not flagged, `-003` for retrieval).

Where Feature-001 already asserts the same observable behaviour from the same starting state, the
scenario is **not repeated** — it is entered in the traceability record against the existing
verification. What this file adds is the properties those verifications do not assert: that
exactly one explicit outcome is reached on every path, and that the outcome matrix holds as a
matrix rather than as isolated cases.

### 3. Retry path — `tests/test_briefing_workflow_retry.py` (User Story 2)

Verifies the properties outcome testing cannot show (FR-023 through FR-027): boundary engagement
**order** via the recorder; feedback propagation into the attempt-2 request when criteria or
feedback were reported; an attempt-2 request identical to attempt 1 when neither was reported and
for a generation-failure retry; generation attempted at most twice; and that the retry path
performs no persistence of its own while a retry-produced briefing is stored exactly once.

Feature-002 already verifies the retry *outcome* matrix comprehensively. This file does not repeat
it. The ordering assertions and the matrix-wide at-most-twice guarantee are new.

### 4. Storage decisions — `tests/test_briefing_workflow_storage.py` (User Story 3)

Verifies FR-028 through FR-031 using the write-counting wrapper: exactly one write for a briefing
validated on either attempt; zero writes for every terminal failure, refusal, not-found,
configuration failure and get-or-create return; a previously stored briefing surviving every
failing outcome; and that nothing unvalidated is ever stored or surfaced.

**Governed-storage parity** re-runs the six storage-decision outcomes only, per the approved
clarification — not the whole suite. The workflow is composed against `VolumeBriefingStore`
constructed with a `Settings` carrying a briefing volume and the existing fake files client. Both
`Settings` and the store's files-client injection point are already public, so no production
change is required. Outcomes that neither read nor write storage are deliberately not re-run.

### 5. Boundaries and observability — `tests/test_briefing_workflow_boundaries.py`

**Planning found the REST boundary's write outcomes already verified** by Feature-001: success,
configuration failure, not-flagged, unknown student, get-or-create with regeneration, terminal
failure with its category, storage failure, and stored-briefing retrieval including the
none-available result. Under FR-032 that coverage is **tracked in the traceability record as
re-verification and not repeated**.

**A read outage is not among them.** Independent review found that no existing verification
exercises a storage failure during retrieval at any boundary — Feature-001's storage-error
scenario covers a write, and Feature-002's read-failure scenarios test the store adapter in
isolation rather than the boundary mapping. Under FR-033 that outcome is covered by Feature-003 at
the service, REST and tool boundaries, because an outage reported as absence would tell an advisor
a briefing does not exist when the store is merely unreachable.

**The tool interface has three genuine gaps.** Its existing verifications cover registration,
get-or-create with regeneration, two error messages (not-at-risk, not-found) and stored
retrieval. They do not cover terminal failure, storage failure, or configuration failure. Those
three outcomes have an observable result at that boundary that no verification asserts, so under
FR-033 they are covered here. Async scenarios use the same marker the existing tool verifications
use, which already resolves without any shared configuration file.

**Failure-path log hygiene** (FR-034) is also covered here. Both existing hygiene verifications
assert only the success-path record; every failure-path record — terminal generation, terminal
validation, storage error, not-at-risk, not-found, none-available — is unasserted. This file
confirms each carries metadata only, with no briefing text, prompt text, criteria content or
secret.

### 6. Traceability, defect and timing — `tests/test_briefing_workflow_traceability.py` (User Story 4)

Three concerns, matching User Story 4's acceptance scenarios:

- **The record self-check (FR-040).** Reads `traceability.md`, extracts every verification it
  cites, and confirms each still resolves by parsing the verification files' syntax trees for
  defined verification names. A cited name that no longer exists fails this check. Parsing the
  source rather than interrogating the runner keeps the check independent of how the suite is
  invoked.
- **Blank generation content (FR-035).** An ordinary verification that a generation response
  carrying no substance — empty or whitespace only — is surfaced as a generation failure with
  nothing stored, on both the first and the retry attempt. This began as an expected-fail
  recording a defect: planning confirmed empirically that such content was returned as validated
  and stored. The defect was fixed before implementation, so the scenario now verifies behaviour
  the implementation exhibits. `traceability.md` retains the defect with its resolution (FR-036).
- **The SC-006 timing verification (FR-037).** Measures the three non-generation request paths —
  not-found, not-flagged, and get-or-create returning an existing briefing — against the mock
  repository and in-memory store, exactly the conditions the criterion names, and confirms each
  completes within the stated one-second budget. Headroom against in-memory operations is several
  orders of magnitude, so this does not introduce a load-sensitive verification.

### 7. The traceability record — `specs/003-briefing-workflow-testing/traceability.md`

Hand-maintained, per the approved clarification, and self-checked by the verification above. It
carries four sections: scenarios mapped to requirements, success criteria and backlog stories;
tracked re-verification, naming the existing Feature-001 verifications that satisfy cross-boundary
coverage; recorded defects, outstanding ones aggregated from their expected-fail annotations and
resolved ones retained with their resolution;
and criteria recorded as unverified with reasons, which is where Feature-001 SC-007's deferral is
recorded (FR-038).

### 8. What is deliberately not built

No `conftest.py`. No fixture framework, plugin or base class. No generation tooling for the
traceability record. No consolidation of the duplicated doubles across the existing suites. No
re-verification of the REST boundary. No verification of any behaviour the existing 84 already
assert.

## Test plan (proportionate — constitution XII)

| Concern | File | Requirements | Approach |
|---|---|---|---|
| Outcome matrix | `test_briefing_workflow_outcomes.py` | FR-012–FR-022 | Service boundary, controlled outcomes |
| Retry order and feedback | `test_briefing_workflow_retry.py` | FR-023–FR-027 | Seam-call recorder, prompt-aware double |
| Storage decisions and parity | `test_briefing_workflow_storage.py` | FR-028–FR-031 | Write-counting wrapper; six outcomes against both stores |
| Tool-boundary gaps, log hygiene | `test_briefing_workflow_boundaries.py` | FR-032–FR-034 | Tool interface for three uncovered outcomes; captured records for failure paths |
| Record self-check, blank content, timing | `test_briefing_workflow_traceability.py` | FR-035–FR-040 | Syntax-tree resolution, blank-content rejection, elapsed-time budget |
| Unverified-criteria record | `traceability.md` | FR-038, FR-039, FR-041 | Hand-maintained document |

**Merge gate**: `uv run ruff check .` and `uv run pytest` from `student_attrition_risk_app/`, with
all pre-existing verifications still passing (SC-014). No verification is expected to fail: the
defect that once warranted an expectation has been resolved.

## Approved decisions carried into this plan

From the confirmed scope decisions and both clarification passes:

1. Briefing workflow only; the non-briefing service surface is out of scope.
2. Purely additive; no production file and no Feature-001/Feature-002 verification file changes.
3. Behaviour already verified accurately by those suites is complete and is not re-covered.
4. Controlled generation and validation outcomes; no invented acceptance criteria.
5. Blank content is verified as an ordinary scenario. It was recorded as a defect during
   planning and resolved separately before implementation; Feature-003 corrected nothing.
6. Feature-001 SC-006 is closed; SC-007 is excluded with its deferral recorded.
7. The advisor-facing interface and concurrency are excluded.
8. Cross-boundary coverage is satisfied by tracking existing verification, adding new only where
   an observable result differs — which planning resolved to the three tool-boundary gaps.
9. An outstanding defect's expected-fail annotation is its authoritative record; the traceability
   record aggregates, and retains resolved defects with their resolution.
10. The traceability record is hand-maintained with a verification that every cited name resolves.
11. Governed-storage parity re-runs the six storage-decision outcomes only.

## Conflict check

The feature input required planning to stop and report if satisfying the specification would need
a production change or a change to an existing verification file. **Each requirement was checked
against the delivered code and none does:**

- Call-order observation needs only wrappers injected at the existing constructor boundaries.
- Governed-storage parity needs only the store's existing settings and files-client injection.
- The blank-content requirement is satisfied by verifying the specified behaviour, which the
  implementation now exhibits, so it needs no production change.
- The timing, log-hygiene and tool-boundary requirements exercise existing public surfaces.
- The record self-check reads files and needs no runtime hook.
- No shared configuration file is required, so no existing verification is affected.

**No conflict to report.**

## Phase 0 / Phase 1 outputs

- Phase 0: [research.md](./research.md) — the planning decisions deferred from the specification,
  each with rationale and rejected alternatives.
- Phase 1: [data-model.md](./data-model.md) — the verification-side entities and the shapes the
  scenarios exchange. [contracts/workflow-doubles.md](./contracts/workflow-doubles.md) and
  [contracts/traceability-record.md](./contracts/traceability-record.md) — the internal contracts
  this feature introduces. [quickstart.md](./quickstart.md) — how to run and validate the feature.
