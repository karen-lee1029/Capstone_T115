# Defect Register: Feature-004 — Final Defect Resolution (US-20)

**Created**: 2026-09-24 | **Spec**: [spec.md](./spec.md) | **Backlog**: US-20 (GitHub issue #27)

Consolidated from the US-20 defect sweep (tracks A–D) run on `feat/feature-004-final-defect-resolution`
at `3181882` (main at `cdaf89e`). All source paths are under
`student_attrition_risk_app/src/student_attrition_risk/` unless they start with `tests/`
(`student_attrition_risk_app/tests/`). Line numbers are as of `3181882`.

Every entry starts with status **Open**. A Feature-004 fix moves to **Closed** only when its
regression test group (named after the register ID) passes in
`tests/test_defect_resolution.py`.

## 1. Baseline (before any Feature-004 change)

| Check | Result |
|---|---|
| `uv run pytest -q` | 209 passed, 5 failed, 13 skipped |
| Failures | All 5 in `tests/test_ui.py` (register A1–A4 / C1) |
| Skips | 13 in `tests/test_dashboard.py` (need a live Databricks workspace) |
| `uv run ruff check .` | 7 errors: 5 × I001 (import order), 2 × F401 (unused import); all autofixable (A8, A9, A10) |

## 2. Decisions (product owner, 2026-09-24 — final)

| # | Decision |
|---|---|
| DEC-1 | Severity scale is Critical / High / Medium / Low. US-20 is met when every Critical and High defect in scope is closed and every lower-priority defect is documented here. |
| DEC-2 | Feature-004 fixes Renny's (RennyMatis2000) own defects only. Teammates' defects are logged with owner and severity and left unfixed (constitution Principle XVI). |
| DEC-3 | Fixed in Feature-004: **B1, B2, B4, C3 (the `mcp_server.py:49-58` half only)**. B2 is rated High. |
| DEC-4 | Renny's defects logged only, not fixed: **C7** (Low), **A9** (Low). |
| DEC-5 | Not defects, recorded as design decisions: **C6** (`st.error` kept on error paths, deliberately red) and **DD-2** (small-group suppression commented out at `student_repository.py:367`, deliberate). |
| DEC-6 | Karen's five failing `tests/test_ui.py` tests are logged against Karen. They are not edited and not superseded. |
| DEC-7 | Done-gate for each fix: ruff clean on changed files; `uv run pytest` shows exactly the 5 known `tests/test_ui.py` failures and no others. |
| DEC-8 | Regression tests go in a new file `tests/test_defect_resolution.py` only, one test group per defect named after its register ID. Merged test files are never edited. |
| DEC-9 | Karen's `StructuredBriefingValidator` is already wired in `main.build_service` (`87670e4`), so the validation half of Feature-001 SC-007 is satisfied by her work. The instructions half (US-12) is still open. Not a Feature-004 item. |

## 3. Register

Action values: **Fix in Feature-004** · **Logged to owner** · **Not a defect – design decision** · **Unverified**.

### 3.1 Renny (RennyMatis2000)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| B1 (= C2, A7) | `student_service.py:122` → `api.py:64-67`; `ui.py:467` (also `ui.py:768-771`) | A store **read** outage during `POST /briefing` (non-regenerate) or during the UI Regenerate pre-check is reported as "Validated briefing could not be stored" / "generated but could not be stored", although nothing was generated or written. | 002 Edge Cases (read-time unreachable → explicit error); 002 FR-036 / FR-038 (misleading outcome) | Medium | Renny | Fix in Feature-004 | Open |
| B2 | `retry_workflow.py:98` (also `student_service.py:150`) | An exception raised by the validator on Attempt 2 escapes `SingleRetryWorkflow.run`: no terminal outcome is logged and the API answers "Databricks data source unavailable". Real trigger: D4 (NaN score). | 002 FR-005, SC-002 | High | Renny | Fix in Feature-004 | Open |
| B4 | `briefing_store.py:64-66`, `84-89` | Any non-briefing file in a student's Volume folder makes `has_validated` true and becomes the "latest" briefing, so every retrieval for that student fails until the file is deleted by hand. | 002 FR-022 / FR-023, SC-008 | Medium | Renny | Fix in Feature-004 | Open |
| C3 (Renny half) | `mcp_server.py:49-58` | The MCP briefing tools let backend exceptions through; FastMCP forwards the raw text (Volume paths, warehouse errors) to the client, while REST returns safe 503 messages. | App README ("503 with safe messages"); constitution X, XI (sweep also cited 002 FR-032, which concerns attempt-count display) | Medium | Renny | Fix in Feature-004 | Open |
| C7 | `api.py:81-84` | `GET /briefing` says "store unavailable" when the data source is what is down (503 either way). | — | Low | Renny | Logged to owner | Open |
| A9 | `ui.py:20` | Unused import `StudentNotAtRiskError` (F401). | — | Low | Renny | Logged to owner | Open |

### 3.2 Karen (karen-lee1029 / k224.lee)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| D1 | `briefing_validation.py:54` | Risk-level check is a substring match on "at risk", so "Not At Risk" passes. | US-14 | High | Karen | Logged to owner | Open |
| D2 | `briefing_validation.py:67` | Score check accepts the integer part anywhere in the text ("78" for 78.5%). | US-14 | High | Karen | Logged to owner | Open |
| D3 | `briefing_validation.py:211` | "Mentions student data" check effectively always passes (0/1 values match any digit). | US-14 | High | Karen | Logged to owner | Open |
| D4 | `briefing_validation.py:211` | NaN raises `ValueError`, inf raises `OverflowError`; triggers B2 on Attempt 2. | US-14 | Medium | Karen | Logged to owner | Open |
| D5 | `briefing_validation.py:148`, `165` | AC5 is appended to the failed criteria twice. | US-14 | Low | Karen | Logged to owner | Open |
| D6 | `briefing_validation.py:109`, `111` | The "I'm going to" / "I've contacted" regexes never match. | US-14 | Medium | Karen | Logged to owner | Open |
| A1–A4 / C1 | `tests/test_ui.py:235-337` | 5 tests fail against the current UI: they expect `st.info`, an "Attempt:" label (contradicts 002 FR-032), and a `FakeService` without `has_stored_briefing`. Not edited, not superseded (DEC-6). | 002 FR-032 | High | Karen | Logged to owner | Open |
| A5 | `main.py:81-84` | `ConfigurationError` is swallowed and `app=None`, so every route returns 500 with no cause shown. Joint with D7. | 001 FR-014 | High | Karen (joint with GuaGuaGua88, D7) | Logged to owner | Open |
| A10 (Karen part) | `briefing_validation.py:9`, `tests/test_ui.py:13` | I001 unsorted imports. | — | Low | Karen | Logged to owner | Open |

### 3.3 GuaGuaGua88 (l52.yang)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| D7 (= A6, B5, C5) | `main.py:29-32` | Mock mode requires `DATABRICKS_MODEL_NAME`, so the README quick start fails and the whole app is unusable. | 001 FR-014 | High | GuaGuaGua88 | Logged to owner | Open |
| D8 | `config.py:87-88` | A blank or non-numeric port raises an uncaught `ValueError` at import. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| D9 | `config.py:78` | `USE_MOCK_DATA` values "1" / "yes" / " true" are read as false, so the app silently runs live. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| D10 | `databricks_client.py:16-21` | Token set with host unset raises `AttributeError`. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| C3 (other half) | `mcp_server.py:21-33` | Profile and list MCP tools leak raw exception text. | App README; 001 | Medium | GuaGuaGua88 | Logged to owner | Open |
| C4 | `mcp_server.py:21-28` | REST and MCP disagree for an unknown student and for `limit=0`. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| C8 | `ui.py:793-856` | Opening and closing `div` wrappers are emitted in separate `st.markdown` calls, so they never wrap the content. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| A8, A10 (part) | `ui.py:6`; `ui.py`, `main.py`, `briefing_instructions.py` | F401 unused `Decimal`; I001 import order. | — | Low | GuaGuaGua88 | Logged to owner | Open |

### 3.4 Third party

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| A11 | — (test run warnings) | Starlette / Authlib deprecation warnings. | — | Low | Third party | Logged to owner | Open |

### 3.5 Design decisions (not defects)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| C6 | `ui.py` (error paths) | `st.error` is used on error paths. Kept red deliberately. | — | — | Renny | Not a defect – design decision | Open |
| DD-2 | `student_repository.py:367` | Small-group suppression is commented out deliberately. | — | — | GuaGuaGua88 | Not a defect – design decision | Open |

### 3.6 Suspected, unconfirmed

Recorded so they are not lost; none is treated as a defect until reproduced.

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| U1 | — | In-memory store is not shared between the Streamlit process and REST/MCP when `BRIEFING_VOLUME` is unset (local only). | — | — | — | Unverified | Open |
| U2 | — | Volume store uses the raw hash in its path. Not exploitable: entry points check the hash exists. | — | — | — | Unverified | Open |
| U3 | — | `LIMIT ?` placeholder on Databricks. | — | — | — | Unverified | Open |
| U4 | — | Case-sensitive column lookup. | — | — | — | Unverified | Open |
| U5 | — | `Decimal` / date types from live Databricks versus the validator. | — | — | — | Unverified | Open |
| U6 | — | AC7 8–10 digit false positive. | — | — | — | Unverified | Open |
| U7 | — | Proxy header merge. | — | — | — | Unverified | Open |
| U8 | — | WebSocket close codes. | — | — | — | Unverified | Open |

## 4. Summary by severity

| Severity | Total | Fix in Feature-004 | Logged to owner |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| High | 7 | 1 (B2) | 6 (D1, D2, D3, A1–A4/C1, A5, D7) |
| Medium | 6 | 3 (B1, B4, C3 Renny half) | 3 (D4, D6, C3 other half) |
| Low | 11 | 0 | 11 (incl. Renny's C7, A9) |

Design decisions (C6, DD-2) and unverified items (U1–U8) carry no severity and are not counted.

US-20 status against DEC-1: the only High defect in Renny's scope (B2) is fixed by Feature-004.
Six High defects remain open with their owners (Karen: D1, D2, D3, A1–A4/C1, A5; GuaGuaGua88: D7).
Closing them is outside Feature-004 under DEC-2.
