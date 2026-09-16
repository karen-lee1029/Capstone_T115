# Contract: the traceability record (`specs/003-briefing-workflow-testing/traceability.md`)

**Plan**: [plan.md](../plan.md) | **Research**: [R6](../research.md)

Feature-003's review artifact, required by FR-038 through FR-041. Hand-maintained, per the
approved clarification, and self-checked so it cannot drift silently — the failure mode
Feature-001's equivalent table demonstrated, where five cited verification names no longer
resolve.

## Location

In the feature folder beside the specification, because it is a review artifact rather than
verification code. Its self-check resolves the path from the repository root.

## Required sections

### 1. Scenario map

Each Feature-003 scenario against what it satisfies.

| Column | Contents |
|---|---|
| Scenario | The verification that carries it, identified by file and name |
| Satisfies | Requirement identifiers, success-criterion identifiers, and the backlog story |

**Constraint (FR-038)**: every Feature-003 scenario appears exactly once.

### 2. Tracked re-verification

Existing verifications that satisfy Feature-003 requirements without being re-implemented — the
mechanism the approved clarification chose for cross-boundary coverage.

| Column | Contents |
|---|---|
| Outcome | The briefing outcome and the boundary it is observed at |
| Satisfied by | The existing Feature-001 verification, by file and name |
| Feature-003 requirement | Which requirement this coverage satisfies |

**Constraint (FR-032)**: entries here are tracked, never re-implemented. Cited names are subject
to the same resolution check as everything else, so this section is what makes the dependency on
Feature-001's verification visible rather than hidden.

### 3. Recorded defects

Aggregated from the expected-fail annotations, which remain the authoritative record.

| Column | Contents |
|---|---|
| Defect | The mismatch, in one line |
| Specified behaviour | What the approved specification requires, and where |
| Delivered behaviour | What the implementation currently does |
| Carrier | The expected-fail verification holding it |
| Owner | The story that will resolve it — never Feature-003 |

**Constraint (FR-036)**: every entry names a carrier. A defect recorded here with no carrying
verification does not satisfy the requirement.

**Known at planning time**: briefing content with no substance — empty or whitespace-only — is
returned as validated and stored, against Feature-002's specified treatment of it as a generation
failure.

### 4. Unverified criteria

Approved criteria within Feature-003's scope that it does not verify, each with its reason.

| Column | Contents |
|---|---|
| Criterion | The criterion identifier and its owning feature |
| Reason | Why it is not verified |

**Constraint (FR-041)**: the reason is specific. "Out of scope" alone is insufficient.

**Known at planning time**: Feature-001 SC-007, because the US-12 and US-14 work is expected to be
delivered outside the seam boundary, so the substitution that criterion describes is not
anticipated during Feature-003 (FR-038).

## Self-check contract

A verification in `tests/test_briefing_workflow_traceability.py`:

1. Reads the record.
2. Extracts every cited verification name, from all sections including tracked re-verification.
3. Resolves each against the verification files' syntax trees.
4. Fails, naming the unresolved entries, if any cited name no longer exists.

**Guarantees**: reads repository files only; needs no runtime hook, no runner internals and no new
dependency, so it is independent of how the suite is invoked (research R6).

**Deliberate consequence**: if a Feature-001 verification cited under tracked re-verification is
later renamed or removed, this check fails. That is intended — it is the early warning that
Feature-003's cross-boundary coverage has lapsed. The correct response is to update Feature-003's
record, never to edit the Feature-001 file, which remains read-only under approved decision H3.

## Prohibited

- Generating the record automatically; the approved clarification settled on hand-maintained.
- Recording a defect with no carrying verification.
- Citing a verification name that does not resolve.
- Editing any Feature-001 or Feature-002 file to make a citation resolve.
