# Phase 1 Prompt: Fact-Centred STAR-Schema Feature Assembly

Use this only after reading `AI_AGENT_MASTER_PROMPT.md` and the five controlling SDD files.

## Objective

Implement only the source audit and fact-centred feature-assembly sections of `student_attrition_machine_learning.py`. Do not create train, validation, or test splits. Do not train a model. Do not write the prediction Delta table.

## Authoritative modelling spine

Begin from:

`workspace.student_aggregate.rpt_student_management__fact__all_enrolment_eftsl__deidentified`

Every candidate modelling row must originate from this fact table.

## Source inventory

Profile these 12 generated Delta tables:

1. `workspace.student_aggregate.rpt_student_management__fact__all_enrolment_eftsl__deidentified`
2. `workspace.student_aggregate.dwh_learning_and_teaching__teaching_period`
3. `workspace.student_aggregate.dwh_curriculum__course`
4. `workspace.student_aggregate.dwh_curriculum__course_offering`
5. `workspace.student_aggregate.dwh_curriculum__module`
6. `workspace.student_aggregate.dwh_curriculum__module_offering`
7. `workspace.student_aggregate.dwh_curriculum__unit`
8. `workspace.student_aggregate.dwh_curriculum__unit_offering`
9. `workspace.student_aggregate.dwh_curriculum__thesis`
10. `workspace.student_aggregate.dwh_curriculum__study_area_a`
11. `workspace.student_aggregate.dwh_curriculum__study_area_b`
12. `workspace.student_aggregate.dwh_internal_organisation__mapped_academic_organisation_hierarchy`

For each table, implement code that records:

- existence and readability;
- schema;
- row count;
- candidate primary or business key;
- null-key count;
- duplicate-key count;
- populated and all-null columns;
- possible relationship to the fact table;
- candidate prediction-time-valid attributes.

## Fact-grain validation

Validate:

- fact row count;
- non-null `student_deidentified_hash` and `enrolment_deidentified_hash`;
- distinct student count;
- distinct enrolment count;
- target availability;
- whether the current source contains exactly one eligible fact row per student.

If multiple fact rows occur for one student, stop Phase 1 and report the problem. Do not use `dropDuplicates()`, `distinct()`, first-row selection, arbitrary aggregation, or a latest-row assumption without human approval.

## Join map

Verify actual schemas before implementing these expected relationships:

- fact `course_key_hash` to course `course_key_hash`;
- fact `course_offering_key_hash` to course offering `course_offering_key_hash`;
- fact `curriculum_item_key_hash` to unit `unit_key_hash`;
- fact `curriculum_item_offering_key_hash` to unit offering `unit_offering_key_hash`;
- fact `study_area_a_key_hash` to study area A `study_area_a_key_hash`;
- fact `study_area_b_key_hash` to study area B `study_area_b_key_hash`;
- fact `academic_organisation_hierarchy_key_hash` to organisation `academic_organisation_hierarchy_key_hash`;
- fact `teaching_period_key_hash` to teaching period `teaching_period_key_hash`.

Profile module, module-offering, and thesis tables. Do not join them unless a verified relationship exists and cannot multiply fact rows.

## Join contract

For every proposed dimension join:

1. confirm both join columns exist and have compatible types;
2. confirm the dimension key is unique;
3. select only the join key and approved attributes;
4. rename selected attributes to source-qualified staging names before joining;
5. prohibit `select("*")` and wildcard enrichment;
6. perform a left join from the fact-centred DataFrame;
7. compare row count before and after;
8. compare distinct student count before and after;
9. record matched and unmatched key counts;
10. assert that no duplicate column names were introduced;
11. stop on any row multiplication, changed student count, duplicate key, or ambiguity.

Do not hide a failed join through deduplication.

## Canonical feature ownership

Create a feature manifest with one canonical source for each feature concept. Initial ownership is:

- demographics and student status: fact table;
- EFTSL and cumulative credit points: fact table;
- commencing or continuing status: fact table;
- teaching-period and calendar attributes: teaching-period dimension;
- course group, course level, and primary field of education: course dimension;
- organisation attributes: organisation dimension;
- offering-specific attributes: corresponding offering dimension only when populated, relevant, and distinct in meaning.

Do not include equivalent field-of-education, course-group, or similar attributes from multiple dimensions merely because their column names can be prefixed.

The feature manifest must record:

- final feature name;
- source table;
- source column;
- source-qualified staging name;
- data type;
- numeric or categorical role;
- prediction-time availability;
- inclusion or exclusion decision;
- exclusion reason.

## Final Phase 1 dataset

Create an explicit canonical projection containing:

- `student_deidentified_hash`;
- `enrolment_deidentified_hash` for traceability;
- `is_twelve_month_student_attrition` as the target source;
- only approved canonical predictive columns.

Validate:

- one row per student;
- unique DataFrame column names;
- unique final feature names;
- binary non-null target for supervised rows;
- class distribution;
- feature missingness;
- no target, course-attrition label, identifier, raw key, or hash in the predictive feature list.

## Phase 1 result and human-review checkpoint

Update `student_attrition_machine_learning.py` with the complete, executable Phase 1 implementation.

Return the implementation result first, followed by one concise Phase 1 review summary containing:

- which of the 12 source tables were successfully inspected;
- which dimensions were joined and which were excluded, with reasons;
- confirmation that every accepted join preserved the fact row count and one-row-per-student grain;
- the final canonical feature manifest and final modelling schema;
- unresolved data-quality problems;
- routine corrections made during implementation;
- material refinements requiring human approval.

Keep detailed table profiles, join counts, unmatched-key counts, missingness results, and validation evidence inside the Databricks notebook so they can be executed and reviewed there. Summarise only the conclusions and failures in the agent response.

The source-profiling, join, duplicate, feature-ownership, and schema checks in this prompt are Phase 1 acceptance criteria. They do not need to be converted into separate GitHub sub-issues or separate task-status reports.

Stop after completing Phase 1 and presenting the result summary. Do not create train, validation, or test splits and do not begin model training until the human reviewer approves Phase 1.
