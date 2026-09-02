from student_attrition_risk.briefing_provider import TemplateBriefingProvider
from student_attrition_risk.models import StudentPrediction, StudentRiskProfile


def test_template_does_not_make_longitudinal_or_causal_claims():
    profile = StudentRiskProfile(
        prediction=StudentPrediction(
            student_deidentified_hash="synthetic-student-001",
            attrition_risk_percentage=80,
            attrition_risk_flag=True,
            prediction_threshold=0.5,
        )
    )
    text = TemplateBriefingProvider().generate(profile).text.lower()
    assert "cross-sectional" in text
    assert "caus" in text
    assert "declined" not in text
