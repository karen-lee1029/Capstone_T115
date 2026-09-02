# Contract: MCP Tools (Feature-001 / US-08)

FastMCP server mounted at `/mcp` (unchanged). Tools contain no SQL and delegate to
`StudentService` (existing rule; constitution IX). Existing `get_student_prediction`,
`get_student_profile`, `get_high_risk_students` are unchanged by Feature-001.

Behaviour matches `contracts/rest-api.md`. With Feature-001's placeholder seams a generation
run cannot succeed — `generate_student_briefing` for a flagged student with no existing briefing
returns a "generation is not configured" tool error until US-13/14/15 land.

## generate_student_briefing(student_hash: str, regenerate: bool = False) -> dict

Request a briefing — get-or-create semantics, same as `POST /api/students/{hash}/briefing`.

- Returns the existing validated briefing (`source="stored"`) when one exists and `regenerate`
  is false — no generation-seam call (FR-035).
- Otherwise, for a student flagged at risk, routes through the generation and validation seams;
  on a seam-reported pass returns the validated briefing (`source="generated"`,
  `validated=true`).
- `regenerate=true` forces a fresh seam run; on terminal failure the previous validated
  briefing is retained (FR-036/FR-037).

Failures surface as MCP tool errors (never a fabricated briefing):

| Cause | Message |
|---|---|
| Not flagged at risk (FR-034) | `student is not flagged at risk` |
| Unknown hash / no prediction | `student hash not found` |
| Generation seam not configured (FR-014; until US-13) | `briefing generation is not configured` |
| Feature blocked pending review (FR-008) | `briefing context requires human review: <constraint>` |
| Retry seam terminal — generation (FR-021) | `briefing could not be produced (generation)` |
| Retry seam terminal — validation (FR-021) | `briefing could not be produced (validation)` |
| Persistence seam failure (FR-024) | `validated briefing could not be stored` |
| Data source unavailable | `databricks data source unavailable` |

## get_student_briefing(student_hash: str) -> dict

Retrieve the most recent stored validated briefing (mirrors `GET /api/students/{hash}/briefing`).

- Returns the validated briefing (`source="stored"`, `validated=true`) when one exists (FR-030).
- Returns `{"available": false, "student_hash": <hash>}` when the student has no validated
  briefing (FR-030).
- Only validated briefings are ever returned (FR-029). Advisor-facing display is US-10.

## Tool inventory after Feature-001

`get_student_prediction`, `get_student_profile`, `get_high_risk_students`,
`generate_student_briefing` (changed), `get_student_briefing` (new).
