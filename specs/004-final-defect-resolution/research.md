# Research: Feature-004 — Final Defect Resolution (US-20)

**Date**: 2026-09-24 | **Plan**: [plan.md](./plan.md)

No Technical Context item was left as NEEDS CLARIFICATION. The decisions below settle the
implementation choices the spec leaves to planning.

## R1 — B2: where to catch a validator exception

- **Decision**: At each `validate` call site — `retry_workflow.py:98` (Attempt 2) and
  `student_service.py:150` (Attempt 1). `ConfigurationError` is re-raised; any other exception on
  Attempt 1 becomes `ValidationFailed(outcome=ValidationOutcome(passed=False, validator_id=...))`
  with no criteria or feedback, so the retry prompt is unchanged (Feature-002 FR-010); on Attempt 2
  it becomes `TerminalFailure(category="validation")`.
- **Rationale**: Mirrors the existing generation-side handling on the lines directly above
  (`retry_workflow.py:90-96`, `student_service.py:139-148`). The terminal outcome then flows through
  the existing `_hand_off_to_retry` log line and `BriefingNotProducedError` → 502 / tool error.
- **validator_id for the synthetic outcome**: `getattr(self.validator, "validator_id",
  "unavailable")`. The `BriefingValidator` port does not declare `validator_id`; both real
  validators set it as a class attribute. The value never reaches a stored briefing (only a
  passing Attempt-2 outcome is stored, with its own id).
- **Alternatives rejected**: wrapping in the validator (Karen's file, DEC-2); a new failure category
  (would change Feature-002's two-category contract).

## R2 — B1: telling a read failure from a write failure

- **Decision**: New `BriefingStoreUnavailableError(BriefingStorageError)` in `student_service.py`,
  raised by the service when `has_validated` / `get_latest_validated` fail on the request path and
  in `has_stored_briefing`. Boundaries catch it **before** `BriefingStorageError`.
- **Rationale**: Stores stay unchanged (they already raise `BriefingStorageError` for any Files-API
  failure). A subclass means any handler that only knows `BriefingStorageError` still catches it,
  so no caller breaks. The `GET` path already maps any failure to "store unavailable" and needs no
  change.
- **Alternatives rejected**: separate exception classes inside each store (touches teammate lines in
  `save_validated`); a non-subclass error (would fall into GuaGuaGua88's generic UI handler, not
  meeting spec Q3).

## R3 — B1: advisor-facing notice without touching teammates' handlers

- **Decision**: `request_briefing()` in `ui.py` catches `BriefingStoreUnavailableError` from the
  pre-check (467) and the service call (469), stores
  `("Store unavailable", "Validated briefing store unavailable.", "store-error-notice")` in
  `st.session_state.ui_message`, and returns. The handler's `st.rerun()` then runs and the existing
  line 789 `render_notice(*message)` shows it. `render_notice`'s `style` parameter drops its
  keyword-only marker so the 3-tuple is accepted; 2-tuples behave exactly as today.
- **Style**: new `.store-error-notice` in the existing `<style>` block, modelled on `.page-notice`,
  with background `#fee4e2`, border `#d92d20`, text `#b42318` (existing error palette).
- **Alternatives rejected**: `st.error` (DEC-10 and the project's no-built-in-alerts rule); editing
  lines 787-789 region owned by GuaGuaGua88.

## R4 — B4: recognising the store's own files

- **Decision**: A module-level compiled pattern
  `^\d{8}T\d{12}Z-attempt\d+-[0-9a-f]{6}\.json$`, matched against the basename of each entry path.
  This is exactly what `_file_path` produces (`%Y%m%dT%H%M%S%fZ`, `token_hex(3)`).
- **Rationale**: Uses the store's own naming convention (FR-016), keeps lexicographic "latest"
  ordering intact, ignores everything else silently (FR-018, spec Q4).
- **Alternatives rejected**: suffix-only `.json` check (a stray `.json` would still win); skipping
  unparsable files on read (would hide a genuinely corrupt briefing, which Feature-002 surfaces as
  an error).

## R5 — C3: which messages

- **Decision**: Tools return the lower-cased form of the REST message for the same failure, which
  is the convention the existing tool messages already follow ("student hash not found" ↔ "Student
  hash not found"). See [contracts/failure-messages.md](./contracts/failure-messages.md).
- **Note**: mirroring `GET` means the retrieval tool also says "store unavailable" when the data
  source is down — the same Low defect as C7, which stays logged (DEC-4), not fixed.

## R6 — Regression test mechanics

- **Decision**: One file, `tests/test_defect_resolution.py`, sections in order B2, B4, C3, B1.
  Imports `workflow_doubles` / `doubles` read-only; adds a local `RaisingValidator` and a local
  store double whose reads raise `BriefingStorageError`. REST via `build_rest_client`; tools via
  `build_mcp_server` with the FastMCP in-process client; UI via Streamlit `AppTest` with a patched
  service, as `tests/test_ui.py` does (not edited).
- **Rationale**: Reuses Feature-003 conventions (FR-006 there, FR-025 here); no merged file edited.
