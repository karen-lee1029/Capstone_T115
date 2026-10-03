# Contract: Persistence Confirmation (Feature-002 / US-15, amendment 2026-09-22)

Covers spec User Story 4 and FR-035–FR-041. It defines **how a successful briefing result
reports that it was saved**. It changes no generation, validation, retry or storage behaviour:
a briefing is saved on exactly the same runs as before this amendment, and no protocol in
`ports.py` changes.

## The signal

```
ValidatedBriefing.storage_confirmed: bool = False
```

*The validated-briefing store has confirmed it holds this briefing.*

It is a property of **storage**, not of the generation attempt. It is therefore identical for a
briefing produced by Attempt 1 and one produced by Attempt 2, and carries no retry indication
(FR-040, FR-032).

## Who may set it

| Component | May set `storage_confirmed`? |
|---|---|
| `StudentService._persist` | **Yes** — to `True`, only after `store.save_validated(...)` has returned (FR-035, FR-036) |
| `StudentService` retrieval paths | **Yes** — to `True`, because the briefing was read out of the store (FR-037) |
| `SingleRetryWorkflow` | No — a producer cannot confirm its own persistence |
| `make_validated_briefing` | No — constructs with the `False` default |
| `VolumeBriefingStore` / `InMemoryBriefingStore` | No — the store reports success or raises; the service records the confirmation |

This is the same division the feature already uses for `source`: the producer sets
`source="generated"`, and `StudentService` restamps `source="stored"` on the retrieval path.

## Outcome table

| Run | Result | `storage_confirmed` |
|---|---|---|
| Attempt 1 passes validation, save succeeds | `ValidatedBriefing`, `attempt_count=1` | `True` |
| Attempt 2 passes validation, save succeeds | `ValidatedBriefing`, `attempt_count=2` | `True` |
| Briefing produced, `save_validated` raises | `BriefingStorageError` → 503 | *no result returned* — no confirmation can escape (FR-036) |
| Terminal failure after Attempt 2 | `BriefingNotProducedError` → 502 | *no result returned* |
| `regenerate=False` and a briefing is already stored | the stored briefing, `source="stored"` | `True` (FR-037) |
| `GET` retrieval / MCP `get_student_briefing` | the stored briefing, `source="stored"` | `True` (FR-037) |
| No briefing stored | "none available" → 404 | *no result returned* |

Because `_persist` raises on failure, the confirmed value is only ever constructed on the line
**after** a successful save. A confirmation therefore cannot be reported optimistically.

## Serialisation

The briefing handed to `save_validated` carries `storage_confirmed=False` — at that instant the
save is not yet confirmed — so the stored JSON document records `False`. That is the correct
pre-confirmation snapshot. The retrieval path restamps it to `True`, exactly as it already
restamps `source`. A document written before this amendment, which has no such key at all, still
parses: the field is defaulted.

## Application surfaces

- **REST**: no change. `ValidatedBriefing` is already the `response_model` for both briefing
  endpoints, so the field ships automatically. No new endpoint, no new response type (FR-035).
- **MCP**: no change. Both briefing tools already return `ValidatedBriefing.model_dump(mode="json")`.
- **Logging**: `_log_outcome` gains an optional boolean `stored` field on the existing
  metadata-only line. No prompt, briefing text or secret (FR-033).

## Advisor-facing confirmation

`briefing_messages.storage_confirmation_message(*, replaced: bool) -> str`

| `replaced` | Reports |
|---|---|
| `False` | the briefing passed validation and has been saved to the validated briefing store |
| `True` | the same, and that it has replaced the previously saved briefing (FR-039) |

Requirements on the copy:

- It MUST mention that the briefing passed validation and that it has been saved (FR-038).
- It MUST be store-neutral — no "Unity Catalog", "Volume" or "in-memory" — because the
  in-memory store remains the local and test implementation (FR-041).
- It MUST NOT mention attempts, retries or attempt counts (FR-032, FR-040).
- It MUST NOT be shown when the request raised any error, including the storage error (FR-038).

`ui.request_briefing` determines `replaced` without an extra store read on the common path:

| Request | Derivation |
|---|---|
| `regenerate=False`, result `source == "stored"` | nothing was generated or saved — report the briefing as already saved, not newly saved |
| `regenerate=False`, result `source == "generated"` | the service generates here only when the student had none ⇒ first save |
| `regenerate=True` | resolved by one `service.has_stored_briefing(hash)` call before regenerating |

`StudentService.has_stored_briefing(student_hash) -> bool` is a one-line public delegation to
`store.has_validated`, so the UI asks the service rather than reaching into the store.

## FR-032 correction

The advisor-facing briefing metadata line shipped rendering `Attempt: {attempt_count}`, contrary
to FR-032. This amendment removes that rendering. `attempt_count` remains unchanged in the
`ValidatedBriefing` model, the REST and MCP responses, the stored document and the workflow log
lines — it simply stops being advisor-facing (SC-016).
