# Phase 3 Prompt: Inference and Delta Persistence

Use this only after the human reviewer approves Phase 2 and authorises persistence.

## Objective

Complete the same `student_attrition_machine_learning.py` notebook by implementing inference for every applicable student, calculating the approved attrition-risk result, validating it, and writing the latest prediction snapshot to Delta.

## Inference dataset

Build the applicable-student inference dataset using the same approved fact-centred feature assembly, canonical projection, feature manifest, training-derived Phase 2 preprocessing contract, and fitted Random Forest from Phases 1 and 2.

Do not refit preprocessing. Do not add or substitute features.

## Probability, percentage, and flag

Extract the positive-class probability as an intermediate:

`attrition_risk_probability`

Calculate:

`attrition_risk_percentage = attrition_risk_probability * 100`

Apply the threshold without rounding first:

- `attrition_risk_flag = true` when `attrition_risk_probability >= 0.50`;
- `attrition_risk_flag = false` when `attrition_risk_probability < 0.50`.

Therefore 0.50 is true and 0.49 is false.

The intermediate probability may be displayed and validated, but the approved persisted schema is:

- `student_deidentified_hash`;
- `attrition_risk_percentage`;
- `attrition_risk_flag`;
- `prediction_threshold` with value 0.50;
- `mlflow_run_id` from Phase 2;
- `scored_at` timestamp.

Do not add another persisted column without human approval and an SDD update.

## Output validation

Before writing, validate:

- one output row per applicable student;
- no null student identifiers;
- no duplicate student identifiers;
- no null intermediate probabilities;
- intermediate probabilities between 0 and 1;
- percentages between 0 and 100;
- Boolean flags only;
- exact threshold value 0.50;
- populated MLflow run ID;
- output count matches the approved inference population.

Fail before persistence if any check does not pass.

## Delta persistence

Write the validated output in overwrite mode to:

`workspace.student_aggregate.student_attrition_risk_prediction`

Do not modify any source Delta table.

After writing:

- confirm the table exists and is queryable;
- confirm row count and unique student count;
- display a small sample;
- query one or more records by `student_deidentified_hash`;
- confirm the retrieved percentage, flag, threshold, MLflow run ID, and timestamp are correct;
- report the table schema.

## Phase 3 result and final human-review checkpoint

Complete `student_attrition_machine_learning.py` with the executable Phase 3 implementation.

Return the completed implementation result first, followed by one concise final review summary containing:

- inference population and output row counts;
- confirmation that one validated result exists per applicable student;
- probability, percentage, Boolean flag, null, uniqueness, and range validation conclusions;
- the final prediction Delta table name and schema;
- the MLflow run linked to the stored predictions;
- confirmation that predictions can be retrieved by `student_deidentified_hash`;
- routine corrections made during implementation;
- material refinements or known limitations requiring human review.

Keep detailed validation outputs, true and false flag counts, sample rows, and retrieval queries inside the Databricks notebook. Summarise only the conclusions, failures, and final approval matters in the agent response.

The inference, threshold, output-validation, persistence, and retrieval requirements in this prompt are Phase 3 acceptance criteria. They do not need to be converted into separate GitHub sub-issues or separate task-status reports.

Stop after presenting the completed notebook and final result summary. Do not independently mark the Sprint or Product Backlog stories as accepted; final acceptance remains with the human reviewer.
