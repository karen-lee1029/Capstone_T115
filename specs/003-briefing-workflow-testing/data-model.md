# Phase 1 Data Model: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Date**: 2026-09-16 | **Plan**: [plan.md](./plan.md)

Feature-003 introduces **no production type and no persisted data**. Every application type it
exchanges already exists in `models.py` and is used unchanged. What follows are the verification-
side entities the specification named, expressed as the shapes the scenarios actually pass around.

---

## Existing application types used unchanged (read-only)

| Type | Role in Feature-003 scenarios |
|---|---|
| `StudentPrediction` | Fixture input; source of the risk fields carried into a validated briefing |
| `ApprovedModelFeatureValues` | Assembled by the service; never asserted on for content |
| `BriefingGenerationContext` | The value a controlled generation outcome receives; its composed prompt is what the prompt-aware double inspects and what retry-feedback assertions examine |
| `DraftBriefing` | What a controlled generation outcome returns. Its text field carries no length constraint, which is the subject of the recorded defect |
| `ValidationOutcome` | What a controlled validation outcome returns: pass flag, failed criteria, feedback, validator identifier |
| `ValidatedBriefing` | The only briefing form a store accepts; subject of write-count and valid-only assertions |
| `GenerationFailed` / `ValidationFailed` | First-attempt outcome handed to the retry boundary |
| `Produced` / `TerminalFailure` | Retry outcome; the basis of terminal-category assertions |
| `StudentNotFoundError`, `StudentNotAtRiskError`, `BriefingNotProducedError`, `BriefingStorageError`, `ConfigurationError` | The error taxonomy whose mapping is verified at each boundary |
| `Settings` | Constructed directly in scenarios to carry a briefing volume for governed-store parity |

**None of these is modified, extended or subclassed by Feature-003.**

---

## Verification-side entities

### Workflow scenario

One complete briefing request from a defined starting state to exactly one explicit outcome.

| Attribute | Description |
|---|---|
| Starting state | Which fixture student, and whether a validated briefing is already stored |
| Request kind | Briefing request, explicit regeneration, or stored-briefing retrieval |
| Controlled outcomes | The ordered generation and validation results that drive the attempt(s) |
| Store under test | The default in-memory store, or the governed store backed by a controlled files client |
| Expected outcome | The validated briefing or the explicit failure the specification requires |
| Expected write count | How many times a validated briefing should be written — 0 or 1 |
| Boundary | Application service, REST, or tool interface |
| Traces to | The requirement, success criterion and backlog story it satisfies |

**Lifecycle**: a scenario reaches exactly one terminal outcome. There is no partial or ambiguous
end state; FR-022 exists to verify precisely that.

### Controlled outcome

A predetermined result supplied at the generation or validation boundary in place of an
implementation that does not yet exist.

| Attribute | Description |
|---|---|
| Boundary | Generation or validation |
| Kind | Generation: produced draft, retryable failure, or configuration failure. Validation: pass, or failure |
| Sequence position | Which attempt consumes it; over-consumption is an error, which is how "no third attempt" stays provable |
| Reported criteria | Visibly synthetic placeholders only, present or absent |
| Reported feedback | Present or absent |
| Validator identifier | A scenario-specific value, so its flow into the validated briefing and the operational record is observable |

**Constraint (FR-010)**: reported criteria are always visibly synthetic. No value may read as
approved US-14 content.

### Seam call record

The ordered list of boundary engagements produced during one scenario.

| Attribute | Description |
|---|---|
| Sequence | Boundary engagements in the order they occurred, across all boundaries |
| Entry | Which boundary, and which attempt it belonged to |

**Constraint (FR-026)**: a generation entry appears at most twice in any single scenario.

### Traceability record

The review artifact connecting verification to requirements, and the aggregate of what remains
unverified. Its structure is defined in
[contracts/traceability-record.md](./contracts/traceability-record.md).

| Section | Contents |
|---|---|
| Scenario map | Each scenario to its requirement, success criterion and backlog story |
| Tracked re-verification | Existing Feature-001 verifications satisfying cross-boundary coverage |
| Recorded defects | Outstanding ones aggregated from their expected-fail annotations; resolved ones retained with their resolution |
| Unverified criteria | Approved criteria in scope not verified, each with its reason |

**Constraint (FR-040)**: every verification name the record cites must resolve.

### Recorded defect

A mismatch between approved specified behaviour and delivered behaviour.

| Attribute | Description |
|---|---|
| Specified behaviour | What the approved specification requires, and where it says so |
| Delivered behaviour | What the implementation currently does |
| Carrier | The expected-fail verification holding it while outstanding — the authoritative record |
| Resolution | How and where it was fixed, once resolved |
| Owner | The story that will resolve it; never Feature-003 |

**Lifecycle**: while the mismatch exists, the carrier reports as expected-fail. When it is
resolved elsewhere, the carrier reports an unexpected pass and fails, which forces the record to
be updated rather than drifting — the expectation is then removed and the scenario kept as an
ordinary verification. **One defect was found during planning and has been resolved**: briefing
content with no substance — empty or whitespace only — was returned as validated and stored,
against Feature-002's specified treatment of it as a generation failure. The generation boundary
now rejects it, so FR-035 verifies that behaviour ordinarily and the record retains the defect
with its resolution.

---

## Fixture data

Supplied entirely by the existing mock repository. No fixture data is introduced.

| Fixture | Properties | Used for |
|---|---|---|
| `synthetic-student-001` | Flagged at risk, 78.5% | Generation, retry, storage and failure scenarios |
| `synthetic-student-002` | Not flagged, 18% | The refusal outcome |
| `synthetic-student-003` | Used with a seeded stored briefing | Get-or-create, regeneration, preservation and retrieval |
| An unknown hash | Absent from the repository | The not-found outcome |

All identifiers are deidentified synthetic values already present in the repository, consistent
with Principle X.
