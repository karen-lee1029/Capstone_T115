# Feature Specification: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Feature Branch**: `feat/feature-005-enhanced-risk-visualisation`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "Feature-005 — Enhanced Student Risk Visualisation (US-28). As an
Academic Advisor, I want student attrition-risk information to be presented through clear and
consistent visualisations, so that I can more easily interpret and compare student risk
information when reviewing students. Surfaces are the Student Risk Overview dashboard and the
risk badge on the advisor page. Keep two risk categories split at 50%, labelled At Risk / Not At
Risk everywhere, with the existing dashboard blues; ordered score ranges; a how-to-read panel
and a description on every chart; tests in Karen's approved dashboard test file and one new
badge test file; teammate edits recorded with revert instructions."

## Overview

Feature-005 is **Product Backlog US-28 — Enhanced Student Risk Visualisation**. The approved
user story and acceptance criterion state:

> As an Academic Advisor, I want student attrition-risk information to be presented through
> clear and consistent visualisations, so that I can more easily interpret and compare student
> risk information when reviewing students.
>
> **Given** student attrition-risk results are available in the Databricks application, **when**
> an Academic Advisor views the Student Risk Overview, **then** risk information is presented
> using clear visualisations with consistent risk categories, chart ordering, labels and
> explanations.

US-28 is **Should Have**, 5 story points, planned for Sprint 6. It is **approved Enhanced scope**:
it is required for the project's marks and is delivered alongside, but separately from, the
base-scope final application story (US-21).

Today the risk information is presented on two surfaces that do not agree with each other:

- **The Student Risk Overview dashboard** labels its two categories "High" and "Low" (and its
  counters "High Risk" and "Low Risk"). These names are left over from an earlier three-level
  design that also had "Medium"; the model and the advisor application only ever produce two
  outcomes, "At Risk" and "Not At Risk". Three of the five charts carry no explanation, the score
  ranges have no guaranteed order, and nothing on the page says what the categories or colours
  mean.
- **The advisor page risk badge** says "At Risk" / "Not At Risk", but in red and green, while the
  dashboard uses two blues for the same two categories.

Feature-005 delivers three things:

- **One vocabulary.** The two risk categories are called "At Risk" and "Not At Risk" on every
  dashboard counter, chart, legend, filter value and table cell, and on the advisor page badge.
- **One visual language.** Each category has one colour, used on every chart and on the badge;
  categories and score ranges always appear in one documented order.
- **Explanations where the advisor looks.** A "How to read this dashboard" panel explains the
  categories, the 50% threshold and the colours, and every chart carries a one-line description.

Feature-005 changes presentation only. It does not change how a student is scored, which
students are at risk, the number of categories, the score ranges, or any briefing behaviour.

## Backlog Alignment

| Backlog story | Owns | Feature-005's relationship |
|---|---|---|
| US-08 | Application backend | Merged (Feature-001). Supplies the at-risk flag the badge reads; unchanged. |
| US-12 – US-15 | Briefing instructions, generation, validation, retry and storage | Merged. Briefing text and its wording are not touched. |
| US-17 | Dashboard and application testing | Karen's dashboard test file is updated, with team approval, so it describes the renamed categories and checks the repository dashboard definition offline. |
| US-18, US-20 | Workflow testing, defect resolution | Merged (Feature-003, Feature-004). Their verification must keep passing; none of it is edited. |
| US-21 | Base-scope final application | Separate story. Feature-005 is Enhanced scope and is not counted inside US-21. |
| US-27, US-29 | Other Enhanced stories | Out of scope for Feature-005. |
| **US-28** | Enhanced student risk visualisation | **This feature.** |

## Clarifications

### Session 2026-10-01 (confirmed Feature-005 scope decisions)

The following decisions were settled with the product owner before specification. They are
authoritative for this specification and are not re-opened.

- Q: Which surfaces does "the Student Risk Overview" cover? → A: Two. The Student Attrition Risk
  Overview dashboard published in the Databricks workspace (its definition is kept in the
  repository), and the risk badge on the advisor page of the Databricks application.
- Q: How many risk categories, and what are they called? → A: Exactly two, split at an attrition
  risk percentage of 50% (50% or higher is at risk), matching the backend's at-risk flag. They are
  labelled "At Risk" and "Not At Risk" everywhere: the category definition behind the dashboard,
  both counter titles, the counter filters, the risk-level filter values, the table column values
  and the colour legend of all five charts. "High" / "Low" is obsolete naming from a former
  three-level design and is removed.
- Q: Which colours? → A: The dashboard's existing blues, used consistently on every chart: At Risk
  = `#1565C0` (dark blue), Not At Risk = `#42A5F5` (light blue). The advisor page badge is
  recoloured to the same two blues, with a text colour on each that gives a contrast ratio of at
  least 4.5:1 (WCAG AA). The badge keeps its wording ("At Risk" / "Not At Risk") and its logic. It
  stays a page-owned element in the existing palette approach; no built-in alert widget is used.
- Q: What happens to the Risk Score Distribution? → A: Its eight data-driven score ranges are kept
  unchanged (0-46, 46-48, 48-49, 49-50, 50-51, 51-52, 52-54, 54-100%). They are always shown in
  ascending order with clear percentage labels. Risk categories appear in one documented order
  (At Risk, then Not At Risk) on every chart and legend.
- Q: What explanations are added? → A: One "How to read this dashboard" text panel covering the
  two categories, the 50% threshold and the two colours, plus a one-line description on every
  chart.
- Q: Where are the tests? → A: The team approved editing Karen's dashboard test file: its category
  constants, its expected widget titles and its replica of the category rule are updated to the
  new labels, and offline checks are added that read the repository dashboard definition. Badge
  tests go in one new test file. Karen's advisor-interface test file stays unchanged and passing.
  No other merged test file is modified.
- Q: What is in scope? → A: US-28 only. US-27 and US-29 are out of scope. The wording of
  generated briefings (briefing provider, briefing instructions, briefing validation) is out of
  scope.
- Q: Who publishes the dashboard? → A: The development agents edit only the dashboard definition
  in the repository. The product owner imports or replaces and publishes it in the Databricks
  workspace, following step-by-step instructions in the quickstart, and captures screenshots as
  evidence in a light, professional style.
- Q: Which teammate contributions may change, and how is that recorded? → A: Three, each approved:
  GuaGuaGua88's badge styling on the advisor page; the dashboard definition (Owner: Renny (the
  user), confirmed 2026-10-01; recorded for revert purposes only); and Karen's dashboard test file.
  Every change to them is recorded in `teammate-changes.md` with file and lines, original author
  and commit, what changed and why, the commit that made it, and exact revert instructions, so the
  product owner can revert quickly if a teammate is unhappy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent risk categories and colours on the dashboard (Priority: P1) 🎯 MVP

An Academic Advisor opening the Student Risk Overview sees the same two categories, with the same
names and the same colours, on every counter, chart, legend, filter and table row, and those names
match what the advisor application says about a student.

**Why this priority**: This is the core of US-28's criterion ("consistent risk categories ... and
labels"). The legacy "High" / "Low" names imply a scale the model does not produce and disagree
with the advisor application, which is the most likely source of misinterpretation.

**Independent Test**: Read the repository dashboard definition offline: the category rule yields
only "At Risk" (50% or higher) and "Not At Risk" (below 50%); both counters are titled and filtered
with those names; all five charts map "At Risk" to `#1565C0` and "Not At Risk" to `#42A5F5`; no
"High", "Low" or "Medium" category value remains.

**Acceptance Scenarios**:

1. **Given** a student with an attrition risk percentage of 50% or higher, **When** the advisor views
   the dashboard, **Then** the student is counted, charted, filtered and listed as "At Risk".
2. **Given** a student below 50%, **When** the advisor views the dashboard, **Then** the student is
   counted, charted, filtered and listed as "Not At Risk".
3. **Given** the two category counters, **When** the advisor reads them, **Then** they are titled
   "At Risk" and "Not At Risk", and together with the total they still add up (total = At Risk + Not
   At Risk).
4. **Given** any of the five charts, **When** the advisor reads its legend, **Then** "At Risk" is
   dark blue `#1565C0` and "Not At Risk" is light blue `#42A5F5`.
5. **Given** the risk-level filter, **When** the advisor opens it, **Then** it offers "At Risk" and
   "Not At Risk" and nothing else.

---

### User Story 2 - Charts are ordered and explained (Priority: P2)

An Academic Advisor can read any chart without prior knowledge: score ranges run from lowest to
highest, categories always appear in the same order, every chart says what it shows, and one panel
explains the categories, the threshold and the colours.

**Why this priority**: It covers the "chart ordering ... and explanations" part of the criterion. It
builds on the vocabulary of User Story 1, so it comes second.

**Independent Test**: Read the repository dashboard definition offline: a text panel titled "How to
read this dashboard" exists and mentions both categories, 50% and both colours; every chart shows a
non-empty description; the score-range axis is ordered ascending and its eight labels each end in
"%"; category order is At Risk then Not At Risk.

**Acceptance Scenarios**:

1. **Given** the Risk Score Distribution, **When** the advisor reads it, **Then** the eight ranges
   appear in ascending order from 0-46% to 54-100%, each labelled with a percentage.
2. **Given** any chart that shows both categories, **When** the advisor reads it, **Then** At Risk
   appears before Not At Risk in the legend and, where categories form an axis, on that axis.
3. **Given** any of the five charts, **When** the advisor looks at it, **Then** a one-line
   description under its title says what it shows.
4. **Given** the dashboard opens, **When** the advisor looks near the top of the page, **Then** a
   "How to read this dashboard" panel explains the two categories, the 50% threshold and which blue
   means which category.

---

### User Story 3 - The advisor page badge matches the dashboard (Priority: P3)

When an Academic Advisor opens a student on the advisor page, the risk badge uses the same colour
for the same category as the dashboard, and its text stays readable.

**Why this priority**: It extends consistency to the second surface. It is independent of the
dashboard work and smaller in impact, so it ranks third.

**Independent Test**: Load an at-risk and a not-at-risk synthetic student on the advisor page
offline: the badge reads "At Risk" on dark blue and "Not At Risk" on light blue, each text colour
has a contrast ratio of at least 4.5:1 with its background, and no built-in alert widget is used.

**Acceptance Scenarios**:

1. **Given** an at-risk student, **When** the advisor opens the student, **Then** the badge reads
   "At Risk" on `#1565C0` with readable text (contrast at least 4.5:1).
2. **Given** a not-at-risk student, **When** the advisor opens the student, **Then** the badge reads
   "Not At Risk" on `#42A5F5` with readable text (contrast at least 4.5:1).
3. **Given** either student, **When** the page is rendered, **Then** which badge is shown is decided
   exactly as before, and the existing advisor-interface verification still passes unchanged.

---

### User Story 4 - The product owner can publish, evidence and revert (Priority: P4)

The product owner needs to put the updated dashboard live in the workspace, capture evidence for
assessment, and be able to undo any change to a teammate's contribution quickly.

**Why this priority**: It turns the repository changes into a published, evidenced result and
protects team relationships, but has value only once Stories 1–3 exist.

**Independent Test**: Follow the quickstart's publish steps end to end on the workspace; open
`teammate-changes.md` and confirm every changed teammate file has a complete entry including revert
instructions; open the traceability record and confirm each requirement maps to a test or a manual
evidence step.

**Acceptance Scenarios**:

1. **Given** the updated repository dashboard definition, **When** the product owner follows the
   quickstart, **Then** the dashboard is replaced and published in the workspace and shows the new
   labels, colours, order and explanations.
2. **Given** a teammate is unhappy with a change, **When** the product owner follows that entry's
   revert instructions, **Then** the teammate's original content is restored without affecting the
   other entries.
3. **Given** the finished feature, **When** a reviewer reads the traceability record, **Then** every
   functional requirement names the automated check or manual evidence that verifies it.

---

### Edge Cases

- **A student at exactly 50.0%**: At Risk (the rule is "50% or higher").
- **A student at 49.95%**: Not At Risk on the dashboard, even though the table's rounded-down
  "Risk %" shows 49.9.
- **A category with no students under the current filters**: the counter shows 0 and the chart
  simply omits that bar; colour and order of the remaining category are unchanged.
- **A score-range label that would sort wrongly as text** (e.g. "54-100%" after "52-54%"): the
  ascending order is set explicitly, not left to text sorting.
- **The dashboard definition is published in the workspace with older content**: the repository
  definition is the source of truth; the quickstart replaces the published copy.
- **The workspace dashboard file is not reachable from a test run**: the existing live check is
  skipped as today; the new offline checks read the repository definition and always run.
- **The at-risk flag and the 50% split disagree for a student** (only possible if a student's
  decision threshold is not 50%): the dashboard follows the percentage rule and the badge follows
  the flag, each exactly as before. See Assumptions.
- **A teammate rejects a change after merge**: the matching `teammate-changes.md` entry is reverted
  on its own, except that the dashboard definition and the dashboard checks that assert it are reverted together (their entries name each other).

## Requirements *(mandatory)*

### Functional Requirements

#### Risk categories and labels

- **FR-001**: The dashboard MUST present exactly two risk categories, "At Risk" (attrition risk
  percentage of 50% or higher) and "Not At Risk" (below 50%).
- **FR-002**: The category names "High", "Low" and "Medium" MUST NOT appear as a category value,
  counter title, filter value or legend entry anywhere on the dashboard.
- **FR-003**: The two category counters MUST be titled "At Risk" and "Not At Risk" and MUST count
  only students in that category; the total-students counter MUST remain unchanged.
- **FR-004**: The risk-level filter and the table's risk-level column MUST show the values "At Risk"
  and "Not At Risk".
- **FR-005**: The advisor page badge MUST keep its wording ("At Risk" / "Not At Risk") and MUST
  decide which badge to show exactly as it does today.

#### Colours

- **FR-006**: Every dashboard chart that distinguishes the categories MUST colour "At Risk" as
  `#1565C0` and "Not At Risk" as `#42A5F5`; all five charts MUST use the same mapping.
- **FR-007**: The counters MUST use the same colour as their category.
- **FR-008**: The advisor page "At Risk" badge MUST use background `#1565C0` and the "Not At Risk"
  badge MUST use background `#42A5F5`, each with a text colour giving a contrast ratio of at least
  4.5:1.
- **FR-009**: The badge MUST remain a page-owned element styled by the page; built-in alert widgets
  MUST NOT be used.

#### Ordering

- **FR-010**: The eight score ranges MUST keep their current boundaries and MUST be displayed in
  ascending order, each labelled with a percentage.
- **FR-011**: Wherever both categories appear (legend or axis), they MUST appear in one documented
  order: "At Risk" then "Not At Risk".

#### Explanations

- **FR-012**: The dashboard MUST include one text panel titled "How to read this dashboard" that
  explains the two categories, the 50% threshold and which colour represents which category.
- **FR-013**: Every dashboard chart MUST show a non-empty one-line description of what it shows.
- **FR-014**: Explanatory text MUST use the same category names, threshold and colours as the
  charts.

#### Verification

- **FR-015**: The dashboard test file MUST describe the renamed categories (constants, expected
  titles, category replica) and MUST include offline checks that read the repository dashboard
  definition and verify FR-001–FR-004, FR-006, FR-007 and FR-010–FR-013.
- **FR-016**: Badge colour, contrast and wording MUST be verified offline in one new test file.
- **FR-017**: Karen's advisor-interface test file and every other merged test file except the
  dashboard test file MUST remain unchanged, and the full verification suite MUST pass.
- **FR-018**: Every verification MUST run without access to any external service, workspace or
  network; checks that need the workspace keep their existing skip behaviour.

#### Scope, publishing and team contributions

- **FR-019**: Feature-005 MUST NOT change how students are scored or flagged, the score-range
  boundaries, briefing wording, or anything belonging to US-27 or US-29.
- **FR-020**: Development MUST change only the repository dashboard definition, the badge styling,
  the dashboard test file, the new badge test file and this feature's documents.
- **FR-021**: The quickstart MUST give the product owner step-by-step instructions to import or
  replace and publish the dashboard in the workspace and to capture light, professional screenshot
  evidence.
- **FR-022**: Every change to a teammate's contribution MUST be recorded in `teammate-changes.md`
  with file and lines, original author and commit, what changed and why, the commit that made it,
  and exact revert instructions.
- **FR-023**: A traceability record MUST map every functional requirement to the automated check or
  manual evidence that verifies it.

### Key Entities

- **Risk category**: One of "At Risk" or "Not At Risk", derived from a student's attrition risk
  percentage at a 50% threshold. Carries a label, a colour and an order position.
- **Score range**: One of eight fixed percentage bands with a label and an ascending position.
- **Dashboard explanation**: The "How to read this dashboard" panel and each chart's description.
- **Teammate change record**: One entry per changed teammate contribution, with its revert path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of category labels on the dashboard and badge read "At Risk" or "Not At Risk"; 0
  occurrences of "High", "Low" or "Medium" as a category value remain.
- **SC-002**: 5 of 5 charts and 2 of 2 category counters use the same colour for the same category.
- **SC-003**: The 8 score ranges appear in ascending order 100% of the time.
- **SC-004**: 5 of 5 charts carry a description, and 1 "How to read this dashboard" panel exists.
- **SC-005**: Both badge text colours reach a contrast ratio of at least 4.5:1.
- **SC-006**: An advisor can say which colour means At Risk and what the threshold is from the
  dashboard alone, without outside explanation.
- **SC-007**: The full verification suite passes with 0 failures; Feature-005 introduces 0 new lint findings.
- **SC-008**: 0 merged test files other than the approved dashboard test file are changed; 100% of
  changed teammate contributions have a complete `teammate-changes.md` entry.
- **SC-009**: The published workspace dashboard matches the repository definition, evidenced by
  screenshots.

## Assumptions

- Every scored student's decision threshold is 50%, so the 50% split used by the dashboard and the
  at-risk flag used by the badge agree. The badge logic is not changed either way.
- The repository dashboard definition at commit `9469edc` is the current published design.
- The dashboard platform honours an explicit ascending sort on a category axis and the order of the
  colour mapping in legends; the product owner confirms this visually when publishing.
- The table's "Risk Flag" column (the model's flag) is unchanged; only the "Risk Level" values are
  renamed.
- The advisor page's relative-risk score circle is not part of the badge and keeps its colour.

## Dependencies

- **Feature-001 (US-08)** — supplies the at-risk flag and percentage. Unchanged.
- **Karen's dashboard tests (US-17)** — updated with team approval.
- **GuaGuaGua88's advisor page styling** — the badge rules are recoloured with approval.
- **The dashboard definition** — committed by Renny in `9469edc`. Owner: Renny (the user),
  confirmed 2026-10-01.
- **The product owner** — publishes the dashboard in the workspace and captures evidence.

## Out of Scope

- US-27, US-29 and the base-scope final application story US-21.
- Briefing wording or behaviour (briefing provider, instructions, validation, retry, storage).
- Changing the scoring model, the at-risk flag, the 50% threshold or the score-range boundaries.
- A third category or a new chart type.
- The advisor page's relative-risk score circle and any styling other than the two badge rules.
- Publishing the dashboard by an agent; any change to the workspace other than by the product owner.
- Editing any merged test file other than the approved dashboard test file.
