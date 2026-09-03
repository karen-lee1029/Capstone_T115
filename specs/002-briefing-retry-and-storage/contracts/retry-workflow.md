# Contract: `SingleRetryWorkflow` (Feature-002 / US-15)

Concrete implementation of the Feature-001 `ports.RetryWorkflow` protocol. **No signature
change** to the protocol, `models.py`, `ports.py`, or `StudentService`. See Feature-001
`contracts/internal-seams.md` for the boundary definition.

```
run(context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome) -> BriefingOutcome
```

## Construction

`SingleRetryWorkflow(generation_provider: GenerationProvider, validator: BriefingValidator)` —
wired in `main.build_service` with the **same instances** given to `StudentService`, so the
US-13 generation and US-14 validation implementations are used by the retry with no extra
wiring (spec FR-034).

## Guarantees

- `generation_provider.generate` is called **exactly once** per `run`; `validator.validate` is
  called **at most once**. No loop, no recursion — a third generation attempt is structurally
  impossible (FR-002, SC-001).
- `run` returns a `BriefingOutcome` for every input and never raises, **except** it re-raises a
  `ConfigurationError` from the attempt-2 `generate` unchanged (FR-005, R4).
- The attempt-2 request preserves the original `student_deidentified_hash`, `prediction`,
  `features`, and `instructions_id` (FR-006). Nothing is fabricated (FR-008, FR-010).
- A `Produced` briefing has `attempt_count == 2`, `source == "generated"`,
  `validator_id` from the attempt-2 `ValidationOutcome`, and prediction-derived fields from
  `context.prediction` (FR-014, R3).
- `run` never persists anything — persistence stays in `StudentService._hand_off_to_retry`
  (FR-019).

## Attempt-2 request construction

`_retry_context(context, first_outcome)` returns
`context.model_copy(update={"composed_prompt": P})`:

| `first_outcome` | `P` |
|---|---|
| `ValidationFailed(outcome)` with `outcome.failed_criteria` **or** `outcome.feedback` non-empty | `context.composed_prompt` + a fixed delimited revision-feedback block containing the failed-criteria list and the feedback text, verbatim |
| `ValidationFailed(outcome)` with empty `failed_criteria` **and** `feedback is None` | `context.composed_prompt` unchanged |
| `GenerationFailed(_)` | `context.composed_prompt` unchanged |

The revision-feedback block is a minimal Feature-002 constant that only relays what the
validator returned. Per approved planning decision 3 (2026-09-03) it introduces no substantive
new briefing instructions, does not duplicate the US-12 prompt design, carries no US-14 criteria
of its own, and is a single replaceable constant so the final US-12 instructions supersede it
without changing `run`.

## Outcome matrix

| First-attempt outcome | Attempt-2 generation | Attempt-2 validation | `run` returns | `StudentService` result |
|---|---|---|---|---|
| `ValidationFailed` | returns a draft | `passed` | `Produced(ValidatedBriefing(attempt_count=2))` | persisted; `ValidatedBriefing` (200) |
| `ValidationFailed` | returns a draft | not `passed` | `TerminalFailure("validation")` | `BriefingNotProducedError("validation")` → 502 |
| `ValidationFailed` | raises non-`ConfigurationError` | — | `TerminalFailure("generation")` | `BriefingNotProducedError("generation")` → 502 |
| `GenerationFailed` | returns a draft | `passed` | `Produced(ValidatedBriefing(attempt_count=2))` | persisted; `ValidatedBriefing` (200) |
| `GenerationFailed` | returns a draft | not `passed` | `TerminalFailure("validation")` | `BriefingNotProducedError("validation")` → 502 |
| `GenerationFailed` | raises non-`ConfigurationError` | — | `TerminalFailure("generation")` | `BriefingNotProducedError("generation")` → 502 |
| either | raises `ConfigurationError` | — | re-raises `ConfigurationError` | existing `ConfigurationError` handler → 503 |

On any `TerminalFailure` or propagated `ConfigurationError`: no briefing is stored, and a
previously stored validated briefing for the student is left untouched (FR-016–FR-018;
Feature-001 `_hand_off_to_retry` / `_persist`).

## Retained placeholder

`RetryNotConfigured` stays in `retry_workflow.py` as the "retry disabled" passthrough
(`run` → `TerminalFailure(first_outcome.category)`), used by Feature-001 orchestration tests and
available as a wiring option. `main.build_service` uses `SingleRetryWorkflow`.
