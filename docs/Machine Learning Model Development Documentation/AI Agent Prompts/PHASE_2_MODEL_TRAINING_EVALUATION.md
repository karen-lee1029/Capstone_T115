# Phase 2 Prompt: Model Training, MLflow, and Evaluation

Use this only after the human reviewer approves Phase 1 and the canonical feature manifest.

## Objective

Continue the same `student_attrition_machine_learning.py` notebook. Implement the approved split, preprocessing, Random Forest training, MLflow tracking, validation evaluation, and final test evaluation. Do not write or overwrite the prediction Delta table in this phase.

## Approved input

Use only the Phase 1 canonical modelling projection and approved feature manifest. Do not rediscover or automatically add new features from the raw schemas.

If the approved Phase 1 columns are unavailable or have changed, stop and report the conflict rather than silently substituting features.

## Split

Create deterministic datasets:

- training: approximately 70 percent;
- validation: approximately 15 percent;
- test: approximately 15 percent;
- seed: 42.

Record row counts, positive and negative counts, and class percentages. Verify no `student_deidentified_hash` occurs in more than one split.

## Preprocessing

Numeric features:

- cast to suitable Spark numeric types;
- replace missing and NaN values using medians derived exclusively from the training split.

Categorical features:

- derive category levels from the training split only;
- convert each categorical feature into deterministic manual one-hot columns;
- include one explicit bucket for NULL or previously unseen values.

Use `VectorAssembler` only as a Transformer to assemble one Spark ML features vector. Do not call `fit()` on the assembler. Do not fit Spark ML preprocessing estimators (`Imputer`, `StringIndexer`, `OneHotEncoder`) or a preprocessing `Pipeline`.

Derive the preprocessing contract only from training data and reuse it for validation and test data. Do not recalculate medians or category levels from validation or test data. Do not apply feature scaling.

Assert that identifiers, labels, leakage fields, raw keys, and hashes are absent from the assembled feature vector.

## Class imbalance

Calculate class distribution from the training split only. If the positive attrition class is materially under-represented, calculate a weight column, document the formula, use the Spark `weightCol`, and log the class weights. If weighting is not applied, explain why.

## Approved model

Use exactly one:

`pyspark.ml.classification.RandomForestClassifier`

Parameters:

- `numTrees=100`
- `maxDepth=7`
- `minInstancesPerNode=20`
- `featureSubsetStrategy="sqrt"`
- `seed=42`

Do not compare models, feature subsets, or alternative parameter configurations.

## MLflow

Start one MLflow run and log at least:

- target;
- approved feature manifest and final feature list;
- excluded features and reasons;
- source and output table names;
- split ratios and seed;
- threshold 0.50;
- Random Forest parameters;
- class counts and weights where used;
- training timestamp;
- validation and test metrics;
- confusion-matrix counts;
- trained Random Forest model artifact;
- training-derived preprocessing contract sufficient to reproduce the feature vector.

Capture the MLflow run ID for use in Phase 3. Formal registry promotion is outside scope.

## Evaluation

Evaluate validation data first. Report:

- recall as the primary metric;
- accuracy;
- precision;
- F1;
- ROC-AUC;
- true positives;
- true negatives;
- false positives;
- false negatives;
- predicted class counts.

Confirm that probabilities are not constant and predictions are not all one class.

After validation checks pass, evaluate the same fitted Random Forest and training-derived preprocessing contract on untouched test data and log the same metrics. Do not alter the model after viewing test results without a material-refinement review.

## Phase 2 result and human-review checkpoint

Update the same `student_attrition_machine_learning.py` notebook with the complete, executable Phase 2 implementation.

Return the implementation result first, followed by one concise Phase 2 review summary containing:

- confirmation that the approved Phase 1 feature manifest was used;
- training, validation, and test row counts and class distributions;
- the preprocessing and class-weighting decisions;
- the exact Random Forest configuration;
- validation and untouched test metrics;
- confirmation that probabilities and predictions are non-trivial;
- the MLflow experiment and run ID;
- routine corrections made during implementation;
- material refinements requiring human approval.

Keep detailed split checks, preprocessing outputs, metric calculations, confusion-matrix counts, and MLflow logging evidence inside the Databricks notebook. Summarise only the conclusions, failures, and approval decisions in the agent response.

The split, preprocessing, weighting, training, evaluation, and MLflow requirements in this prompt are Phase 2 acceptance criteria. They do not need to be converted into separate GitHub sub-issues or separate task-status reports.

Stop after completing Phase 2 and presenting the result summary. Do not run Phase 3 or write or overwrite the prediction Delta table until the human reviewer approves Phase 2.
