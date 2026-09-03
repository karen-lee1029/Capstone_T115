from student_attrition_risk.briefing_instructions import InterimInstructions
from student_attrition_risk.briefing_provider import StubGenerationProvider
from student_attrition_risk.briefing_store import InMemoryBriefingStore
from student_attrition_risk.briefing_validation import InterimValidator
from student_attrition_risk.models import UNAVAILABLE
from student_attrition_risk.retry_workflow import RetryNotConfigured
from student_attrition_risk.student_repository import MODEL_FEATURE_COLUMNS, MockStudentRepository
from student_attrition_risk.student_service import StudentNotFoundError, StudentService


def service(repository=None):
    return StudentService(
        repository=repository or MockStudentRepository(),
        generation_provider=StubGenerationProvider(),
        instructions=InterimInstructions(),
        validator=InterimValidator(),
        retry_workflow=RetryNotConfigured(),
        store=InMemoryBriefingStore(),
    )


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
    profile = service(repository).get_student_profile("synthetic-student-001")
    assert profile.snapshot is None


def test_get_model_features_returns_exactly_the_21_names_never_reduced():
    features = MockStudentRepository().get_model_features("synthetic-student-001")
    assert features is not None
    assert set(features.values) == set(MODEL_FEATURE_COLUMNS)
    assert len(features.values) == 21


def test_get_model_features_preserves_the_unavailable_marker():
    features = MockStudentRepository().get_model_features("synthetic-student-001")
    assert features is not None
    assert features.values["detailed_primary_field_of_education"] == UNAVAILABLE


def test_get_model_features_is_none_for_an_unknown_hash():
    assert MockStudentRepository().get_model_features("missing") is None
