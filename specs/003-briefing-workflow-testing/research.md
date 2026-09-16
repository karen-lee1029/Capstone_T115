# Phase 0 Research: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Date**: 2026-09-16 | **Plan**: [plan.md](./plan.md)

The approved specification deliberately deferred implementation-level choices to planning. This
document resolves each one against the delivered repository. There were no `NEEDS CLARIFICATION`
markers in the specification to resolve; both were settled during the clarification passes.

---

## R1 — Where support code lives, and whether to introduce a shared configuration file

**Decision**: A plain importable module at `tests/workflow_doubles.py`. **No `conftest.py`.**

**Rationale**: `tests/doubles.py` already proves the pattern works in this repository — three
existing verification files import it by bare module name, because pytest places the tests
directory on the import path when no package marker is present. A `conftest.py` would apply
implicitly to all 84 existing verifications. Since approved decision H3 forbids disturbing
Feature-001 and Feature-002 verification files, a mechanism that could silently change their
behaviour is the wrong tool even though it would not edit them textually.

**Alternatives considered**: A `conftest.py` with shared fixtures — rejected for the implicit
reach described above. A test package with `__init__.py` — rejected because it would change how
every existing verification file is imported. Extending `doubles.py` in place — rejected outright;
it is a Feature-002 artifact and is read-only under H3.

---

## R2 — How boundary call *order* is observed

**Decision**: Thin recording wrappers around the generation, validation, retry and store
boundaries, each appending an entry to one shared ordered list, injected through the existing
`StudentService` constructor.

**Rationale**: The service already accepts every boundary as a constructor argument, so recording
requires nothing from the production code. A single shared list preserves relative order across
boundaries, which is the property FR-023 requires; per-double counters cannot express it. Every
existing verification asserts counts or outcomes, so ordering is genuinely unverified today.

**Alternatives considered**: Patching or monkeypatching production modules — rejected as an
indirect modification of production behaviour and unnecessary given constructor injection. Reading
the emitted operational records to infer order — rejected because those records are deliberately
metadata-only and do not capture boundary entry.

---

## R3 — How feedback propagation into the retry request is proven

**Decision**: A prompt-aware generation double whose returned draft depends on whether the
received composed prompt carries the retry revision block.

**Rationale**: Asserting that the retry prompt contains a substring proves the text was appended.
Making the second attempt's *success* conditional on the block's presence proves the request
actually reached the generation boundary carrying it, which is the behaviour FR-024 describes. It
also reproduces the behavioural shape of a model responding to revision feedback without any model
being involved, which keeps the scenario meaningful when US-13 later replaces the double.

**Alternatives considered**: Substring assertions alone — kept as a complement for the verbatim
requirement, but insufficient on their own. Recording the received context and asserting on it
afterwards — used for the identity-field checks, but it does not demonstrate that the content
influenced the attempt.

---

## R4 — How the governed store is exercised at workflow level

**Decision**: Compose the workflow against `VolumeBriefingStore`, constructed with a `Settings`
value carrying a briefing volume and with the existing `FakeFilesClient` injected. Re-run the six
storage-decision outcomes only.

**Rationale**: Both injection points are already public — the store accepts a files client
parameter specifically so it can be exercised without a workspace, and `Settings` is a plain
frozen dataclass that can be constructed directly. No production change and no environment
variable manipulation is required. The six-outcome scope is the approved clarification: outcomes
that never read or write storage cannot vary by store, and re-running them would add verification
beyond the approved criteria, which Principle XII forbids.

**Alternatives considered**: Setting the briefing-volume environment variable and building the
service through the composition root — rejected as unnecessary global state for no added
assurance. Re-running every scenario against both stores — rejected by the approved clarification.
Re-verifying the store contract itself — rejected because Feature-002 already covers it, so under
H3 it is complete.

---

## R5 — How the blank-content expectation is recorded

**Decision**: One expected-fail verification asserting the **specified** behaviour, marked strict,
with the defect described in its annotation. Covers both empty and whitespace-only content.

**Rationale**: Asserting current behaviour would enshrine a defect as correct. Asserting the
specified behaviour without an expectation marker would fail the suite for a known, accepted gap.
A strict expectation does neither: it records what the approved specification requires, passes the
suite while the gap exists, and **fails loudly if the gap is ever closed**, forcing the record to
be updated instead of drifting. That matches the specification's edge case for this situation.

Planning confirmed empirically that both empty and whitespace-only content currently produce a
briefing returned as validated and written to storage, so covering whitespace alongside empty is
not speculative — Feature-002's edge case mentions only empty content, and whitespace is a second
instance of the same mismatch.

**Alternatives considered**: A non-strict expectation — rejected because an unexpected pass would
be silent, which is the exact failure mode this feature exists to prevent. A prose-only defect
note with no verification — rejected by the approved clarification, which requires the annotation
to be the authoritative record.

---

## R6 — How the traceability record checks itself

**Decision**: Parse the record for cited verification names, then resolve each against the
verification files' syntax trees.

**Rationale**: Feature-001's traceability table cites five verification names and none still
resolves — drift is a demonstrated failure here, not a hypothetical one. Reading the source
syntax tree makes the check independent of how the suite is invoked and avoids depending on runner
internals. It is a few lines and needs no new dependency.

**Alternatives considered**: Generating the record from the verifications — rejected as
unnecessary tooling for a document of this size, and the approved clarification settled on
hand-maintained. Collecting names through the test runner's own machinery — rejected as coupling
to runner internals. Manual review — rejected; it is precisely what failed in Feature-001.

---

## R7 — How the SC-006 time budget is measured

**Decision**: Measure elapsed time around the three non-generation request paths — unknown
student, not-flagged student, and a get-or-create request returning an existing briefing — against
the mock repository and in-memory store, asserting the one-second budget the criterion states.

**Rationale**: Those conditions are the ones Feature-001 SC-006 itself names, so the verification
closes the criterion as written rather than inventing a new threshold. These paths perform only
in-memory work, so the headroom against a one-second budget is several orders of magnitude and the
verification is not load-sensitive. No repetition count, warm-up or statistical treatment is
warranted at that margin.

**Alternatives considered**: A benchmarking plugin — rejected as new infrastructure for a single
assertion. A tighter threshold — rejected as inventing a requirement the criterion does not state.
Repeated sampling with a percentile — rejected as disproportionate given the headroom.

---

## R8 — Which cross-boundary scenarios are genuinely new

**Decision**: Track the REST boundary's existing coverage as re-verification. Add new verification
only for the three uncovered tool-interface outcomes: terminal failure, storage failure, and
configuration failure.

**Rationale**: Planning inventoried both boundaries against the outcome matrix. The REST boundary
is comprehensively covered by Feature-001 — success, configuration failure, not-flagged, unknown
student, get-or-create with regeneration, terminal failure with its category, storage failure and
stored-briefing retrieval including the none-available result. Re-verifying any of it would breach
both H3 and Principle XII. The tool interface covers registration, get-or-create with
regeneration, two error messages and stored retrieval, leaving three outcomes whose observable
result at that boundary nothing asserts. Those are exactly what FR-033 describes.

**Alternatives considered**: Re-verifying every outcome at all three boundaries — rejected by the
approved clarification. Skipping the tool boundary entirely — rejected because three outcomes
produce a distinct observable result there that no verification covers, which FR-033 requires.

---

## R9 — Async scenarios at the tool boundary

**Decision**: Use the same async marker the existing tool-interface verifications use; introduce
no configuration.

**Rationale**: The existing tool verifications run today with no `conftest.py` and no async mode
setting in project configuration — the async plugin's default backend fixture resolves on its own,
visible in the suite output where those scenarios are parameterised by backend. Matching that
pattern keeps R1's no-shared-configuration decision intact.

**Alternatives considered**: Adding an async mode setting to project configuration — rejected as
an unnecessary change to a shared file that affects existing verifications.

---

## R10 — File granularity

**Decision**: Five verification files, one per specification concern, plus one support module.

**Rationale**: One file per user story, with the cross-cutting boundary and observability
requirements in a fifth, lets a reviewer locate the evidence for any requirement without
searching, and matches the existing convention of topic-named verification files. Fewer, larger
files would obscure that mapping; more files would fragment closely related scenarios.

**Alternatives considered**: A single large file — rejected as unreviewable and contrary to the
existing convention. One file per requirement group — rejected as fragmentation without benefit.
