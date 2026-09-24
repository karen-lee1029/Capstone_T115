# Implementation Plan: Feature-004 — Final Defect Resolution (US-20)

**Branch**: `feat/feature-004-final-defect-resolution` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md) | **Register**: [defect-register.md](./defect-register.md)

**Input**: Feature specification from `specs/004-final-defect-resolution/spec.md`

## Summary

Close the four defects the register marks "Fix in Feature-004" — B2 (High), B4, C3 (briefing-tool
half) and B1 — with the smallest change to this contributor's own lines that restores the
behaviour Feature-001 and Feature-002 already specify. Each fix gets one regression group in a
new file, `tests/test_defect_resolution.py`. No new module, dependency or abstraction is added;
the one new type is an exception subclass that lets a store **read** failure be told apart from a
store **write** failure (B1). Every other register entry is documented, not fixed.

## Technical Context

**Language/Version**: Python 3.11 (`pyproject.toml` `target-version = "py311"`)

**Primary Dependencies**: FastAPI (REST), FastMCP (tool interface), Streamlit (advisor surface),
`databricks-sdk` Files API (governed store) — all existing; none added.

**Storage**: Unity Catalog Volume via `VolumeBriefingStore`; `InMemoryBriefingStore` locally. No
schema or layout change.

**Testing**: pytest with the existing offline doubles (`tests/doubles.py`,
`tests/workflow_doubles.py`) imported read-only; FastAPI `TestClient`; FastMCP in-process client;
Streamlit `AppTest`. Ruff (`E, F, I, UP`, line length 110).

**Target Platform**: Databricks App (Linux); local mock mode for verification.

**Project Type**: Web service + Streamlit app in `student_attrition_risk_app/`.

**Performance Goals**: None new. B4 adds one filename match per listed entry.

**Constraints**: Change only this contributor's lines (register DEC-2, DEC-10, DEC-11); never edit
merged tests; offline verification; done-gate = ruff clean on changed files and exactly the 5 known
`tests/test_ui.py` failures (DEC-7).

**Scale/Scope**: 4 defects, 6 source files, 1 new test file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — still passing.*

| Principle | How this plan satisfies it |
|---|---|
| I Specification-driven | Every change traces to an FR in spec.md and an approved Feature-001/002 requirement; no requirement is rewritten. |
| II Scope containment | Only the files and line ranges in § Change map. Teammates' lines (`ui.py:725-737`, `763-775`, `787-788`; `mcp_server.py:21-33`; `briefing_validation.py`; `main.py`; `config.py`) untouched. |
| III Read broadly, write narrowly | Teammate code was read (and `git blame`d) only to confirm ownership boundaries. |
| IV Minimal change | Each fix is a local `try/except` or filter at the failing line. One exception subclass; one CSS class. |
| V Reuse architecture | Reuses `TerminalFailure`, `ValidationFailed`, `ValidationOutcome`, `BriefingStorageError`, `render_notice`, existing REST wording, existing doubles. |
| VI No unnecessary complexity | No new module, port, dependency, or configuration. |
| VII Plan-defined structure | File list fixed here; tasks may not widen it. |
| VIII Technology compatibility | Python only; Volume Files API unchanged. |
| IX Separation of responsibilities | Retry fix stays in the retry workflow; read/write distinction in the service; wording at each boundary; filename rule inside the store. |
| X Security and privacy | C3 removes raw Volume paths and warehouse text from tool errors. Logs stay metadata-only. |
| XI Explicit error handling | B2 and B1 replace an escaping or misattributed exception with an explicit outcome. |
| XII Proportionate testing | One regression group per defect; no re-test of Feature-001/002/003 behaviour. |
| XIII Human review | Plan, tasks and diffs reviewed by the product owner before merge. |
| XIV Traceability | Register ID → FR → task → regression group; register entries closed with group names. |
| XV Completion = spec | Done when FR-001–FR-032 hold; nothing extra. |
| XVI Team contributions | Enforced by the line-owned change map below. |
| XVII Human-controlled VCS | Commits only on the feature branch when instructed; no push or merge. |

No violations; Complexity Tracking is empty.

## Change map (per defect)

Line numbers are as of `3181882`. Every listed line is authored by RennyMatis2000 (`git blame`),
except where noted as a pure insertion point.

| Defect | File | Lines | Change |
|---|---|---|---|
| **B2** | `src/student_attrition_risk/retry_workflow.py` | 98-100 | Wrap the Attempt-2 `validate` call: `ConfigurationError` re-raised; any other exception → `TerminalFailure(category="validation")`. |
| B2 | `src/student_attrition_risk/student_service.py` | 150-163 | Wrap the Attempt-1 `validate` call: `ConfigurationError` re-raised; any other exception → `ValidationFailed` with an empty failed outcome, handed to the retry (spec Q2). |
| **B4** | `src/student_attrition_risk/briefing_store.py` | 8-16 (import `re`, add name pattern), 62-73 (`has_validated`), 84-88 (`get_latest_validated` filter) | Only entries whose basename matches the store's own `<YYYYMMDDTHHMMSSffffffZ>-attempt<n>-<6 hex>.json` name count. Others ignored silently (spec Q4). `save_validated` (teammate-touched lines 101-118) unchanged. |
| **C3** | `src/student_attrition_risk/mcp_server.py` | 34-47 (`generate_student_briefing`), 49-57 (`get_student_briefing`) | Add the missing mappings so each tool returns the lower-cased REST message: generate → catch-all `"databricks data source unavailable"`; get → any non-not-found failure `"validated briefing store unavailable"`. Lines 21-33 unchanged. |
| **B1** | `src/student_attrition_risk/student_service.py` | 53-54 (insert `BriefingStoreUnavailableError(BriefingStorageError)`), 122-123 (read path), 186-192 (`has_stored_briefing`) | Store read failures raised as `BriefingStoreUnavailableError`; write failures keep `BriefingStorageError`. |
| B1 | `src/student_attrition_risk/api.py` | 7-13 (import), 60-67 (insert handler before `BriefingStorageError`) | `POST /briefing` read failure → 503 `"Validated briefing store unavailable"` (the `GET` wording, spec Q3). |
| B1 | `src/student_attrition_risk/mcp_server.py` | 6-12 (import), 42-45 (insert handler before `BriefingStorageError`) | `generate_student_briefing` read failure → `"validated briefing store unavailable"`. |
| B1 | `src/student_attrition_risk/ui.py` | 17-22 (import; line 19 is GuaGuaGua88's and stays as is — the new name is added on its own line), 332-343 (insert `.store-error-notice` after `.page-notice`), 441 (`render_notice` `style` made positional-or-keyword so a 3-tuple `ui_message` renders through the existing line 789), 461-480 (`request_briefing` catches `BriefingStoreUnavailableError` from lines 467 and 469, sets `ui_message = ("Store unavailable", "Validated briefing store unavailable.", "store-error-notice")`, returns) | Red page-owned notice (#fee4e2 / #d92d20 / #b42318), `html.escape` via `render_notice`; no `st.error`/`st.info`/`st.warning`. GuaGuaGua88's handlers (725-737, 763-775) and render lines 787-788 untouched (DEC-10). |

**Cross-group overlap** — `student_service.py` (B2: 150-163; B1: 53-54, 122-123, 186-192) and
`mcp_server.py` (C3: 34-57; B1: 6-12, 42-45). B1 therefore runs **after B2 and C3**. B4 is
independent.

## Project Structure

### Documentation (this feature)

```text
specs/004-final-defect-resolution/
├── spec.md
├── defect-register.md       # the "current defect list" (US-20)
├── plan.md                  # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── failure-messages.md  # per-boundary wording each fix must produce
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks
```

### Source Code (repository root)

```text
student_attrition_risk_app/
├── src/student_attrition_risk/
│   ├── retry_workflow.py     # B2
│   ├── student_service.py    # B2, B1
│   ├── briefing_store.py     # B4
│   ├── mcp_server.py         # C3, B1
│   ├── api.py                # B1
│   └── ui.py                 # B1
└── tests/
    └── test_defect_resolution.py   # NEW — sections B2, B4, C3, B1
```

**Structure Decision**: Existing single-app layout. No new source module. One new test file,
following the Feature-003 convention of importing `doubles.py` / `workflow_doubles.py` read-only
and defining any extra double locally (a validator that raises).

## Complexity Tracking

None.
