# Review Dispositions: Feature-006 SDD (US-29)

Source: independent Codex SDD review by Pam, 2026-10-04
(`hive/agents/pam-mutfxxzb/handoffs/US-29/SDD_Independent_Review_Handoff.md`), against commit
`d2be96d`. Recommendation: Request changes (P2 × 4, P3 × 1).

## Dispositions

| Finding | Disposition | SDD changes |
|---|---|---|
| **SDD-01** (P2) Gender chart clicks would narrow other widgets, contradicting Q6 | **Accepted.** Q6 applies to every interaction path, including chart selections. Q6 *can* be enforced while keeping the Gender display (research R-8: tables emit no selections; cross-filters are page-scoped). There is more than one compliant layout, and each changes a teammate's visible layout, so the choice goes to the product owner as **Q16**. | spec FR-004 (a)+(b), FR-008, FR-009, SC-004, edge case; contract C-1 note; plan test plan + R-7; quickstart B4 negative evidence; tasks T011a ⏸ |
| **SDD-02** (P2) The 100,000-row table rendering limit contradicts the "no student hidden" promise | **Accepted.** The completeness promise is withdrawn. No supported native design gives in-table access to all ~974,000 students. The access contract is a product decision, so it goes to **Q17**. | spec FR-012, edge case; contract C-2 and C-3; plan D-4 + R-8; quickstart C3/C4; traceability; tasks T014 ⏸ |
| **SDD-03** (P2) The filter-reach fallback was ineffective and conflicted with preservation | **Accepted.** All 11 existing data widgets already use graph queries. The fallback is withdrawn and replaced by a verification-and-escalation gate. C-5 stays unconditional. | plan D-2, R-2; spec edge case and assumption |
| **SDD-04** (P2) Acceptance evidence omitted combinations and cases | **Accepted.** | quickstart rewritten as a workspace acceptance matrix A0 – D4 (all 8 fields, multi-value, intersection, chart + filter, independent clearing, every page, Search Student + filters, empty result, missing enrolment, > 100,000 boundary), with a pending-not-passed rule; traceability re-mapped |
| **SDD-05** (P3) Constitution Check omitted VII, IX, XI, XV | **Accepted.** | plan Constitution Check now covers all 17 principles |
| Review item 3: live check `tests/test_dashboard.py:366` asserts one page | **Needs a decision.** It sits outside the 24 authorised repairs (it is skipped offline, so it was not among them). Goes to **Q18**. | tasks T003 ⏸ |

## Decisions requested from the product owner

**Answered 2026-10-04 by the product owner: Q16 = a, Q17 = a, Q18 = a** (spec Clarifications).

### Q16 (SDD-01) — Stopping a click on Risk by Gender from narrowing other widgets

Evidence: chart `52cb0fd3` queries `Student_Enrolment_Details.gender` through the shared graph (definition line ~980–995). Cross-filtering acts on other widgets *on the same page*. Tables emit no selections (research R-8). No documented per-chart switch turns cross-filtering off.

- **a) Move Risk by Gender to its own page ("Gender Breakdown") with no other data widget** (recommended). The chart is unchanged: same colours, description, and global filters. A click has nothing to narrow. Cost: Karen's Demographic Breakdown layout changes, logged as a teammate change. The Feature-005 checks are unchanged apart from the chart's page.
- **b) Replace the bar chart with a small table of counts by gender and risk level.** Tables emit no selections. Cost: the bar visual is lost, and the Feature-005 colour checks drop to six charts.
- **c) Remove the Risk by Gender chart.** Gender then appears only as a column in the Demographic Breakdown table (Q9). Cost: the aggregate gender view is lost.
- **d) Keep the chart in place and turn its cross-filtering off,** but only if the workspace export (R-3) shows a supported setting for it. Otherwise apply the alternative named in the answer. Cost: this depends on an undocumented setting.

### Q17 (SDD-02) — What the "Students in this view" tables promise

Evidence: the platform renders at most 100,000 table rows, a rendering limit distinct from any query limit ([Dashboard limits](https://docs.databricks.com/aws/en/dashboards/limits)). Unfiltered there are about 974,000 students. Any individual is reachable through Student List → Search Student.

- **a) Bounded: up to 100,000 students, highest risk first** (recommended). There is no query limit. The description and help panel say: "Shows up to 100,000 students in this view, highest risk first. Narrow with filters or a chart selection to see others; find any student by ID on Student List." Matrix row C4 verifies the boundary and the sort.
- **b) Bounded to an explicit smaller "Top N"** (for example N = 1,000; please give N). There is an explicit row cap, and the title or description says "Top N highest-risk students in this view", with the same narrowing guidance. It is easier to read and quicker to load.
- **c) Full-population access is required.** No supported native table design was found. Meeting it would need a new feature outside the 15 answers (for example, an export), which would be a scope change.

For a and b: if the workspace shows that truncation happens before the sort, implementation stops and escalates.

### Q18 (review item 3) — The live, workspace-only one-page check

Evidence: `tests/test_dashboard.py:366` `test_has_one_page_named_overview` asserts exactly one page named Overview. It runs only with workspace access (skipped offline). It already fails against the four-page base and would fail against the added Filters page.

- **a) Leave it unchanged** (recommended). Record that a workspace-connected run would fail it, as a pre-existing defect outside the 24 repairs. The offline suite is green, and the handoff says so explicitly.
- **b) Authorise a narrow repair.** It would assert the published page list: Overview, Course Analysis, Demographic Breakdown, Student List and Filters, plus the Q16 page if Q16 = a. It would be logged as a teammate change to Karen's test.
- **c) Remove that one live test.** It would be logged as a teammate change.
