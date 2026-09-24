# Feature Specification: Feature-004 — Final Defect Resolution (US-20)

**Feature Branch**: `feat/feature-004-final-defect-resolution`

**Created**: 2026-09-24

**Status**: Draft

**Input**: User description: "Feature-004 — Final Defect Resolution (US-20, GitHub issue #27). Use the existing directory specs/004-final-defect-resolution, which already contains the defect register. Fix Renny's defects B1, B2 (High), B4 and the Renny half of C3 per the register; log teammates' defects with owner and severity, unfixed; C7 and A9 logged only; C6 and the small-group suppression are design decisions; regression verification in a new verification file only, one group per register ID; never edit merged verification or teammates' source; done-gate is lint-clean changed files and only the 5 known advisor-interface verification failures."

## Overview

Feature-004 is **Product Backlog US-20 — Final Defect Resolution** (GitHub issue #27). The
approved acceptance criterion states:

> **Given** the current defect list and test results are available, **when** final defect
> resolution is performed, **then** critical and high-priority defects are closed and any
> remaining lower-priority defects are documented.

The "current defect list" is the [defect register](./defect-register.md) in this directory. It
consolidates the US-20 defect sweep, records the baseline verification and lint results, and
carries the product owner's decisions. The register is the single source of truth for which
defects exist, who owns them, how severe they are, and what Feature-004 does about each one.

Feature-004 delivers three things:

- **Resolution of the in-scope defects.** Four defects in the briefing workflow line of work
  that this contributor delivered (Feature-001, Feature-002) are fixed: B1, B2, B4 and the
  briefing-tool half of C3. B2 is the only High-severity defect in that scope; the other three
  are Medium and are fixed because they sit in the same code and each makes an advisor or tool
  see a misleading or unsafe result.
- **A regression verification for each fixed defect**, grouped and named by register ID, so a
  reviewer can trace each closed entry to the evidence that closed it.
- **A complete, honest defect record.** Every other finding — teammates' defects of any
  severity, this contributor's low-severity items, design decisions and unconfirmed suspicions —
  is documented in the register with owner, severity and action, and is not fixed here.

Feature-004 changes production behaviour only where a fix requires it, and only in files this
contributor owns. It changes no teammate's source, no merged verification artifact, and no
approved requirement of Feature-001, Feature-002 or Feature-003. Each fix restores behaviour an
approved specification already requires; Feature-004 adds no new capability.

## Backlog Alignment

| Backlog story | Owns | Feature-004's relationship |
|---|---|---|
| US-08 | Application backend | Delivered by Feature-001 (merged). B1 and C3 (Renny half) are fixed at its service, REST and tool-interface boundaries. |
| US-12 | Final briefing instructions | Not in Feature-004. The instructions half of Feature-001 SC-007 stays open (register DEC-9). |
| US-14 | Acceptance-criteria validation | Owned by Karen. D1–D6 are logged to her, unfixed. Feature-004 guards against D4's effect on the retry workflow (B2) without changing validation behaviour. |
| US-15 | Single retry and validated storage | Delivered by Feature-002 (merged). B2 and B4 are fixed against its approved requirements. |
| US-17 | Dashboard and broad application testing | Not in Feature-004. The five failing advisor-interface verifications (A1–A4 / C1) are logged to Karen. |
| US-18 | Briefing workflow testing | Delivered by Feature-003 (merged). Its verification is not re-run or edited, only kept passing. |
| **US-20** | Final defect resolution | **This feature**, for this contributor's scope. |
| US-19, US-21 – US-23 | Refinement, delivery, documentation, handover | Not in Feature-004. |

## Clarifications

### Session 2026-09-24 (confirmed Feature-004 scope decisions)

The following decisions were settled with the product owner after the defect sweep. They are
recorded as DEC-1 to DEC-9 in the defect register and are authoritative for this specification.

- Severity uses a four-level scale: Critical, High, Medium, Low. US-20's criterion is read as:
  close every Critical and High defect in scope, and document every lower-priority defect.
- Feature-004 fixes this contributor's own defects only. Teammates' defects are logged with
  owner and severity and left unfixed, in line with constitution Principle XVI.
- Fixed in Feature-004: B1, B2, B4, and C3 limited to the briefing tools. B2 is High; the sweep
  found no Critical defect.
- Logged only, not fixed: C7 (Low) and A9 (Low), both this contributor's.
- Not defects: C6 (error paths deliberately shown as errors) and the deliberately disabled
  small-group suppression. Both are recorded as design decisions.
- The five failing advisor-interface verifications are logged against their owner. They are not
  edited and not superseded.
- Regression verification goes in one new verification file only, one group per defect named
  after its register ID. Merged verification files are never edited.
- Done-gate for every fix: changed files are lint-clean, and the full verification suite shows
  exactly the five known advisor-interface failures and no others.

### Session 2026-09-24

- Q: Does Feature-004 complete US-20 while six High-severity defects owned by teammates (D1, D2,
  D3, A1–A4 / C1, A5, D7) remain open? → A: Yes, for this contributor's scope only. Feature-004
  completes US-20 for that scope, and the register names each open High defect and its owner.
  US-20 as a whole stays open until those defects are closed by their owners.
- Q: Is an unexpected error from the validation step on the first attempt in scope, as well as on
  the retry attempt? → A: Yes. On the first attempt it is treated as a validation failure and the
  request goes on to the single retry. On the retry attempt it becomes a terminal validation
  failure.
- Q: What does the advisor see when the store cannot be read during a briefing request? → A: The
  existing "store unavailable" wording that the stored-briefing retrieval path already uses. No new
  wording is introduced.
- Q: How does the governed store treat items in a student's storage location that it does not
  recognise as its own briefings? → A: It ignores them silently. They are not logged, reported,
  modified or removed.
- Q: What failure text do the briefing tools return when a backend dependency fails? → A: The same
  safe messages the equivalent REST endpoints already return for the same failure. No
  tool-specific wording is introduced.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The retry workflow always ends with an explicit outcome (Priority: P1)

An advisor who requests a briefing must always receive an explicit, accurate outcome. When the
validation step itself fails unexpectedly during the retry attempt, the request must end as a
terminal failure of the briefing, not as a misleading report that the data source is down.
(Register B2, High.)

**Why this priority**: B2 is the only High-severity defect in scope, so closing it is the minimum
Feature-004 needs to meet US-20's criterion. It breaks an approved guarantee (Feature-002 FR-005,
SC-002) and has a real trigger in the current validator (register D4).

**Independent Test**: With a controlled validation outcome that raises an unexpected error on the
retry attempt, a briefing request ends with exactly one explicit terminal failure, the terminal
outcome is recorded in the operational records, and nothing is stored.

**Acceptance Scenarios**:

1. **Given** a first attempt that fails validation, **When** the validation step raises an
   unexpected error on the retry attempt, **Then** the request ends with a terminal failure
   identifying validation as the failure kind, and nothing is stored.
2. **Given** the same case, **When** the outcome reaches the REST and tool-interface boundaries,
   **Then** it is reported as a briefing failure and never as a data-source outage.
3. **Given** the same case, **When** the operational records are inspected, **Then** exactly one
   terminal outcome is recorded, carrying metadata only.
4. **Given** the validation step raises an unexpected error on the first attempt, **When** the
   request continues, **Then** it is treated as a validation failure carrying no failed criteria
   or feedback, the single retry is attempted, and the request still ends with exactly one
   explicit outcome.
5. **Given** a configuration failure during the retry attempt, **When** the request completes,
   **Then** it is still surfaced unchanged, as Feature-002 requires.

---

### User Story 2 - A storage read outage is reported as what it is (Priority: P2)

When the validated-briefing store cannot be read, an advisor or tool that requests a briefing
must be told the store is unavailable. It must not be told that a briefing was generated but
could not be stored, because nothing was generated or written. (Register B1.)

**Why this priority**: The current message is false and would lead an advisor to believe a
briefing exists somewhere. It contradicts Feature-002's read-time edge case and its
evidence-based persistence reporting (FR-036, FR-038).

**Independent Test**: With a controlled store that fails on read, a non-regenerating briefing
request and the advisor-facing regenerate pre-check each surface a store-unavailable result, no
generation is attempted, and no "could not be stored" wording appears.

**Acceptance Scenarios**:

1. **Given** the store fails when checked for an existing briefing, **When** a briefing is
   requested without asking for a fresh one, **Then** an explicit store-unavailable failure is
   surfaced with the existing "store unavailable" wording, distinct from a failure to write, and
   no generation is attempted.
2. **Given** the same store failure, **When** the advisor starts a regeneration from the
   advisor-facing surface, **Then** the advisor is told, in the existing "store unavailable"
   wording, that the store is unavailable, not that a briefing was generated but not stored.
3. **Given** the store fails while writing a validated briefing, **When** the request completes,
   **Then** the existing "could not be stored" failure is still surfaced unchanged.

---

### User Story 3 - Unrelated files never hide a student's briefing (Priority: P3)

A stray file in a student's governed storage location must not be mistaken for a validated
briefing. Retrieval must keep returning the student's most-recent validated briefing, or the
"none available" result, as if the file were not there. (Register B4.)

**Why this priority**: One unrelated file currently blocks every retrieval for that student until
someone deletes it by hand, which breaks Feature-002 FR-022, FR-023 and SC-008. It is less
likely to occur than B1 or B2, so it ranks below them.

**Independent Test**: With controlled governed storage holding an unrelated file beside, or
instead of, a student's validated briefings, the store reports presence and returns the latest
briefing exactly as if the unrelated file were absent.

**Acceptance Scenarios**:

1. **Given** a student's storage location holds only an unrelated file, **When** presence is
   checked and the latest briefing is requested, **Then** the store reports no validated briefing
   and returns "none available".
2. **Given** a student's storage location holds validated briefings and an unrelated file that
   sorts after them, **When** the latest briefing is requested, **Then** the most-recent validated
   briefing is returned.
3. **Given** an unrelated file is present, **When** a new validated briefing is stored, **Then** it
   becomes the most-recent and the unrelated file is left untouched.

---

### User Story 4 - Briefing tools never leak internal error text (Priority: P4)

A tool client that requests or retrieves a briefing must receive a safe, generic failure when a
backend dependency fails, never internal storage locations or data-warehouse error text. The
REST boundary already behaves this way. (Register C3, briefing-tool half.)

**Why this priority**: It is a privacy and information-disclosure gap (constitution Principles X
and XI) at one boundary only, and the same failures are already safe at the REST boundary.

**Independent Test**: With controlled backend failures carrying recognisable internal text, each
briefing tool returns a safe failure whose message contains none of that text.

**Acceptance Scenarios**:

1. **Given** a storage failure carrying an internal storage path, **When** a briefing tool is
   called, **Then** the tool reports a safe storage failure and the path does not appear.
2. **Given** a data-source failure carrying internal error text, **When** a briefing tool is
   called, **Then** the tool reports a safe failure and the internal text does not appear.
3. **Given** the failures the briefing tools already map safely (unknown student, not at risk,
   configuration failure), **When** a briefing tool is called, **Then** their results are
   unchanged.

---

### User Story 5 - Every remaining defect is documented and traceable (Priority: P5)

A reviewer needs one place that shows every defect found, its owner and severity, what was done
about it, and the evidence for each one Feature-004 closed.

**Why this priority**: It is the second half of US-20's criterion ("remaining lower-priority
defects are documented") and turns the fixes into reviewable evidence. It has value only once the
fixes exist, so it comes last.

**Independent Test**: The defect register is inspected: every sweep finding appears once with
owner, severity, action and status; every defect fixed here is Closed and names its regression
group; every other entry stays Open with its owner.

**Acceptance Scenarios**:

1. **Given** the completed fixes, **When** the register is reviewed, **Then** B1, B2, B4 and C3
   (Renny half) are Closed and each names the regression group that verifies it.
2. **Given** a defect owned by a teammate, **When** the register is reviewed, **Then** it is listed
   with its owner and severity, marked as logged to its owner, and left unchanged in the source.
3. **Given** the full verification suite after all fixes, **When** it is run, **Then** it shows the
   baseline results plus the new regression verifications, with exactly the five known
   advisor-interface failures and no others.

---

### Edge Cases

- **A fix would require changing a teammate's file**: the change is not made. The dependency is
  recorded in the register against the owner. B2 is fixed at the retry boundary, not in the
  validator that triggers it (D4).
- **A fix would require changing a merged verification**: the change is not made. If a merged
  verification asserts the defective behaviour, that is raised as a decision for the product
  owner before the fix proceeds.
- **A regression verification would duplicate an existing one**: it is not added. Only the
  defective behaviour and its corrected result are verified.
- **A fix changes a known advisor-interface failure**: not expected, because those five failures
  have causes unrelated to B1–B4. If their count or identity changes, the done-gate fails.
- **The first-attempt validation step raises unexpectedly**: treated as a validation failure with
  no criteria or feedback, so the single retry runs (User Story 1, scenario 4).
- **An unconfirmed suspicion is reproduced during the work**: it is added to the register as a new
  entry with owner and severity. It is fixed here only if the product owner approves.
- **The register and the source disagree on a line number after a fix**: the register keeps the
  line numbers of the sweep commit it names. Fixes are traced by register ID, not by line.

## Requirements *(mandatory)*

### Functional Requirements

#### Scope and containment

- **FR-001**: Feature-004 MUST fix exactly the defects the register marks "Fix in Feature-004":
  B1, B2, B4 and C3 (Renny half).
- **FR-002**: Feature-004 MUST NOT change source owned by another contributor, including to fix a
  defect logged against them. Where a file is shared (the advisor-facing surface holds both B1
  and teammates' defects C8, A8), only the lines belonging to this contributor's defect MAY
  change.
- **FR-003**: Feature-004 MUST NOT change any merged verification artifact from Feature-001,
  Feature-002, Feature-003 or any teammate.
- **FR-004**: Feature-004 MUST NOT change any approved requirement of an earlier feature. Each fix
  MUST restore behaviour an approved specification already requires.
- **FR-005**: Feature-004 MUST NOT fix C7 or A9. They stay logged as Low.
- **FR-006**: Feature-004 MUST NOT change the behaviour recorded as design decisions (C6, DD-2).

#### B2 — retry workflow outcome (High)

- **FR-007**: When the validation step raises an unexpected error on the retry attempt, the retry
  workflow MUST end with a terminal failure identifying validation as the failure kind, and MUST
  NOT let the error pass its boundary (Feature-002 FR-005).
- **FR-008**: That terminal failure MUST be recorded in the operational records as exactly one
  metadata-only outcome, and nothing MUST be stored.
- **FR-009**: At the REST and tool-interface boundaries, that outcome MUST be reported as a
  briefing failure, never as a data-source outage.
- **FR-010**: An unexpected error from the validation step on the first attempt MUST be treated as
  a validation failure carrying no failed criteria and no feedback, and the request MUST go on to
  the single retry. If the retry attempt then fails, FR-007 applies.
- **FR-011**: A configuration failure MUST still be surfaced unchanged on either attempt.

#### B1 — read-time storage outage

- **FR-012**: A store failure while checking for an existing briefing MUST be surfaced as an
  explicit store-unavailable failure, distinct from a failure to write a validated briefing, using
  the same wording the stored-briefing retrieval path already uses for an unavailable store.
- **FR-013**: When that read failure occurs, no generation MUST be attempted and nothing MUST be
  stored.
- **FR-014**: The advisor-facing surface, for both a first request and the regenerate pre-check,
  MUST report a store read failure with the existing "store unavailable" wording, and MUST NOT say
  that a briefing was generated or could not be stored.
- **FR-015**: A failure while writing a validated briefing MUST still be surfaced as it is today.

#### B4 — unrelated files in governed storage

- **FR-016**: The governed store MUST treat as a stored validated briefing only an item that it
  wrote itself, recognised by its own naming convention.
- **FR-017**: Presence checks and latest-briefing retrieval MUST ignore every other item in a
  student's storage location.
- **FR-018**: The governed store MUST ignore unrecognised items silently: it MUST NOT log,
  report, modify or remove them.

#### C3 (Renny half) — briefing tool error text

- **FR-019**: The briefing tools at the tool interface MUST map storage failures and any other
  unexpected backend failure to the same safe message the equivalent REST endpoint returns for
  that failure.
- **FR-020**: No briefing tool failure MUST carry internal storage paths, data-warehouse error
  text or credentials.
- **FR-021**: Failures the briefing tools already map safely MUST keep their current results. No
  tool-specific failure wording MUST be introduced.
- **FR-022**: The profile and list tools (the other half of C3) MUST NOT be changed.

#### Regression verification and done-gate

- **FR-023**: Each fixed defect MUST have a regression verification group named after its
  register ID, all in one new verification file.
- **FR-024**: Each regression group MUST fail against the sweep commit and pass after the fix.
- **FR-025**: Regression verification MUST run with controlled outcomes and no access to any
  external service, workspace or network.
- **FR-026**: Regression verification MUST NOT duplicate behaviour already verified by an earlier
  feature.
- **FR-027**: Every file Feature-004 changes MUST be lint-clean.
- **FR-028**: After all fixes, the full verification suite MUST show exactly the five known
  advisor-interface failures (A1–A4 / C1) and no other failure.

#### Defect register

- **FR-029**: The register MUST list every sweep finding once, with ID, location, description,
  specification reference, severity, owner, action and status.
- **FR-030**: The register MUST record the baseline verification and lint results and the product
  owner's decisions.
- **FR-031**: On completion, each defect fixed by Feature-004 MUST be marked Closed with the name of
  its regression group. Every other entry MUST stay Open with its owner.
- **FR-032**: The register MUST state which High-severity defects remain open and who owns each,
  and MUST record that Feature-004 completes US-20 for this contributor's scope only; US-20 as a
  whole stays open until those defects are closed.

### Key Entities

- **Defect**: A mismatch between approved or expected behaviour and delivered behaviour. Carries a
  register ID, location, description, specification reference, severity, owner, action and
  status.
- **Defect register**: The list of all defects found by the US-20 sweep, with the baseline results
  and decisions. The single source of truth for US-20.
- **Regression group**: The verifications that show one defect's corrected behaviour, named after
  its register ID.
- **Design decision**: A finding the product owner has ruled deliberate. Recorded so it is not
  re-reported as a defect.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of defects marked "Fix in Feature-004" (4 of 4) are Closed, each with a passing
  regression group.
- **SC-002**: 100% of Critical and High defects in this contributor's scope are Closed (B2; no
  Critical was found). The six High defects owned by teammates are listed as open with their
  owners; US-20 as a whole is not reported complete while any of them remains open.
- **SC-003**: 100% of sweep findings appear in the register with owner, severity and action; 0
  findings are missing.
- **SC-004**: 0 teammate source files and 0 merged verification artifacts are changed.
- **SC-005**: 100% of briefing requests in which the validation step raises unexpectedly end with
  exactly one explicit outcome; 0 are reported as a data-source outage.
- **SC-006**: 0 store-read failures are reported as a failure to store a generated briefing.
- **SC-007**: 0 unrelated files in a student's storage location change what retrieval returns.
- **SC-008**: 0 briefing-tool failures expose internal storage paths or data-warehouse error text.
- **SC-009**: The full verification suite shows exactly 5 failures, all the known advisor-interface
  ones; every pre-existing passing verification still passes.
- **SC-010**: 0 lint errors in files changed by Feature-004.
- **SC-011**: 100% of regression verifications run with no external service, workspace or network.

## Assumptions

- The defect register reflects the sweep at commit `3181882`. Line numbers are as of that commit.
- Severity ratings in the register are final (DEC-1, DEC-3). Medium defects B1, B4 and C3 are fixed
  because the product owner chose to, not because US-20's criterion requires it.
- "Closed" means fixed with a passing regression group. It does not require closing a GitHub issue.
- B2 is fixed at the retry boundary. D4, which triggers it, stays with its owner; after the fix,
  D4 produces a terminal validation failure instead of a misleading outage.
- The failure category, wording and status code for each corrected outcome reuse the application's
  existing failure types and safe messages; no new failure type is introduced unless planning
  shows none fits.
- Controlled generation, validation and storage outcomes from earlier features are the approved
  verification approach and are reused.
- The five failing advisor-interface verifications fail for reasons unrelated to B1–B4, so fixing
  B1 at the advisor-facing surface does not change them.

## Dependencies

- **Feature-001 (US-08)** and **Feature-002 (US-15)** — merged. Their approved specifications
  define the behaviour B1, B2, B4 and C3 restore.
- **Feature-003 (US-18)** — merged. Its verification must keep passing.
- **The defect register** in this directory — the defect list US-20's criterion names.
- **Teammates' work** — Karen (US-14 validation, advisor-interface verification) and GuaGuaGua88
  (configuration, data access, advisor-interface layout) own the logged defects. Their resolution
  is outside Feature-004. Feature-004 completes US-20 for this contributor's scope only; US-20 as
  a whole stays open until the six open High defects are closed by their owners.

## Out of Scope

- Any defect owned by a teammate, whatever its severity: D1–D10, A1–A5, A8, A10, C1, C3 (profile
  and list tools), C4, C8.
- This contributor's Low defects C7 and A9, which are logged only.
- Design decisions C6 and DD-2.
- Unconfirmed suspicions U1–U8, unless one is reproduced and the product owner approves a fix.
- Third-party deprecation warnings (A11).
- Feature-001 SC-007's instructions half (US-12).
- Any edit to a merged verification artifact, including the five failing advisor-interface
  verifications.
- New capability, refactoring or cleanup beyond what a fix requires.
