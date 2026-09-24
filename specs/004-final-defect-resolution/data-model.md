# Data Model: Feature-004 — Final Defect Resolution (US-20)

**Date**: 2026-09-24 | **Plan**: [plan.md](./plan.md)

Feature-004 adds no persisted data and changes no model field. Two small additions and one
recognition rule:

## BriefingStoreUnavailableError (new exception, B1)

- **Where**: `student_service.py`, beside `BriefingStorageError`.
- **Is-a**: `BriefingStorageError` (so existing handlers still catch it).
- **Meaning**: the validated-briefing store could not be **read** (presence check or latest
  retrieval) during a briefing request. Nothing was generated or written.
- **Raised by**: `StudentService.request_briefing` (read before generation) and
  `StudentService.has_stored_briefing`.
- **Not raised by**: `_persist` — a **write** failure stays a plain `BriefingStorageError`.

## Synthetic failed ValidationOutcome (B2, Attempt 1)

- `ValidationOutcome(passed=False, failed_criteria=[], feedback=None, validator_id=<validator's id or "unavailable">)`
- Used only to hand an Attempt-1 validator exception to the retry as `ValidationFailed`. Carries
  no criteria or feedback, so the retry prompt is unchanged (Feature-002 FR-010). Never stored.

## Stored briefing file name (B4, recognition rule only)

`<YYYYMMDD>T<HHMMSSffffff>Z-attempt<n>-<6 lowercase hex>.json` under
`${BRIEFING_VOLUME}/<student_hash>/`. Unchanged from Feature-002; Feature-004 only makes the store
**ignore** any entry whose basename does not match it.

## Defect register entry (documentation)

Fields: ID · File:line · Description · Spec reference · Severity · Owner · Action · Status.
Status transitions: `Open` → `Closed (<regression group>)` for Feature-004 fixes only; all other
entries stay `Open`.
