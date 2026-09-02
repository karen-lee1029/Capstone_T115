"""Streamlit single-student interface."""

import streamlit as st

from student_attrition_risk.main import build_service
from student_attrition_risk.student_service import StudentNotFoundError


def _snapshot_label(name: str) -> str:
    return name.replace("_", " ").title()


def _snapshot_value(value: object) -> str:
    if value is None:
        return "Unavailable"
    return str(value)


def _render_snapshot(attributes: dict[str, object]) -> None:
    columns = st.columns(2)
    for index, (name, value) in enumerate(attributes.items()):
        with columns[index % 2]:
            st.markdown(f"**{_snapshot_label(name)}**")
            st.write(_snapshot_value(value))

st.set_page_config(page_title="Student Attrition Risk Briefing", layout="centered")
st.title("Student Attrition Risk Briefing")
st.caption("Synthetic student record review")
st.info(
    "This proof of concept uses cross-sectional synthetic data. The prediction is a model-generated "
    "risk signal for decision support and is not a longitudinal assessment or final decision."
)
st.sidebar.write("Student Attrition Risk App")

service = build_service()
student_hash = st.text_input("Student hash", placeholder="synthetic-student-001")
retrieve = st.button("Retrieve", type="primary")

if retrieve:
    if not student_hash.strip():
        st.error("Enter a student hash.")
    else:
        try:
            st.session_state.profile = service.get_student_profile(student_hash.strip())
            st.session_state.briefing = None
        except StudentNotFoundError:
            st.error("No prediction was found for that student hash.")
        except Exception:
            st.error("The data source is currently unavailable.")

profile = st.session_state.get("profile")
if profile:
    prediction = profile.prediction
    st.metric("Risk percentage", f"{prediction.attrition_risk_percentage:.1f}%")
    st.write(f"**Risk flag:** {'At Risk' if prediction.attrition_risk_flag else 'Not At Risk'}")
    st.write(f"**Prediction threshold:** {prediction.prediction_threshold:.2f}")
    st.write(f"**MLflow run ID:** {prediction.mlflow_run_id or 'Unavailable'}")
    st.write(f"**Scored at:** {prediction.scored_at or 'Unavailable'}")
    st.subheader("Student Snapshot")
    if profile.snapshot:
        st.caption("Descriptive values from the verified cross-sectional record.")
        _render_snapshot(profile.snapshot.attributes)
    else:
        st.caption(
            "Snapshot attributes are unavailable because the optional fact table is not configured "
            "or has no approved columns for this record."
        )
    if st.button("Generate Draft Briefing"):
        with st.spinner("Generating briefing..."):
            st.session_state.briefing = service.generate_briefing(prediction.student_deidentified_hash)
    briefing = st.session_state.get("briefing")
    if briefing:
        st.subheader("Draft Briefing")
        st.caption(f"Source: {briefing.source.replace('_', ' ').title()}")
        st.write(briefing.text)
