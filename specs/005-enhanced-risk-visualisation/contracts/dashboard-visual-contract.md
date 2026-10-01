# Contract: Risk visual language after Feature-005

**Plan**: [../plan.md](../plan.md) | **Spec**: [../spec.md](../spec.md)

This contract is the target state Tracks B and C build and Track D's offline checks assert. File:
`student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json` unless stated.
Anything not listed here stays exactly as it is at `9469edc`.

## 1. Label map

| Where | Before | After |
|---|---|---|
| Dataset `b798cf1c`, dimension `risk_level`, `expr` | `CASE WHEN source.attrition_risk_percentage >= 50 THEN 'High' ELSE 'Low' END` | `CASE WHEN source.attrition_risk_percentage >= 50 THEN 'At Risk' ELSE 'Not At Risk' END` (same line breaks: `"CASE\n  WHEN source.attrition_risk_percentage >= 50 THEN 'At Risk'\n  ELSE 'Not At Risk'\nEND"`) |
| `counter_high` filter | `` `student_attrition_risk_prediction`.`risk_level` IN ('High') `` | `` `student_attrition_risk_prediction`.`risk_level` IN ('At Risk') `` |
| `counter_high` title | `High Risk` | `At Risk` |
| `counter_low` filter | `` ... IN ('Low') `` | `` ... IN ('Not At Risk') `` |
| `counter_low` title | `Low Risk` | `Not At Risk` |
| Colour-map `value`s on all five charts | `High`, `Low` | `At Risk`, `Not At Risk` |
| `filter_risk_level` options, table "Risk Level" column | `High`, `Low` (from the dimension) | `At Risk`, `Not At Risk` (from the dimension; no edit) |

Forbidden anywhere as a category value, title, filter literal or mapping value: `High`, `Low`,
`Medium`, `High Risk`, `Low Risk`.

## 2. Colour map

Identical on every chart, in this order (`encodings.color.scale.mappings`):

```json
[
  {"color": "#1565C0", "value": "At Risk"},
  {"color": "#42A5F5", "value": "Not At Risk"}
]
```

Charts (widget name → title): `chart_risk_donut` → Risk Level Distribution;
`chart_risk_by_faculty` → Risk Score Distribution; `chart_risk_study_mode` → Risk by Age Band;
`chart_risk_gender` → Risk by Gender; `chart_risk_intl` → Risk by Origin.

Counters keep their existing `style.fontColor`: `counter_high` `#1565C0` (light and dark),
`counter_low` `#42A5F5` (light and dark).

## 3. Sort order

| Chart | Categorical axis | Setting | Resulting order |
|---|---|---|---|
| Risk Level Distribution | `y` (`risk_level`) | `"sort": {"by": "natural-order"}` | At Risk, Not At Risk |
| Risk Score Distribution | `x` (`risk_score_bucket`) | `"sort": {"by": "natural-order"}` | 0-46%, 46-48%, 48-49%, 49-50%, 50-51%, 51-52%, 52-54%, 54-100% |
| Risk by Age Band | `y` (`age_band`) | `"sort": {"by": "natural-order"}` | ascending label |
| Risk by Gender | `y` (`gender`) | `"sort": {"by": "natural-order"}` | ascending label |
| Risk by Origin | `y` (`international_domestic`) | `"sort": {"by": "natural-order"}` | ascending label |

The setting goes inside the existing `scale` object beside `"type": "categorical"`. Legend order
follows the colour-map order in § 2 (At Risk first). The eight range labels and boundaries are
unchanged.

## 4. Chart descriptions

Every chart: `spec.frame.showDescription = true` and `spec.frame.description = {"value": <text>,
"fields": []}`.

| Chart | Description |
|---|---|
| Risk Level Distribution | `Number of students in each risk category: At Risk (50% or higher) and Not At Risk (below 50%)` |
| Risk Score Distribution | `Number of students in each attrition risk score range, lowest to highest; ranges from 50% are At Risk` |
| Risk by Age Band | `At Risk and Not At Risk student counts for each age band` |
| Risk by Gender | `At Risk and Not At Risk student counts for each gender` |
| Risk by Origin | `At Risk and Not At Risk student counts for domestic and international students` |

Titles are unchanged except the two counters (§ 1).

## 5. "How to read this dashboard" text widget

New layout item on page `f8c29798`:

```json
{
  "widget": {
    "name": "how_to_read",
    "multilineTextboxSpec": {
      "lines": [
        "<div style=\"background-color: #F5F7FA; border-left: 3px solid #1565C0; border-radius: 4px; padding: 10px 16px; color: #374151; font-size: 12px; line-height: 1.5;\">\n",
        "<div style=\"color: #00407A; font-size: 14px; font-weight: 700; margin-bottom: 4px;\">How to read this dashboard</div>\n",
        "Each student is placed in one of two risk categories by their attrition risk percentage. ",
        "<span style=\"display: inline-block; width: 10px; height: 10px; background-color: #1565C0; border-radius: 2px;\"></span> <strong>At Risk</strong> (dark blue, #1565C0): 50% or higher. ",
        "<span style=\"display: inline-block; width: 10px; height: 10px; background-color: #42A5F5; border-radius: 2px;\"></span> <strong>Not At Risk</strong> (light blue, #42A5F5): below 50%.<br>\n",
        "The same colours and order (At Risk, then Not At Risk) are used on every chart. Score ranges run from lowest to highest.\n",
        "</div>"
      ]
    }
  },
  "position": {"x": 0, "y": 2, "width": 12, "height": 3}
}
```

Every other layout item with `position.y >= 2` moves down by 3 (`y + 3`); `x`, `width` and
`height` are unchanged. After the move no two widgets overlap.

Required content (asserted offline): the strings `How to read this dashboard`, `At Risk`,
`Not At Risk`, `50%`, `#1565C0`, `#42A5F5`.

## 6. Expected widget titles (offline and live checks)

`Total Students`, `At Risk`, `Not At Risk`, `Risk Level Distribution`, `Risk Score Distribution`,
`Student Details`, `Risk by Age Band`, `Risk by Gender`, `Risk by Origin`, `Filter by Risk Level`,
`Filter by Risk Flag`, `Search Student`. A title is read from `spec.frame.title.value`, or from
`spec.frame.title` when it is a plain string (`filter_faculty`).

## 7. Advisor page badge (`student_attrition_risk_app/src/student_attrition_risk/ui.py`)

| Rule | Property | Before | After |
|---|---|---|---|
| `.risk-badge` | `background` | `#fee4e2` | `#1565C0` |
| `.risk-badge` | `color` | `#b42318` | `#FFFFFF` (5.75:1) |
| `.not-risk-badge` | `background` | `#dcfae6` | `#42A5F5` |
| `.not-risk-badge` | `color` | `#067647` | `#172033` (6.15:1) |

Unchanged: every other property of both rules, the label text (`At Risk` / `Not At Risk`), the
class choice (`attrition_risk_flag`), and the page-owned `<span>` markup. No `st.info`,
`st.success`, `st.warning` or `st.error` is introduced.

### 7a. Relative-risk score circle (added 2026-10-01, spec decision 10, FR-024)

The circle keeps its ring shape (8px border, white fill, 92px, and the unchanged 76px media-query
size) and takes the category colours. Text contrast is measured against the white fill.

| Rule | Property | Before | After |
|---|---|---|---|
| `.risk-circle` | `border` | `8px solid #d92d20` | `8px solid #1565C0` |
| `.risk-circle` | `color` | `#d92d20` | `#1565C0` (5.75:1 on white) |
| `.risk-circle` | `background` | `white` | `white` (unchanged) |
| `.risk-circle.not-risk-circle` (new rule) | `border-color` | — | `#42A5F5` |
| `.risk-circle.not-risk-circle` (new rule) | `color` | — | `#172033` (16.3:1 on white) |

Markup: a `circle_class` variable chosen from `attrition_risk_flag` (`"risk-circle"` or
`"risk-circle not-risk-circle"`) replaces the fixed `class="risk-circle"` on the score `<div>`.
The badge logic and the score value are unchanged.

### 7b. Student summary card edge (added 2026-10-01, spec decision 11, FR-025)

| Rule | Property | Before | After |
|---|---|---|---|
| `.summary-card` | `border-left` | `5px solid #d92d20` | `5px solid #1565C0` |
| `.summary-card.not-risk-card` (new rule) | `border-left-color` | — | `#42A5F5` |

Markup: a `card_class` variable chosen from `attrition_risk_flag` (`"summary-card"` or
`"summary-card not-risk-card"`) replaces the fixed `class="summary-card"`. Every other property of
the card is unchanged. Error notices (for example `.store-error-notice`) stay red.
