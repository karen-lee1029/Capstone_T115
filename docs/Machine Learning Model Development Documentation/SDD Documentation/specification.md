# Specification: Student Attrition Machine Learning

Sprint 2 requirements, user stories, acceptance criteria, and clarified behaviour.

This specification defines what the Sprint 2 machine-learning workflow must achieve and why. Technical implementation details are defined separately in `plan.md` after clarification.

## 1. Overview and intent

The workflow trains and evaluates a binary classification model using deidentified synthetic student data. It predicts twelve-month student attrition, generates an attrition-risk percentage and risk flag for each applicable student, records the model run through MLflow, and stores the validated results in a queryable Delta table linked by `student_deidentified_hash` so that the Databricks application can retrieve each student's correct prediction result.

## 2. Stakeholders

| Persona | Interest in the model |
|---|---|
| Academic advisor | Uses risk percentages and flags to identify students who may require support. |
| Machine-learning engineer | Builds, evaluates, and refines the student-attrition model. |
| Data analyst | Validates modelling data and retrieves prediction results from Delta tables. |
| Project team / reviewer | Reviews AI-generated code and confirms Sprint 2 acceptance criteria. |
| Industry partner / data owner | Requires appropriate use of deidentified synthetic data and a student-level outcome. |

## 3. Story numbering and Product Backlog relationship

The user stories in this specification are numbered independently from the main Product Backlog. They describe detailed requirements for developing the Sprint 2 machine-learning component and do not replace or renumber the project-level Product Backlog stories.

| Machine-learning specification story | Parent Product Backlog relationship |
|---|---|
| US-1 | Product Backlog US-05: Machine Learning Classification Model |
| US-2 | Product Backlog US-06: Student Attrition Risk Percentage Generation |
| US-3 | Product Backlog US-07: Student Attrition Risk Prediction Delta Table |
| US-4 to US-8 | Supporting technical requirements primarily under Product Backlog US-05, with relevant support for US-06 and US-07 |

These detailed machine-learning stories may be implemented as GitHub sub-issues beneath the corresponding parent Product Backlog stories.

## 4. User stories and acceptance criteria

Acceptance criteria are written in Given / When / Then form.

### US-1: Machine Learning Classification Model

**As an academic advisor, I want** a machine-learning classification model to assess student attrition risk, **so that** students who may require additional support can be identified.

- **Given** the required synthetic student data is available, **when** the classification model is trained and evaluated, **then** it produces student-level attrition-risk predictions.
- **Given** model training is completed, **when** the run is reviewed, **then** the model parameters, evaluation metrics, and trained model artifact are available through MLflow.
- **Given** the model target is configured, **then** the model predicts twelve-month student attrition rather than course attrition.

**MoSCoW Priority:** Must Have  
**Story Points:** 13  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-2: Student Attrition Risk Percentage Generation

**As an academic advisor, I want** an attrition-risk percentage generated for each applicable student, **so that** I can compare and prioritise students who may require support.

- **Given** a trained classification model and valid student data are available, **when** inference is executed, **then** a risk percentage from 0 to 100 is generated for every applicable student.
- **Given** a risk percentage has been generated, **when** the approved 0.50 probability threshold is applied, **then** the corresponding Boolean risk flag is produced.
- **Given** inference results are produced, **then** every risk percentage is valid and non-missing.

**MoSCoW Priority:** Must Have  
**Story Points:** 8  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-3: Student Attrition Risk Prediction Delta Table

**As a data analyst, I want** student attrition-risk results stored with the correct deidentified student identifiers, **so that** the Databricks application can retrieve each student's correct prediction result.

- **Given** student attrition-risk predictions have been generated, **when** results are persisted, **then** each `student_deidentified_hash` is linked to its risk percentage and risk flag in a queryable Delta table.
- **Given** the prediction table is written, **then** each applicable student appears once in the latest prediction snapshot.
- **Given** the output is validated, **then** risk flags are Boolean and the logical primary key `student_deidentified_hash` contains no duplicates.
- **Given** a stored prediction is retrieved, **then** the table also provides the approved threshold, MLflow run identifier, and scoring timestamp required for traceability.

**MoSCoW Priority:** Must Have  
**Story Points:** 5  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-4: Student Attrition Target and Leakage Prevention

**As a machine-learning engineer, I want** target and feature roles defined correctly, **so that** the model learns to predict student attrition without being given outcome information or arbitrary identifiers.

- **Given** the modelling dataset is prepared, **when** the target is selected, **then** `is_twelve_month_student_attrition` is the sole supervised label.
- **Given** the predictive feature set is created, **then** `is_twelve_month_student_attrition` and `is_twelve_month_course_attrition` are excluded from the feature vector.
- **Given** `student_deidentified_hash` and `enrolment_deidentified_hash` are retained for traceability, **then** neither identifier is included as a predictive feature.
- **Given** any additional feature is proposed, **then** it is included only when it is available at the census-date prediction snapshot and does not reveal the outcome.

**MoSCoW Priority:** Must Have  
**Story Points:** 5  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-5: Modelling-Data Quality

**As a machine-learning engineer, I want** the modelling dataset validated before training, **so that** model results are based on complete, correctly joined, student-level data.

- **Given** the modelling dataset is built, **when** validation runs, **then** required identifier, target, and feature columns exist with compatible data types.
- **Given** the target is checked, **then** it contains only valid binary values and no missing labels in supervised-modelling rows.
- **Given** modelling grain is checked, **then** each training record represents one deidentified student and duplicate student identifiers are reported or resolved.
- **Given** fact and dimension data are joined, **then** row-count and key checks confirm that joins do not unintentionally duplicate students.
- **Given** model training begins, **then** target class distribution and feature missingness are reported for review.

**MoSCoW Priority:** Must Have  
**Story Points:** 5  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-6: Training, Validation and Test Split

**As a machine-learning engineer, I want** separate and reproducible training, validation, and test datasets, **so that** development checks and final evaluation are reliable.

- **Given** the validated modelling dataset is available, **when** it is split, **then** approximately 70 percent is assigned to training, 15 percent to validation, and 15 percent to testing.
- **Given** the split is repeated with unchanged data and settings, **then** the same seed of 42 is used.
- **Given** the workflow is reviewed during development, **then** validation results are inspected before the untouched test dataset is used for final evaluation.
- **Given** the three datasets are checked, **then** no modelling row occurs in more than one split.

**MoSCoW Priority:** Must Have  
**Story Points:** 3  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-7: Feature Preprocessing

**As a machine-learning engineer, I want** numeric and categorical features prepared consistently, **so that** the classification model can train and score students without avoidable data errors.

- **Given** numeric features contain missing values, **when** preprocessing information is derived, **then** numeric missing-value handling is based only on training data.
- **Given** categorical features are used, **when** they are prepared for modelling, **then** categories are encoded into a model-compatible representation and unseen inference categories do not cause failure.
- **Given** preprocessing is applied to validation, test, or inference data, **then** the training-derived preprocessing contract is reused and is not recalculated using validation, test, or inference data.
- **Given** identifiers, labels, and leakage columns are present, **then** they are excluded from the assembled feature vector.

**MoSCoW Priority:** Must Have  
**Story Points:** 5  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

### US-8: Model Evaluation

**As a project reviewer, I want** the classification model evaluated with suitable metrics, **so that** its ability to identify students at risk is transparent before results are used.

- **Given** a trained model and validation data, **when** evaluation is performed, **then** recall is treated as the primary metric and accuracy, precision, F1 score, ROC-AUC, and a confusion matrix are also produced.
- **Given** development validation is complete, **when** final evaluation is performed, **then** the same required metrics are reported on the untouched test dataset.
- **Given** predictions are reviewed, **then** the model produces non-trivial probabilities rather than a constant score or a single predicted class for every student.
- **Given** evaluation results are recorded, **then** they can be traced to the corresponding MLflow run.

**MoSCoW Priority:** Must Have  
**Story Points:** 5  
**Planned Sprint:** Sprint 2  
**Status:** Accepted (2026-08-06)

## 5. Clarified Sprint 2 decisions

- **Applicable students:** every valid student row in the prepared modelling dataset is scored.
- **Prediction timing:** the model represents a census-date snapshot and uses only information treated as available by that point.
- **Implementation approach:** Spark ML Random Forest; the full generated dataset is not collected into one pandas DataFrame.
- **Primary metric:** recall; accuracy, precision, F1, ROC-AUC, and confusion matrix remain supporting metrics.
- **Risk threshold:** fixed probability threshold of 0.50.
- **Risk storage:** advisor-facing `attrition_risk_percentage` is stored from 0 to 100.
- **Prediction persistence:** each successful inference run overwrites the latest prediction snapshot.
- **Output table:** `workspace.student_aggregate.student_attrition_risk_prediction`.
- **Model scope:** one approved Spark ML Random Forest and one validated feature set are implemented. Alternative-model benchmarking, competing feature-subset experiments, automated feature selection, broad hyperparameter searches, and research-led model selection are excluded.
- **Permitted refinement:** unavailable, completely NULL, invalid, incompatible, post-outcome, or leakage-prone features may be corrected or removed as part of validation. Such refinements must be reported to the human reviewer.
- **Human approval:** any proposed refinement that changes model behaviour, approved features, parameters, split, threshold, data grain, output schema, or architecture requires human review and approval before it is accepted.
- **Approved feature amendment (2026-08-06):** `course_admission_load_category` and `commencing_continuing_period` were added to the approved feature set following Phase 1 human review, giving 21 predictive features. Field-of-education attributes from the study area and unit dimensions remain excluded so that the course dimension stays the single canonical owner of that concept. Recorded as amendments A-1 and A-2 in `plan.md`.

## 6. Constraints and non-functional requirements

- Sprint scope: Sprint 2; all stories were accepted following human review on 2026-08-06.
- Synthetic and deidentified student data only.
- Prediction subject: an individual student exiting education, not a course-level leaving rate.
- Primary prediction identifier: `student_deidentified_hash`.
- The prediction Delta table must support retrieval of the correct risk result for each applicable student by the Databricks application.
- Implementation produced by an AI agent must be human-reviewed before acceptance.

## 7. Out of scope for Sprint 2

- A separate course-attrition model.
- Alternative-model benchmarking, competing feature-set experiments, automated feature selection, broad hyperparameter searches, and research-led model selection.
- Automated intervention decisions or automatic contact with students.
- Generative-AI production of the final academic-advisor briefing.
- Formal MLflow promotion governance, approval roles, aliases, rollback procedures, or release management.
- Automated retraining, drift monitoring, and scheduled production deployment.
- Validation against real student-level records where access has not been supplied by the industry partner.
