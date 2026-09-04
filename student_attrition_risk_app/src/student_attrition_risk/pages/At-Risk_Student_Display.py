"""At-Risk Student Display"""

import streamlit as st
from student_attrition_risk.main import build_service

service = build_service()
page_limit = st.selectbox("Page Limit", [10, 20, 50, 100])
try:
    st.session_state.student_list = st.dataframe(service.get_high_risk_students(page_limit))
except Exception:
    st.error("Error loading data. Please try again.")