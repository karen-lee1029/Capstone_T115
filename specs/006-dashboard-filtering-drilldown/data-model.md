# Data Model: Feature-006 (US-29)

Feature-006 adds **no** data. It reuses existing dimensions and measures unchanged (FR-013, FR-016).

## Reused fields

| Dataset | Dimension / measure | Used by |
|---|---|---|
| P | `risk_level` ("At Risk" ≥ 50%, else "Not At Risk") | Filter by Risk Level; all tables |
| P | `student_id` (`LEFT(hash, 16)`, "Student ID (de-identified)") | all tables |
| P | `risk_pct` | all tables; sort key |
| P | `risk_score_bucket` | Overview table |
| P | `count` | counters, charts (unchanged) |
| P (joined, Q25) | `enrol_course_level`, `enrol_field_of_education`, `enrol_origin`, `enrol_age_band`, `enrol_commencing_continuing` | filters (Faculty and Study Mode removed, Q24); one row per student, 973,770 rows, every value filled (read-only check 2026-10-05) |
| E | `course_level`, `broad_primary_field_of_education` | Course Analysis table |
| E | `age_band`, `gender`, `international_domestic` | Demographic Breakdown table |

## Interaction entities (presentation only)

- **Dashboard-wide filter**: `{widget, title, dataset, dimension}`; selection = set of values,
  empty = all; applies to every page.
- **Chart selection**: platform-held, per page, transient; shown in the active filter bar.
- **Effective student set** on a page = matches every dashboard-wide filter AND the page's chart
  selection AND (Student List only) Search Student.

## Invariants

- Total = At Risk + Not At Risk for any effective set.
- One table row per student (`disaggregated: true`).
- A student with no E row is excluded once any E filter is set (Q12).
