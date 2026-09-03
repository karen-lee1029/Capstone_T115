# Constitution: Student Attrition Machine Learning

Persistent principles that constrain the Sprint 2 machine-learning implementation.

## 1. Project purpose

Develop a machine-learning classification workflow that uses deidentified synthetic student data to estimate whether an individual student will exit university education within the defined twelve-month attrition window. The output supports academic advisors in identifying students who may require additional support.

## 2. Technology stack

- **Platform:** Databricks using serverless-compatible compute.
- **Processing and modelling:** Python, PySpark, and Spark ML.
- **Storage:** Delta Lake tables in the existing Unity Catalog environment.
- **Experiment tracking:** MLflow for model parameters, metrics, and the trained model artifact.
- **Data source:** deidentified synthetic student fact and dimension tables.

## 3. Guiding principles

1. **Specification as source of truth.** Required behaviour is defined in the specification before implementation; the plan, tasks, code, and tests remain consistent with it.
2. **Student-level prediction.** The model predicts whether a student exits education, not whether a student leaves one course or whether a course has a high leaving rate.
3. **Single target definition.** The supervised target is `is_twelve_month_student_attrition`.
4. **No target leakage.** The target itself, `is_twelve_month_course_attrition`, and any information that reveals or occurs after the target outcome are excluded from predictive features.
5. **Identifiers are not predictors.** Deidentified student and enrolment hashes are retained for traceability but excluded from the feature vector.
6. **Prediction-time validity.** Every feature must be available at the intended census-date prediction snapshot.
7. **Reproducibility.** Data splitting, preprocessing, training, and evaluation use recorded settings and fixed random seeds where applicable.
8. **Evaluation separation.** Training data fits the model, validation data checks development performance, and test data is reserved for final evaluation.
9. **Privacy by design.** Only deidentified synthetic data is processed; the workflow must not expose or reconstruct real student records.
10. **Human oversight.** AI-generated implementation is reviewed and tested by a team member before acceptance.

## 4. Data ethics and decision support

- The model output supports academic-advisor judgement and does not automatically determine an intervention.
- Predictions remain linked only to deidentified student identifiers.
- A risk percentage is a model estimate, not a confirmed future outcome.

## 5. Change management

- Clarify and update the specification before changing required behaviour.
- Derive the technical plan and atomic tasks from the approved specification.
- Do not mark Sprint 2 work complete until acceptance criteria are tested and human-reviewed.
