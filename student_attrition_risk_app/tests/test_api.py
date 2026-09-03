from fastapi.testclient import TestClient

from student_attrition_risk.api import create_api
from student_attrition_risk.briefing_provider import TemplateBriefingProvider
from student_attrition_risk.student_repository import MockStudentRepository
from student_attrition_risk.student_service import StudentService

client = TestClient(create_api(StudentService(MockStudentRepository(), TemplateBriefingProvider())))


def test_api_status_codes_and_responses():
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/students/synthetic-student-001").status_code == 200
    assert client.get("/api/students/missing").status_code == 404
    assert client.get("/api/students/high-risk?limit=0").status_code == 422
    assert client.post("/api/students/synthetic-student-001/briefing").json()["source"] == "template"
