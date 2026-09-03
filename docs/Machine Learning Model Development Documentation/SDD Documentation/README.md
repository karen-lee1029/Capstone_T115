# Student Attrition Machine Learning: Spec-Driven Documentation

This folder documents the Sprint 2 student-attrition machine-learning workflow using the Spec-Driven Development methodology. The specification is the source of truth from which the technical plan, implementation tasks, code, tests, and supporting documentation are derived.

## Document set

| SDD phase | File | Purpose |
|---|---|---|
| 0 - Constitution | `constitution.md` | Persistent project principles, technology stack, ethical rules, and guardrails that constrain every design and implementation decision. |
| 1 - Specify | `specification.md` | Sprint 2 machine-learning user stories, acceptance criteria, priorities, story points, target behaviour, constraints, and out-of-scope work. Defines the what and why. |
| 2 - Clarify | Integrated into `specification.md` and `plan.md` | Records the confirmed decisions made before planning, including the student-level target, Spark ML implementation, recall as the primary metric, the 0.50 threshold, and the exclusion of model-comparison experiments. |
| 3 - Plan | `plan.md` | Technical blueprint for preparing the student-level dataset, preprocessing features, training and evaluating the Random Forest, logging the run in MLflow, and writing predictions to Delta Lake. |
| 4 - Tasks | `tasks.md` | Atomic, testable, dependency-ordered implementation tasks derived from the approved specification and plan. |

The PDF files supplied with this package are human-readable exports of the same approved Markdown documentation. The Markdown files are the controlling files supplied to the AI coding agent.

## Current status

- **Sprint:** Sprint 2.
- **Documentation status:** Finalised following human review and approved for implementation.
- **Implementation status:** Complete. Approved by human review on 2026-08-06 after successful
  execution in Databricks. All tasks T1 to T32 are marked complete in `tasks.md`.
- **Output table:** `workspace.student_aggregate.student_attrition_risk_prediction` — one row per
  `student_deidentified_hash`, written by `student_attrition_machine_learning.py`.
- **Known limitations:** L-1 to L-3 in `plan.md` govern how stored risk percentages should be read.

## Confirmed project scope

- The model predicts twelve-month student attrition: whether an individual student exits university education, not whether the student leaves a particular course.
- The supervised target is `is_twelve_month_student_attrition`; `is_twelve_month_course_attrition` is excluded from predictive features to prevent target leakage.
- The implementation uses a Spark ML Random Forest, a reproducible 70/15/15 train-validation-test split, recall as the primary evaluation metric, and a fixed 0.50 risk threshold.
- The workflow must prepare the modelling data, train and evaluate the model, generate an attrition-risk percentage and Boolean risk flag for every applicable student, and persist the validated results in a created queryable Delta table.
- The prediction Delta table is linked by `student_deidentified_hash` and contains the information required for the Databricks application to retrieve each student's attrition-risk result, including the percentage, Boolean flag, prediction threshold, MLflow run identifier, and scoring timestamp.
- MLflow records model parameters, metrics, and the trained model artifact. Formal model governance, model-comparison experiments, and competing feature-set experiments are outside the Sprint 2 scope.

## User-story relationship

The user stories in `specification.md` are numbered independently from the main Product Backlog because they are detailed requirements for the Sprint 2 machine-learning component.

- Machine-learning specification **US-1** is implemented under Product Backlog **US-05: Machine Learning Classification Model**.
- Machine-learning specification **US-2** is implemented under Product Backlog **US-06: Student Attrition Risk Percentage Generation**.
- Machine-learning specification **US-3** is implemented under Product Backlog **US-07: Student Attrition Risk Prediction Delta Table**.
- Machine-learning specification **US-4 to US-8** are supporting technical requirements primarily under Product Backlog **US-05**, with relevant support for US-06 and US-07.

These detailed stories may be represented as GitHub sub-issues beneath the corresponding Product Backlog stories rather than added as new top-level Product Backlog items.

## Approved implementation workflow

1. Provide `README.md`, `constitution.md`, `specification.md`, `plan.md`, and `tasks.md` to the AI coding agent.
2. The agent reads the controlling SDD files in that order and implements `tasks.md` in dependency order without changing approved behaviour.
3. The agent inspects the synthetic-data generator, existing ML prototype, Delta schemas, table relationships, and available columns as technical implementation sources after reviewing the controlling SDD documents.
4. The agent reports conflicts, unavailable features, leakage risks, technical corrections, known limitations, and proposed refinements.
5. Material refinements that change model behaviour, features, parameters, data grain, outputs, or architecture require human review and approval before they are accepted.
6. A team member executes and tests the implementation in Databricks, reviews it against the acceptance criteria, and authorises completed task and user-story statuses.

## Source references

- **Synthetic data generator:** DBLDatagen Synthetic Data Generation V2.
- **Input data:** deidentified synthetic Delta fact and dimension tables in `workspace.student_aggregate`.
- **Primary target:** `is_twelve_month_student_attrition`.
- **Output table:** `workspace.student_aggregate.student_attrition_risk_prediction`.
- **Enterprise design context:** T115 Student Risk & Intervention Briefing physical solution design.
- **Parent Product Backlog stories:** US-05, US-06, and US-07 from T115 Product Backlog User Stories.
