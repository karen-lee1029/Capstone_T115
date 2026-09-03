# Tasks: Student Attrition Machine Learning

Atomic, testable, dependency-ordered Sprint 2 tasks derived from the specification and plan.

**Legend:** `[ ]` Planned, `[x]` Completed. Each task maps to one or more independently numbered machine-learning specification stories.

## Milestone 1: Modelling-data preparation

Completed and approved at the Phase 1 human-review checkpoint on 2026-08-06. The reviewer confirmed
that `student_attrition_machine_learning.py` runs top to bottom against the regenerated Delta tables
with every validation assertion passing.

- [x] **T1.** Define source-table, output-table, target, identifier, threshold, and seed constants.  
  **Satisfies:** US-1, US-2, US-3, US-4.
- [x] **T2.** Read the synthetic fact table and required populated dimensions from `workspace.student_aggregate`.  
  **Satisfies:** US-1, US-5.
- [x] **T3.** Join required descriptive attributes and produce one candidate modelling row per `student_deidentified_hash`.  
  **Satisfies:** US-5.
- [x] **T4.** Validate required columns, data types, non-null identifiers, and binary target values.  
  **Satisfies:** US-5.
- [x] **T5.** Check row counts and confirm joins have not produced duplicate student identifiers.  
  **Satisfies:** US-5.
- [x] **T6.** Report target class distribution and feature missingness; remove unusable all-null features.  
  **Satisfies:** US-5.
- [x] **T7.** Define `is_twelve_month_student_attrition` as the label and separate identifiers from predictive features.  
  **Satisfies:** US-4.
- [x] **T8.** Explicitly exclude `is_twelve_month_course_attrition`, the target, and identifier hashes from the feature vector.  
  **Satisfies:** US-4.

## Milestone 2: Split and preprocessing

Completed and approved at the Phase 2 human-review checkpoint on 2026-08-06. Material refinement
**M-1** — split assigned by hashing the student identifier rather than `randomSplit`, because
serverless compute forbids the `cache()` that `randomSplit` needs to be reproducible — was approved
and is recorded as amendment A-4 in `plan.md`.

- [x] **T9.** Create deterministic 70/15/15 training, validation, and test splits using seed 42.  
  **Satisfies:** US-6.
- [x] **T10.** Record split row counts and class distributions and verify no row overlaps across splits.  
  **Satisfies:** US-6.
- [x] **T11.** Implement numeric casting and training-derived median imputation.  
  **Satisfies:** US-7.
- [x] **T12.** Derive categorical levels from training data and implement deterministic manual one-hot encoding with explicit unseen/NULL handling.  
  **Satisfies:** US-7.
- [x] **T13.** Assemble processed columns into the Spark ML feature vector and verify excluded columns are absent.  
  **Satisfies:** US-4, US-7.

## Milestone 3: Random Forest training and evaluation

Completed and approved at the Phase 2 human-review checkpoint on 2026-08-06. T19 to T21 must be read
against limitations L-1 to L-3 in `plan.md`: ROC-AUC near 0.5 and precision near the 5.51% base rate
are the expected result for this synthetic dataset, and are attributable to the data generating
process rather than to the model.

- [x] **T14.** Calculate a training weight column when class imbalance requires it.  
  **Satisfies:** US-1, US-8.
- [x] **T15.** Configure the Spark ML Random Forest with 100 trees, maximum depth 7, minimum instances per node 20, `sqrt` feature strategy, and seed 42 (amendment A-5; reduced for Databricks free-edition Serverless memory limits).  
  **Satisfies:** US-1.
- [x] **T16.** Implement the stateless preprocessing workflow and configure VectorAssembler as a Transformer for the Random Forest feature vector.  
  **Satisfies:** US-1, US-7.
- [x] **T17.** Start an MLflow run and log the approved configuration, feature list, target, split details, threshold, table names, and the training-derived preprocessing contract.  
  **Satisfies:** US-1.
- [x] **T18.** Fit RandomForestClassifier directly on the prepared training split and log the trained model artifact and preprocessing contract.  
  **Satisfies:** US-1.
- [x] **T19.** Evaluate validation predictions and log recall, accuracy, precision, F1, ROC-AUC, and confusion-matrix counts.  
  **Satisfies:** US-8.
- [x] **T20.** Confirm probabilities and predicted classes are non-trivial and investigate any constant-output failure.  
  **Satisfies:** US-8.
- [x] **T21.** Perform final evaluation on the untouched test split and log the same metrics.  
  **Satisfies:** US-6, US-8.

## Milestone 4: Inference and Delta persistence

Completed and approved at the Phase 3 human-review checkpoint on 2026-08-06. The reviewer confirmed
that `workspace.student_aggregate.student_attrition_risk_prediction` was written with one row per
`student_deidentified_hash`, that retrieval by the logical primary key returns the correct result,
and that no source table was modified. T23, T27, and T28 are implemented through a transient scoring
staging table so the model is applied to the full population once rather than twice; the guarantee
T27 requires — nothing persisted to the approved table until every check passes — is unchanged. See
sections 18 and 19 of `plan.md`.

- [x] **T22.** Build the applicable-student inference dataset using the same validated column definitions.  
  **Satisfies:** US-2, US-5.
- [x] **T23.** Apply the training-derived preprocessing contract and fitted Random Forest to every valid applicable student row.  
  **Satisfies:** US-2.
- [x] **T24.** Extract the positive-class probability and calculate `attrition_risk_percentage` from 0 to 100.  
  **Satisfies:** US-2.
- [x] **T25.** Apply the fixed 0.50 probability threshold to produce a Boolean `attrition_risk_flag`.  
  **Satisfies:** US-2.
- [x] **T26.** Create the prediction output with `student_deidentified_hash`, percentage, flag, threshold, MLflow run ID, and scored timestamp.  
  **Satisfies:** US-2, US-3.
- [x] **T27.** Validate non-null unique student identifiers, valid percentage range, Boolean flags, and one output row per applicable student.  
  **Satisfies:** US-3.
- [x] **T28.** Overwrite `workspace.student_aggregate.student_attrition_risk_prediction` with the validated latest snapshot.  
  **Satisfies:** US-3.
- [x] **T29.** Query the written Delta table and confirm the Databricks application can retrieve the correct prediction result by `student_deidentified_hash`.  
  **Satisfies:** US-3.

## Milestone 5: Sprint 2 review

Completed at the Phase 3 human-review checkpoint on 2026-08-06. The reviewer approved the
implementation against the controlling documents, accepted the recorded limitations L-1 to L-3, and
authorised closure of Sprint 2 machine-learning tasks.

- [x] **T30.** Review AI-generated code, reported technical corrections, and proposed refinements against the constitution, specification, plan, tasks, and acceptance criteria. Obtain human approval for every material refinement before accepting it.  
  **Satisfies:** All stories.
- [x] **T31.** Record known limitations, including synthetic-data assumptions and the absence of real-data validation.  
  **Satisfies:** US-8. Recorded as L-1 to L-3 in `plan.md`.
- [x] **T32.** Mark tasks and user stories complete only after successful execution, testing, and human review.  
  **Satisfies:** All stories.
