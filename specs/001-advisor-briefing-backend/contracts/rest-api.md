# Contract: REST API (Feature-001 / US-08)

Base path `/api` (unchanged). New and changed operations only; existing `GET /api/health`,
`GET /api/students/{hash}`, `GET /api/students/high-risk` are unchanged by Feature-001 (the
high-risk list is retained as the backend risk-data retrieval US-10 consumes). Response bodies
are the models in `data-model.md`. FastAPI request validation still yields `422`.

The status rows below describe the full contract. With Feature-001's **placeholder seams**
(`StubGenerationProvider`, `InMemoryBriefingStore`), a generation run cannot succeed — a flagged
student with no existing briefing gets `503 "Briefing generation is not configured"`. The
success rows become reachable when US-13 (generation), US-14 (validation), and US-15 (storage)
supply concrete seams.

## POST /api/students/{student_hash}/briefing  — request a briefing (get-or-create)

Get-or-create behaviour, approved 2026-09-03 (`plan.md` → Approved planning decisions #1): an
existing validated briefing is returned without invoking the generation seam; a fresh briefing
occurs only via `?regenerate=true`.

**Path**: `student_hash` — 1–256 chars (existing `Path` bound).
**Query**: `regenerate` — bool, default `false`. `true` forces a fresh seam run even when a
validated briefing exists.

| Situation | Status | Body |
|---|---|---|
| Validated briefing exists and `regenerate=false` | `200` | `ValidatedBriefing` (`source="stored"`, `validated=true`); **no generation-seam call** (FR-035) |
| Flagged at risk, no existing briefing (or `regenerate=true`), generation seam returns a draft the validation seam passes | `200` | `ValidatedBriefing` (`source="generated"`, `validated=true`, `attempt_count=1`) |
| Known student, `attrition_risk_flag` is false | `409` | `{"detail": "Student is not flagged at risk"}` — no context assembly, no seam call for generation (FR-034) |
| Unknown / malformed hash, or no prediction row | `404` | `{"detail": "Student hash not found"}` |
| Generation seam not configured (Feature-001 default; until US-13) | `503` | `{"detail": "Briefing generation is not configured"}` (FR-014) |
| A required feature blocked by a policy/platform constraint | `503` | `{"detail": "Briefing context requires human review: <constraint>"}` (FR-008) |
| Attempt 1 fails (generation seam or validation seam) → retry seam → `TerminalFailure` | `502` | `{"detail": "Briefing could not be produced (generation)"}` or `"... (validation)"` — the category is in the message only, not a distinct code (FR-021) |
| Persistence seam reports a write failure | `503` | `{"detail": "Validated briefing could not be stored"}`; any previous validated briefing is retained (FR-024/FR-037) |
| Delta source unavailable | `503` | `{"detail": "Databricks data source unavailable"}` (existing convention) |

Notes:
- On `regenerate=true` terminal failure, the previously stored briefing is unchanged and still
  retrievable via `GET` (FR-037).
- Every terminal path returns a body (FR-022). No template/deterministic briefing is ever
  returned here (FR-020).

## GET /api/students/{student_hash}/briefing  — retrieve the stored validated briefing

**Path**: `student_hash` — 1–256 chars.

| Situation | Status | Body |
|---|---|---|
| A validated briefing exists | `200` | `ValidatedBriefing` (`source="stored"`, `validated=true`) — the most recent (FR-030) |
| No validated briefing for this student | `404` | `{"detail": "No validated briefing available"}` (FR-030) |
| Unknown / malformed hash | `404` | `{"detail": "Student hash not found"}` |
| Persistence seam unavailable | `503` | `{"detail": "Validated briefing store unavailable"}` |

Only validated briefings are ever returned; drafts and failed briefings are structurally
unreachable because only validated briefings are handed to the persistence seam (FR-029). The
advisor-facing display of this briefing is US-10.

## Status code summary (approved set — 2026-09-03; no others to be introduced)

| Code | Meaning in this feature |
|---|---|
| `404` | Requested student / resource does not exist (unknown or malformed hash, no prediction row, no validated briefing on retrieval) |
| `409` | Valid request conflicts with application state — including a briefing request for a student not flagged at risk (FR-034) |
| `422` | Request / input validation only, via the existing FastAPI / Pydantic behaviour |
| `502` | A downstream briefing-generation dependency failed to produce a valid briefing — retry-seam `TerminalFailure`, generation or validation (category in the detail text only) (FR-021) |
| `503` | Required Databricks / data / backend infrastructure unavailable — Delta source down, generation seam unconfigured (until US-13), persistence seam unavailable, or a feature blocked pending human review (FR-008/FR-014/FR-024) |
