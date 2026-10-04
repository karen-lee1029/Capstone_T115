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


# Code review dispositions (2026-10-04)

Source: independent Codex code review of `f745a62`
(`hive/agents/codex-code-reviewer-mutdf98m/handoffs/US-29/Code_Independent_Review_Handoff.md`).
Recommendation: Request changes (P2 × 2, P3 × 1).

| Finding | Disposition | Changes |
|---|---|---|
| **CODE-01** (P2) Table selections were exempted from the Q6 checks | **Accepted.** The official filter docs (updated 2026-10-02) list Table as a cross-filter source, so research R-8's "tables emit no selections" was wrong. It came from an older community article. The Student List table is the only data widget on its page. The Demographic Breakdown table shows Gender (Q9) beside the Age Band and Origin charts, so a selection in it could narrow them. The only documented suppression ("Ignored filters") works per source widget, not per column, so every fix changes design or needs workspace work. Sent to the product owner as **Q21**; not implemented yet. | research R-8 corrected; spec FR-004 and contract C-1 mark the table rule pending; test comment updated |
| **CODE-02** (P2) Offline checks validated aliases, not bindings | **Accepted and fixed.** New `test_filter_binding_is_complete` (8 cases) checks each filter's query fields, expressions, query name and encoding as one binding. `_filter_dimensions` reads expressions and encodings too, so the sensitive-filter check catches an expression bound to gender. `test_drill_table_columns_match_contract` checks every column's expression. The reviewer's three faults now each fail a test (see Implementation_Handoff.md). | `tests/test_dashboard_filtering.py` |
| **CODE-03** (P3) Acceptance text said four pages | **Accepted and fixed.** SC-001 and matrix rows A1 – A2 (and A3 – A8 through "As A2") name all 5 canvas pages, Gender Breakdown included. | spec SC-001, quickstart |
| Stale R-2 wording (assurance limits) | **Accepted and fixed.** R-2 now says "not yet verified" and points to the A1 – A11 gate, with no fallback. | research R-2 |

## Q21 (CODE-01) — Stopping a selection in the Demographic Breakdown table from narrowing by Gender

Evidence: the official [filter docs](https://docs.databricks.com/aws/en/dashboards/manage/filters/)
(updated 2026-10-02) list Table as a cross-filter source and describe an **Ignored filters** setting
on the receiving widget, per source widget. They do not say which column a table click filters by.
`drill_table_demographic` shares its page with `eaf7eaf4` Risk by Age Band and `292bc630` Risk by
Origin. No workspace test has been run. Q6 stays binding, and Q9 requires the Gender column.

- **a) Test, then suppress if needed** (recommended). With the product owner's permission, the agent
  first adds the Ignored filters setting to the existing "US29 format probe" through the API to learn
  its exact JSON. It then sets Risk by Age Band and Risk by Origin to ignore `drill_table_demographic`
  as a cross-filter source. The table keeps Gender, still follows chart clicks and global filters,
  and its own clicks narrow nothing. A new matrix row (B7) gives the negative evidence. Cost: a
  setting on two of Karen's charts (logged), one workspace write to the probe, and losing table →
  chart filtering on that page (no answer requires it).
- **b) Observe first, change only if it leaks.** The product owner publishes and clicks a Gender cell
  (B7). If nothing narrows, record that behaviour and its deployment scope, with no change. If it
  narrows, apply (a). Cost: the outcome stays open until the workspace check.
- **c) Remove Gender from the Demographic Breakdown table.** Cost: reverses Q9.

### Outcome (2026-10-04)

- **Q21 = a.** One approved API write to the probe added candidate keys. Inconclusive: the server keeps
  any unknown key inside a widget `spec`, so a surviving key proves nothing.
- The product owner then looked for the option in the workspace editor: **no "Ignored filters"
  option is offered.**
- **Q22 = a** (try the dashboard authoring assistant once, else fall back to Q21 option b). The
  assistant reported that its `setIgnoredFilters` operation is rejected by its own schema, that
  `ignoredFilters` in the query is stripped, and that `ignoredFilters`, `ignoredSources` and
  `filterExclusions` in the chart spec are rejected as unknown properties.
- **Resolved as Q21 option b (observe first).** The dashboard is unchanged; Karen's charts are not
  touched. The offline test names `drill_table_demographic` as the only table allowed to share a page
  while showing a sensitive field, so any other such table fails. Matrix row B7 gives the workspace
  evidence. If B7 shows narrowing, Q6 is broken and the question returns to the product owner.

# Workspace acceptance round 2 (2026-10-05)

The product owner published `a5245c1` and ran the matrix (results in Implementation_Handoff.md).
Read-only diagnosis found three causes:

1. **Faculty and Study Mode only list null**: the source columns are NULL in every row. This is
   not a dashboard fault.
2. **UNRESOLVED_COLUMN on every chart** for the enrolment filters: their condition is applied to
   queries that hold only prediction columns. The design relied on relationship filter propagation
   (research R-2, unverified), which Databricks lists as Public Preview (3 and 10 Sep 2026).
3. **Chart clicks highlight but do not narrow**: inferred to be the same propagation limit.

Decisions: **Q23 = a** (an admin checks the two previews, then A rows are re-run). **Q24 = a with
the product owner's rule** (remove any filter that only shows null or errors). Faculty and Study
Mode are removed. The four erroring enrolment filters, plus Field of Education (bound the same
way, not reported), are removed too if they still error after the preview check.

### Outcome of Q23 and Q25 (2026-10-05)

Q23 = a: the product owner found no Previews page (the user menu, Settings and the direct URL were
all checked) and confirmed the workspace is Databricks Free Edition. The account is a workspace
admin. **Q25 = a**: the five enrolment fields are joined into the prediction dataset's source, and
all six filters bind to it. A read-only check shows the joined query returns 973,770 rows, one per
student, with every filter field filled. This is a C-5 exception for Karen's dataset (TC-4).

### Q26 (2026-10-05)

Round 3 showed every filter passing, but chart clicks on Course Analysis and Demographic Breakdown
raised "Filter expression references multiple sources". Those charts mixed an enrolment-dataset axis
with the prediction-dataset Risk Level colour. **Q26 = a**: they and the two drill tables now take
their enrolment fields from the joined prediction source. The Overview Risk Score Range click, which
uses only prediction fields, already worked (B6).
