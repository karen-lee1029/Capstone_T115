# Data Model: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Date**: 2026-10-01 | **Plan**: [plan.md](./plan.md)

Feature-005 adds no persisted data, no table, no model field and no Python type. It changes how
existing values are labelled, coloured, ordered and explained.

## Risk category (derived, dashboard dimension `risk_level`)

| Field | Value |
|---|---|
| Source | `attrition_risk_percentage` in `workspace.student_aggregate.student_attrition_risk_prediction` |
| Rule | `>= 50` → `At Risk`; otherwise `Not At Risk` (was `High` / `Low`) |
| Values | exactly two: `At Risk`, `Not At Risk` |
| Order | `At Risk` (1), `Not At Risk` (2) |
| Colour | `At Risk` `#1565C0`; `Not At Risk` `#42A5F5` |

Advisor page equivalent: the badge label comes from `attrition_risk_flag` (`True` → `At Risk`,
`False` → `Not At Risk`), unchanged. With a 50% decision threshold the two rules agree (spec
Assumptions).

## Score range (derived, dashboard dimension `risk_score_bucket`) — unchanged

| Order | Label | Range of `attrition_risk_percentage` | Category |
|---|---|---|---|
| 1 | `0-46%` | `< 46` | Not At Risk |
| 2 | `46-48%` | `46 – < 48` | Not At Risk |
| 3 | `48-49%` | `48 – < 49` | Not At Risk |
| 4 | `49-50%` | `49 – < 50` | Not At Risk |
| 5 | `50-51%` | `50 – < 51` | At Risk |
| 6 | `51-52%` | `51 – < 52` | At Risk |
| 7 | `52-54%` | `52 – < 54` | At Risk |
| 8 | `54-100%` | `>= 54` | At Risk |

Each range falls wholly in one category, so each bar of the Risk Score Distribution takes a single
category colour.

## Dashboard explanation

- **How to read panel**: widget `how_to_read`, one per dashboard. Text names both categories, the
  50% threshold and both colours.
- **Chart description**: `spec.frame.description.value` with `showDescription: true`, one per chart
  (five).

## Badge style (advisor page)

| Class | Shown when | Background | Text | Contrast |
|---|---|---|---|---|
| `.risk-badge` | `attrition_risk_flag` is `True` | `#1565C0` (was `#fee4e2`) | `#FFFFFF` (was `#b42318`) | 5.75:1 |
| `.not-risk-badge` | `attrition_risk_flag` is `False` | `#42A5F5` (was `#dcfae6`) | `#172033` (was `#067647`) | 6.15:1 |

## Teammate change record (documentation)

Fields: File + lines · Original author + commit · What changed and why · Commit that made it ·
Revert instructions. One table per changed contribution in
[teammate-changes.md](./teammate-changes.md).
