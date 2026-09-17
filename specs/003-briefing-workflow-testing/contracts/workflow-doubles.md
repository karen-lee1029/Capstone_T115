# Contract: Feature-003 controlled outcomes and recorders (`tests/workflow_doubles.py`)

**Plan**: [plan.md](../plan.md) | **Research**: [R1](../research.md), [R2](../research.md),
[R3](../research.md)

The support module Feature-003 adds. It **extends** the existing `tests/doubles.py` convention and
changes nothing in it. Every item here satisfies an existing boundary protocol in `ports.py`; no
new protocol, base class or abstraction is introduced.

## Reused unchanged from `tests/doubles.py` (read-only)

| Item | Surface | Why reused |
|---|---|---|
| `ScriptedGenerationProvider` | Ordered draft-or-raise actions, one consumed per generation call; over-call is an error | Already the established way to drive attempt sequences, and its over-call error is how "no third attempt" stays provable |
| `ScriptedValidator` | Ordered validation outcomes, one consumed per call | Already the established way to drive pass/fail sequences |
| `FakeFilesClient` | In-memory upload / download / list surface, raising the real not-found error | Already the established way to exercise the governed store offline |

Feature-003 imports these. It does not copy, wrap-and-replace, or modify them.

## Added by Feature-003

### Prompt-aware generation double

Satisfies the `GenerationProvider` protocol.

- Returns a draft whose content depends on whether the received composed prompt carries the retry
  revision block, so a second attempt succeeds **only if** feedback propagated (research R3).
- Records every context it received, so identity fields — student hash, prediction, features,
  instructions provenance — can be asserted as preserved across the retry request.
- Returned text is deterministic and visibly synthetic, so a fixture briefing can never be
  mistaken for a real one in a record or a stored document.

**Guarantees**: performs no network or workspace access; raises nothing unless scripted to.

### Seam call recorder

Thin wrappers around the generation, validation, retry and store boundaries, injected through the
existing `StudentService` constructor.

- All wrappers append to **one shared ordered list**, preserving relative order across boundaries.
  This is the only mechanism in the repository that makes FR-023's call order observable.
- Each entry names the boundary engaged and the attempt it belonged to.
- Wrappers delegate to the wrapped boundary unchanged and alter no behaviour or return value.

**Guarantees**: observation only; no production module is patched or monkeypatched.

### Write-counting store wrapper

Satisfies the `BriefingStore` protocol by delegating to a real store.

- Counts writes of a validated briefing, so every outcome can assert an exact expected count
  rather than only a final state.
- Wraps either the in-memory store or the governed store, so the same assertions hold for the
  governed-storage parity scenarios.
- A variant raises the existing storage error on write, for the storage-failure outcome.

**Note**: Feature-002 has a file-local equivalent. It is not imported or modified — it belongs to
a read-only file under approved decision H3, so an equivalent is provided here.

### Synthetic criteria constants

Visibly synthetic acceptance-criteria values used wherever a controlled validation outcome reports
failed criteria.

**Constraint (FR-010)**: no value may read as plausible approved US-14 content. Values are
recognisably placeholders so that a fixture can never be cited later as an approved criterion.

## Composition helper

A single helper assembles a `StudentService` from a scenario's controlled outcomes, chosen store
and optional recorder, and optionally exposes it through the REST or tool boundary. Assembly uses
the existing public constructors only.

**Constraint**: the same generation and validation instances are passed to the service and to the
retry workflow, matching how the composition root wires them, so a scripted sequence is consumed
across both attempts exactly as it is in the delivered application.

## Prohibited

- Modifying `tests/doubles.py` or any other existing verification file.
- Patching, monkeypatching or otherwise altering any production module.
- Introducing a `conftest.py`, plugin, fixture framework or base class (research R1, R10).
- Any network, workspace, credential or filesystem access beyond reading repository files for the
  traceability self-check.
