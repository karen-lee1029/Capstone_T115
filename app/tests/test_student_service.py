from student_attrition_risk.briefing_provider import TemplateBriefingProvider
from student_attrition_risk.models import StudentBriefing, StudentRiskProfile
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import StudentNotFoundError, StudentService


def service(provider=None):
    return StudentService(MockStudentRepository(), provider or TemplateBriefingProvider())


def test_retrieves_prediction_and_snapshot():
    profile = service().get_student_profile("synthetic-student-001")
    assert profile.prediction.attrition_risk_percentage == 78.5
    assert profile.snapshot is not None


def test_unknown_student_raises_not_found():
    try:
        service().get_student_profile("missing")
    except StudentNotFoundError:
        pass
    else:
        raise AssertionError("missing students must be explicit")


def test_high_risk_limit_is_validated():
    for invalid in (0, 101):
        try:
            service().get_high_risk_students(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid limits must be rejected")


def test_no_fact_table_still_returns_prediction():
    repository = MockStudentRepository()
    repository.get_snapshot = lambda _: None
    profile = StudentService(repository, TemplateBriefingProvider()).get_student_profile(
        "synthetic-student-001"
    )
    assert profile.snapshot is None


def test_model_failure_uses_template_fallback():
    class FailingProvider:
        def generate(self, profile: StudentRiskProfile) -> StudentBriefing:
            raise RuntimeError("model unavailable")

    briefing = service(FailingProvider()).generate_briefing("synthetic-student-001")
    assert briefing.source == "template"
    assert "cross-sectional" in briefing.text
