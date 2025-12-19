import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import math

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="ARETE Item Analysis Automated System",
    page_icon="📂",
    layout="wide"
)

# ===============================
# GLOBAL STYLE (FONT + COLORS)
# ===============================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Times New Roman", serif;
    background-color: #F5F7FA;
    color: #111111;
}

.big-title {
    font-size: 36px;
    font-weight: bold;
    color: #0A2A66;
}

.sub-title {
    font-size: 18px;
    color: #2E2E2E;
}

.section {
    background-color: #FFFFFF;
    padding: 22px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 6px solid #0A2A66;
}

/* Blue outline for tables */
[data-testid="stDataFrame"] {
    border-left: 6px solid #0A2A66;
    padding-left: 5px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# UTILITIES
# ===============================
def difficulty_label(p):
    if p <= 0.20: return "Very Difficult"
    if p <= 0.40: return "Difficult"
    if p <= 0.60: return "Moderately Difficult"
    if p <= 0.80: return "Easy"
    return "Very Easy"

def discrimination_label(d):
    if d <= -0.60: return "Questionable"
    if d <= -0.20: return "Not Discriminating"
    if d <= 0.20: return "Moderately Discriminating"
    if d <= 0.60: return "Discriminating"
    return "Very Discriminating"

def final_decision(p, d):
    if d >= 0.20 and 0.26 <= p <= 0.75:
        return "Retained"
    if d < 0.20 and 0.26 <= p <= 0.75:
        return "Revised"
    return "Rejected"

def kr20(df):
    k = df.shape[1]
    if k < 2:
        return np.nan
    p = df.mean()
    q = 1 - p
    pq = (p * q).sum()
    total_var = df.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return np.nan
    return (k / (k - 1)) * (1 - (pq / total_var))

def kr_label(alpha):
    if alpha >= 0.90: return "Excellent"
    if alpha >= 0.80: return "Good"
    if alpha >= 0.70: return "Acceptable"
    if alpha >= 0.60: return "Questionable"
    if alpha >= 0.50: return "Poor"
    return "Unacceptable"

# ===============================
# PUBLIC LANDING PAGE
# ===============================
def landing_page():
    st.markdown('<div class="big-title">ARETE Item Analysis Automated System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Departmental Assessment Item Analytics System (DAIAS)</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="section">
        <h4>System Overview</h4>
        <p>
        The <strong>ARETE Item Analysis Automated System</strong> is an institutional-grade,
        web-based psychometric evaluation platform developed to support evidence-based
        decision-making in academic assessment.
        </p>
        <p>
        It automates the computation, interpretation, and reporting of item difficulty,
        item discrimination, and test reliability using established principles of
        <em>Classical Test Theory</em>, ensuring transparency, validity, and quality assurance
        in examination development.
        </p>
    </div>

    <div class="section">
        <h4>Supported Examination Types</h4>
        <ul>
            <li>Departmental and Institutional Examinations</li>
            <li>Summative and Periodical Assessments</li>
            <li>Mock Board and Pre-Board Examinations</li>
            <li>In-House Standardized Tests</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Proceed to Faculty Login"):
        st.session_state.show_login = True
        st.rerun()

# ===============================
# LOGIN PAGE
# ===============================
def login_page():
    st.markdown('<div class="big-title">Faculty Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.logged_in = True
        st.rerun()

# ===============================
# MAIN APPLICATION
# ===============================
def main_app():
    st.markdown('<div class="big-title">ARETE Departmental Automated Item Analysis System (DAIAS)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Item Analysis Dashboard • Difficulty • Discrimination • Reliability</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### EXAMINATION MANAGEMENT MODULE")

    col1, col2 = st.columns(2)

    with col1:
        exam_name = st.text_input(
            "EXAMINATION TITLE",
        )

        year_level = st.selectbox(
            "YEAR LEVEL",
            [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year"
            ])
        
    with col2:
        academic_year = st.text_input(
            "ACADEMIC YEAR",
        )

        exam_type = st.selectbox(
            "EXAMINATION TYPE",
            [
                "Departmental Examination",
                "Mock Board Examination"
            ]
        )

    st.markdown("### ASSESSMENT DATA SUBMISSION")
    
    responses_file = st.file_uploader("UPLOAD STUDENTS RESPONSES (CSV)", type="csv")
    key_file = st.file_uploader("UPLOAD ANSWER KEY (CSV)", type="csv")

    if responses_file and key_file:
        responses = pd.read_csv(responses_file)
        key = pd.read_csv(key_file)

        item_cols = [c for c in responses.columns if c.lower().startswith("item")]
        responses = responses[item_cols]
        key = key[item_cols]

        scored = (responses == key.iloc[0]).astype(int)
        scores = scored.sum(axis=1)
        scored["Total"] = scores
        scored = scored.sort_values("Total", ascending=False)

        n = len(scored)
        g = max(1, math.floor(0.27 * n))
        top = scored.head(g)
        bottom = scored.tail(g)

        results = []
        for item in item_cols:
            U = top[item].sum()
            L = bottom[item].sum()
            p = (U + L) / (2 * g)
            d = (U - L) / g
            results.append({
                "Item": item,
                "Difficulty Index (P)": round(p, 3),
                "Difficulty Interpretation": difficulty_label(p),
                "Discrimination Index (D)": round(d, 3),
                "Discrimination Interpretation": discrimination_label(d),
                "Final Decision": final_decision(p, d)
            })

        df = pd.DataFrame(results)
        alpha = kr20(scored[item_cols])

        st.markdown("### ITEM ANALYSIS RESULTS")
        st.markdown(
            f"""
            <div style="
                background-color: #FFFFFF;
                border: 1.5px solid #0A2A66;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 18px;
                font-size: 14px;
                line-height: 1.5;
            ">
                <div><strong>Examination Title:</strong> {exam_name}</div>
                <div><strong>Subject:</strong> {year_level}</div>
                <div><strong>Academic Year:</strong> {academic_year}</div>
                <div><strong>Examination Type:</strong> {exam_type}</div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Difficulty and Discrimination Indices")
        st.dataframe(df, use_container_width=True)

        st.markdown("### Test Reliability")

        reliability_df = pd.DataFrame({
            "Measure": [
                "KR-20 Coefficient",
                "Reliability Interpretation"
            ],
            "Result": [
                round(alpha, 3),
                kr_label(alpha)
            ]
        })

        st.dataframe(reliability_df, use_container_width=True)

        # ===============================
        # OVERALL ITEM INDEX SUMMARY
        # ===============================
        st.markdown("### Overall Item Index Summary")

        overall_p = sum(
            item["Difficulty Index (P)"] for item in results
        ) / len(results)

        overall_d = sum(
            item["Discrimination Index (D)"] for item in results
        ) / len(results)

        overall_df = pd.DataFrame({
            "Index": [
                "Overall Difficulty Index (P̄)",
                "Overall Discrimination Index (D̄)"
            ],
            "Computed Value": [
                round(overall_p, 3),
                round(overall_d, 3)
            ],
            "Interpretation": [
                difficulty_label(overall_p),
                discrimination_label(overall_d)
            ]
        })

        st.dataframe(overall_df, use_container_width=True)
    

# ===============================
# APP FLOW
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False

if not st.session_state.show_login:
    landing_page()
elif not st.session_state.logged_in:
    login_page()
else:
    main_app()
