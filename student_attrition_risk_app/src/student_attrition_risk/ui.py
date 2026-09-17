"""Streamlit Student Advisor Briefing interface."""

from __future__ import annotations

import html
from decimal import Decimal
from typing import Any

import streamlit as st

from student_attrition_risk.main import build_service
from student_attrition_risk.student_service import (
    BriefingNotProducedError,
    BriefingStorageError,
    StudentNotAtRiskError,
    StudentNotFoundError,
)

from student_attrition_risk.models import (
    SUPPRESSED,
    UNAVAILABLE,
)

# ---------------------------------------------------------------------------
# Page configuration and application service
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Student Advisor Briefing",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

top_left, top_right = st.columns([4, 1])

with top_right:
    st.link_button(
        "View Dashboard",
        "https://dbc-d9f16845-692d.cloud.databricks.com/dashboardsv3/01f1b232102f1045b5d3828ffc7abc0a/published?o=7474649460131169",
        type="primary",
        use_container_width=True,
    )

@st.cache_resource
def get_service():
    """Create one service instance per Streamlit process.

    This also preserves InMemoryBriefingStore contents across Streamlit reruns
    during local development.
    """
    return build_service()


service = get_service()


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .stApp {
            background: #f4f6f8;
            color: #172033;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1480px;
            padding-top: 0;
            padding-bottom: 3rem;
        }

        .top-bar {
            background: #00558c;
            color: white;
            padding: 0.85rem 1.4rem;
            margin: 0 -1rem 1.8rem -1rem;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }

        .page-title {
            color: #152033;
            font-size: 2.25rem;
            line-height: 1.15;
            font-weight: 750;
            margin: 0;
        }

        .page-subtitle {
            color: #667085;
            font-size: 1rem;
            margin-top: 0.4rem;
            margin-bottom: 1.5rem;
        }

        .summary-card {
            background: white;
            border-left: 5px solid #d92d20;
            border-radius: 12px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 4px rgba(16, 24, 40, 0.08);
        }

        .summary-label {
            color: #667085;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .student-reference {
            color: #172033;
            font-size: 1.15rem;
            font-weight: 700;
            word-break: break-all;
        }

        .student-meta {
            color: #667085;
            font-size: 0.9rem;
            margin-top: 0.55rem;
        }

        .risk-badge {
            display: inline-block;
            background: #fee4e2;
            color: #b42318;
            padding: 0.3rem 0.65rem;
            margin-left: 0.6rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .not-risk-badge {
            display: inline-block;
            background: #dcfae6;
            color: #067647;
            padding: 0.3rem 0.65rem;
            margin-left: 0.6rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .risk-panel {
            text-align: center;
            padding-top: 0.1rem;
        }

        .risk-label {
            color: #667085;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .risk-circle {
            width: 92px;
            height: 92px;
            border: 8px solid #d92d20;
            border-radius: 50%;
            margin: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #d92d20;
            font-size: 1.25rem;
            font-weight: 800;
            background: white;
        }

        .section-card {
            background: white;
            border: 1px solid #e4e7ec;
            border-radius: 12px;
            padding: 1.35rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(16, 24, 40, 0.05);
        }

        .section-title {
            color: #172033;
            font-size: 1.15rem;
            font-weight: 750;
            margin-bottom: 1rem;
        }

        .snapshot-card {
            background: #f8fafc;
            border: 1px solid #e4e7ec;
            border-left: 4px solid #2e90fa;
            border-radius: 9px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
        }

        .snapshot-label {
            color: #344054;
            font-size: 0.86rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .snapshot-value {
            color: #475467;
            font-size: 0.92rem;
            line-height: 1.45;
            word-break: break-word;
        }

        .ai-notice {
            background: #eff8ff;
            border: 1px solid #b2ddff;
            border-radius: 8px;
            color: #175cd3;
            padding: 0.75rem 0.9rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .briefing-body {
            color: #344054;
            line-height: 1.7;
        }

        .briefing-meta {
            color: #667085;
            font-size: 0.8rem;
            margin-top: 1rem;
            border-top: 1px solid #e4e7ec;
            padding-top: 0.75rem;
        }

        .empty-state {
            color: #667085;
            background: #f8fafc;
            border: 1px dashed #d0d5dd;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }

        .privacy-note {
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.5;
        }

        div.stButton > button {
            border-radius: 8px;
            min-height: 2.8rem;
            font-weight: 650;
        }

        div.stButton > button[kind="primary"] {
            background: #00558c;
            border-color: #00558c;
        }

        @media (max-width: 900px) {
            .page-title {
                font-size: 1.75rem;
            }

            .risk-circle {
                width: 76px;
                height: 76px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

SNAPSHOT_LABELS = {
    "course_group": "Course Level",
    "broad_primary_field_of_education": (
        "Field of Education"
    ),
    "international_domestic_student": (
        "Student Category"
    ),
    "socioeconomic_status": (
        "Socioeconomic Status"
    ),
    "regional_remote_status": (
        "Regional or Remote Status"
    ),
}

def _snapshot_label(name: str) -> str:
    return SNAPSHOT_LABELS.get(
        name,
        name.replace("_", " ").title(),
    )

LABELS = {
    "age_band": "Age band",
    "attendance_mode": "Attendance mode",
    "course_admission_load_category": "Study load",
    "eftsl": "EFTSL",
    "enrolment_year": "Enrolment year",
    "commencing_continuing": "Student stage",
    "commencing_continuing_period": "Commencing/continuing period",
    "international_domestic_student": "International/domestic",
    "cumulative_credit_points_enrolled": "Credit points enrolled",
    "cumulative_credit_points_passed": "Credit points passed",
    "cumulative_credit_points_failed": "Credit points failed",
    "cumulative_credit_points_withdrawn": "Credit points withdrawn",
}

def display_label(name: str) -> str:
    return LABELS.get(name, name.replace("_", " ").title())


def _snapshot_value(value: object) -> str:
    if value == SUPPRESSED:
        return "Suppressed for privacy"

    if value in (None, UNAVAILABLE):
        return "Unavailable"

    return str(value)


def safe(value: Any) -> str:
    return html.escape(_snapshot_value(value))


def clear_selected_student() -> None:
    for key in (
        "profile",
        "briefing",
        "selected_hash",
        "reviewed",
        "ui_message",
    ):
        st.session_state.pop(key, None)


def load_student(student_hash: str) -> None:
    profile = service.get_student_profile(student_hash)
    st.session_state.profile = profile
    st.session_state.selected_hash = student_hash
    st.session_state.briefing = None
    st.session_state.reviewed = False


def request_briefing(*, regenerate: bool = False) -> None:
    profile = st.session_state.get("profile")

    if profile is None:
        return

    briefing = service.request_briefing(
        profile.prediction.student_deidentified_hash,
        regenerate=regenerate,
    )
    st.session_state.briefing = briefing
    st.session_state.reviewed = False


def retrieve_stored_briefing() -> None:
    profile = st.session_state.get("profile")

    if profile is None:
        return

    briefing = service.get_stored_briefing(
        profile.prediction.student_deidentified_hash
    )

    if briefing is None:
        st.session_state.ui_message = (
            "No previously validated briefing is available."
        )
        return

    st.session_state.briefing = briefing
    st.session_state.reviewed = False


def render_snapshot(attributes: dict[str, Any]) -> None:
    available = [
        (name, value)
        for name, value in attributes.items()
        if value is not None and value != "__unavailable__"
    ]

    if not available:
        st.markdown(
            '<div class="empty-state">'
            "No approved snapshot information is available."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    for name, value in available:
        st.markdown(
            f"""
            <div class="snapshot-card">
                <div class="snapshot-label">
                    {html.escape(display_label(name))}
                </div>
                <div class="snapshot-value">{safe(value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Header and search
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="top-bar">Student Briefing</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="page-title">Student Advisor Briefing</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-subtitle">
        Review model-generated risk information and prepare a supportive,
        human-led response.
    </div>
    """,
    unsafe_allow_html=True,
)

query_hash = st.query_params.get("student_hash", "")
default_hash = (
    query_hash
    or st.session_state.get("selected_hash", "")
)

with st.container(border=True):
    search_column, button_column = st.columns([5, 1])

    with search_column:
        student_hash = st.text_input(
            "Deidentified student reference",
            value=default_hash,
            placeholder="Enter a deidentified student hash",
            label_visibility="collapsed",
        )

    with button_column:
        retrieve_student = st.button(
            "Retrieve",
            type="primary",
            use_container_width=True,
        )

if retrieve_student:
    if not student_hash.strip():
        st.error("Enter a deidentified student reference.")
    else:
        clear_selected_student()

        try:
            load_student(student_hash.strip())
            st.rerun()
        except StudentNotFoundError:
            st.error("No prediction was found for that student reference.")
        except Exception:
            st.error(
                "Student information is currently unavailable. "
                "Please try again later."
            )


# ---------------------------------------------------------------------------
# Student profile
# ---------------------------------------------------------------------------

profile = st.session_state.get("profile")

if profile is None:
    st.markdown(
        """
        <div class="empty-state">
            Retrieve a deidentified student record to view the risk snapshot
            and advisor briefing.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


prediction = profile.prediction
risk_label = "At Risk" if prediction.attrition_risk_flag else "Not At Risk"
badge_class = (
    "risk-badge"
    if prediction.attrition_risk_flag
    else "not-risk-badge"
)
risk_score = prediction.attrition_risk_percentage
threshold_percentage = prediction.prediction_threshold * 100

summary_left, summary_right = st.columns([5, 1.25])

with summary_left:
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">Student summary</div>
            <div class="student-reference">
                Deidentified student
                <span class="{badge_class}">
                    {html.escape(risk_label)}
                </span>
            </div>
            <div class="student-meta">
                Reference:
                {html.escape(prediction.student_deidentified_hash)}
            </div>
            <div class="student-meta">
                Decision threshold:
                {threshold_percentage:.1f}%
                &nbsp;·&nbsp;
                Scored:
                {safe(prediction.scored_at)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with summary_right:
    st.markdown(
        f"""
        <div class="section-card risk-panel">
            <div class="risk-label">Relative risk score</div>
            <div class="risk-circle">{risk_score:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Snapshot and briefing columns
# ---------------------------------------------------------------------------

left_column, right_column = st.columns([0.9, 1.35], gap="large")

with left_column:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Available Student Information</div>
            <div class="privacy-note">
                Approved cross-sectional student information.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if profile.snapshot:
        render_snapshot(profile.snapshot.attributes)
    else:
        st.markdown(
            """
            <div class="empty-state">
                No approved snapshot information is available.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Briefing Actions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if prediction.attrition_risk_flag:
        if st.button(
            "Generate Advisor Briefing",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Generating advisor briefing..."):
                try:
                    request_briefing(regenerate=False)
                    st.rerun()
                except BriefingNotProducedError as exc:
                    st.error(
                        "A briefing could not be produced "
                        f"({exc.category})."
                    )
                except BriefingStorageError:
                    st.error(
                        "The briefing was generated but could not be stored."
                    )
                except Exception:
                    st.error(
                        "The briefing workflow is currently unavailable."
                    )

        retrieve_column, regenerate_column = st.columns(2)

        with retrieve_column:
            if st.button(
                "Retrieve Saved",
                use_container_width=True,
            ):
                try:
                    retrieve_stored_briefing()
                    st.rerun()
                except Exception:
                    st.error(
                        "The saved briefing is currently unavailable."
                    )

        with regenerate_column:
            if st.button(
                "Regenerate",
                use_container_width=True,
            ):
                with st.spinner("Regenerating advisor briefing..."):
                    try:
                        request_briefing(regenerate=True)
                        st.rerun()
                    except BriefingNotProducedError as exc:
                        st.error(
                            "A new briefing could not be produced "
                            f"({exc.category})."
                        )
                    except BriefingStorageError:
                        st.error(
                            "The briefing was generated but could not be stored."
                        )
                    except Exception:
                        st.error(
                            "The briefing workflow is currently unavailable."
                        )
    else:
        st.info(
            "This student is not currently classified as at risk. "
            "Briefing generation is unavailable."
        )

    message = st.session_state.pop("ui_message", None)
    if message:
        st.info(message)


with right_column:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">AI-Assisted Advisor Briefing</div>
            <div class="ai-notice">
                AI-generated—review before taking action.
            </div>
        """,
        unsafe_allow_html=True,
    )

    briefing = st.session_state.get("briefing")

    if briefing:
        st.markdown(
            '<div class="briefing-body">',
            unsafe_allow_html=True,
        )
        st.markdown(briefing.text)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="briefing-meta">
                Source: {html.escape(briefing.source.title())}
                &nbsp;·&nbsp;
                Validation: {html.escape(briefing.validator_id)}
                &nbsp;·&nbsp;
                Attempt: {briefing.attempt_count}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.checkbox(
            "I have reviewed this AI-generated briefing",
            key="reviewed",
            help=(
                "This local review state is not yet persisted by the backend."
            ),
        )

        st.download_button(
            "Download Briefing",
            data=briefing.model_dump_json(indent=2),
            file_name=(
                f"advisor-briefing-"
                f"{briefing.student_deidentified_hash[:12]}.json"
            ),
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                Generate a briefing to display concise risk context,
                advisor actions and suggested next steps.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)