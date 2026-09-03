"""At-Risk Student Display"""

import streamlit as st
import pandas as pd
from student_attrition_risk.main import build_service

page_limit = st.selectbox("Page limit:", [10, 20, 50])

service = build_service()
try:
    high_risk_students = service.get_high_risk_students(page_limit)
except Exception:
    st.error("No students found.")
