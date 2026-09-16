# Quickstart: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Date**: 2026-09-16 | **Plan**: [plan.md](./plan.md)

How to run and validate Feature-003. Everything here runs offline — no network, no Databricks
workspace, no credentials, no environment variables.

## Prerequisites

- Python 3.11–3.13 and `uv`
- Working directory: `student_attrition_risk_app/`
- No new dependency is required; `uv sync --dev` covers everything

```zsh
cd student_attrition_risk_app
uv sync --dev
```

## Baseline before starting

Record that the pre-existing suite is green before any Feature-003 file is added. Feature-003 must
not disturb it (SC-014).

```zsh
uv run ruff check .
uv run pytest
```

**Expected at planning time**: 84 passed.

## Running Feature-003

```zsh
# Feature-003 only
uv run pytest tests/test_briefing_workflow_*.py

# Full merge gate
uv run ruff check .
uv run pytest
```

**Expected after implementation**: all pre-existing verifications still pass and the Feature-003
verifications pass. **No verification is expected to fail.** The blank-content defect that once
warranted a strict expected-fail was resolved before implementation, so that scenario is now an
ordinary passing verification.

Should Feature-003 later record a new defect, its expected-fail would appear here; an unexpected
pass on such a verification fails the suite deliberately, signalling that the defect was fixed and
the record needs updating. See [contracts/traceability-record.md](./contracts/traceability-record.md).

## Validating the feature

Each row is checkable without reading implementation detail.

| # | Check | How | Expected |
|---|---|---|---|
| 1 | No production file changed | Inspect the working tree | Only files under `tests/` and `specs/003-briefing-workflow-testing/` differ |
| 2 | No Feature-001/002 verification changed | Inspect the working tree | None of the twelve pre-existing verification files differ |
| 3 | Pre-existing suite intact | `uv run pytest` | All 84 pre-existing verifications still pass |
| 4 | Offline | Disconnect the network and re-run | Identical result |
| 5 | Outcome coverage | Read the scenario map | Every outcome in FR-012–FR-021 appears |
| 6 | Call order verified | Retry verifications | Boundary order asserted, not only counts |
| 7 | Feedback propagation | Retry verifications | Second attempt succeeds only when the revision block reached generation |
| 8 | No third attempt | Retry verifications | Generation engaged at most twice in every scenario |
| 9 | Write counts | Storage verifications | Exactly one write on success; zero on every failure, refusal and get-or-create return |
| 10 | Governed-store parity | Storage verifications | The six storage-decision outcomes behave identically against the governed store; no other outcome is re-run |
| 11 | Tool-boundary gaps | Boundary verifications | Terminal failure, storage failure and configuration failure covered there; REST tracked, not repeated |
| 12 | Log hygiene | Boundary verifications | Failure-path records carry metadata only — no briefing text, prompt text, criteria or secret |
| 13 | Timing criterion | Traceability verifications | The three non-generation paths complete within one second |
| 14 | Blank content rejected | Traceability verifications | Empty and whitespace-only content surface as a generation failure; nothing stored |
| 15 | Record resolves | `uv run pytest tests/test_briefing_workflow_traceability.py` | Every cited verification name resolves |
| 16 | Deferral recorded | Traceability record | Feature-001 SC-007 listed with its specific reason |
| 17 | No invented criteria | Search fixtures for criteria values | All visibly synthetic |

## Deliberately not verifiable here

These are out of scope and no check should be expected to cover them:

- Briefing quality or acceptance-criteria content — **US-14**
- Final prompt content — **US-12**
- Real generative-provider behaviour, latency, non-determinism, rate limits, filtering, cost — **US-13**
- Live Unity Catalog Volume access and end-to-end integration — **US-16** and infrastructure
- The advisor-facing interface — **US-17**
- Concurrent requests for the same student — declared not specially handled by Feature-002
- Feature-001 SC-007 seam substitution — deferred, with the reason recorded in the traceability record
- Any fix to a defect this feature records — **US-19 through US-23**

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| The record self-check fails naming a Feature-001 verification | That verification was renamed or removed. Update Feature-003's traceability record. **Do not edit the Feature-001 file** — it is read-only under approved decision H3 |
| A verification marked expected-fail reports an unexpected pass | Its defect was fixed elsewhere. Update the traceability record, remove the expectation, keep the scenario as an ordinary verification |
| A scripted double reports being called more times than scripted | A scenario drove more attempts than intended — usually the genuine "no third attempt" signal working correctly |
| The timing verification is marginal | Investigate rather than loosening the budget; headroom over in-memory operations is several orders of magnitude, so a near-miss indicates a real change |
