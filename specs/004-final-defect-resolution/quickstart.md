# Quickstart: Verifying Feature-004 — Final Defect Resolution (US-20)

**Plan**: [plan.md](./plan.md) | **Contract**: [contracts/failure-messages.md](./contracts/failure-messages.md)

## Prerequisites

From `student_attrition_risk_app/`:

```bash
uv sync --dev
```

No workspace, credentials or network are needed; every regression scenario is offline.

## 1. Regression groups only

```bash
uv run pytest tests/test_defect_resolution.py -v
```

Expected: every test passes, grouped by section B2, B4, C3, B1. Each group should fail when run
against the sweep commit `3181882` (FR-024).

## 2. Done-gate (DEC-7)

```bash
uv run pytest -q
uv run ruff check src/student_attrition_risk/retry_workflow.py \
  src/student_attrition_risk/student_service.py \
  src/student_attrition_risk/briefing_store.py \
  src/student_attrition_risk/mcp_server.py \
  src/student_attrition_risk/api.py \
  tests/test_defect_resolution.py
```

Expected:

- pytest: the baseline 209 passed plus the new regression tests, **exactly 5 failed** (all
  `tests/test_ui.py`, register A1–A4 / C1), 13 skipped.
- ruff: no errors in the listed files. `ui.py` carries pre-existing teammate lint findings
  (A8, A10) and Renny's logged A9; check that Feature-004 adds none
  (`uv run ruff check src/student_attrition_risk/ui.py` shows the same findings as at `3181882`).

## 3. Manual spot-check (optional, local mock mode)

Point `BRIEFING_VOLUME` at an unreachable path, open the Streamlit app, select an at-risk student
and press **Generate**: a red **Store unavailable** notice appears; no "generated but could not be
stored" message.

## 4. Register

Open [defect-register.md](./defect-register.md): B1, B2, B4 and C3 (Renny half) show
`Closed (<regression group>)`; every other entry is `Open` with its owner.
