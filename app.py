import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import math

# ===============================
# PAGE CONFIG & STYLE
# ===============================
st.set_page_config(
    page_title="ARETE Item Analysis Automated System",
    page_icon="📂",
    layout="wide"
)

st.markdown("""
<style>
.big-title {
    font-size: 36px;
    font-weight: 700;
    color: #0A2A66;
}
.sub-title {
    font-size: 18px;
    color: #555;
}
.section {
    background-color: #F8F9FA;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# UTILITIES
# ===============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    if d >= 0.20 and not (0.26 <= p <= 0.75):
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
# LOGIN
# ===============================
def login_page():
    st.markdown('<div class="big-title">CTE Faculty Login</div>', unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = pd.read_csv("users.csv")

        match = users[
            (users["username"] == username) &
            (users["password"] == password)
        ]

        if not match.empty:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ===============================
# MAIN APP
# ===============================
def main_app():
    st.markdown('<div class="big-title">ARETE Departmental Assessment Item Analytics System (DAIAS)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Difficulty • Discrimination • Reliability</div>', unsafe_allow_html=True)

    st.markdown("---")

    responses_file = st.file_uploader("📄 Upload Student Responses (CSV)", type="csv")
    key_file = st.file_uploader("📑 Upload Answer Key (CSV)", type="csv")

    if responses_file and key_file:
        responses = pd.read_csv(responses_file)
        key = pd.read_csv(key_file)

        # Identify item columns
        item_cols = [c for c in responses.columns if c.lower().startswith("item")]

        # --- KEY ALIGNMENT (SAFE) ---
        if key.shape[0] == 1:
            common_items = [c for c in item_cols if c in key.columns]
            responses = responses[common_items]
            key = key[common_items]

        elif key.shape[1] == 2:
            key.columns = ["Item", "Answer"]
            key_dict = dict(zip(key["Item"], key["Answer"]))
            common_items = [c for c in item_cols if c in key_dict]

            responses = responses[common_items]
            key = pd.DataFrame([[key_dict[c] for c in common_items]], columns=common_items)

        else:
            st.error("❌ Invalid key format")
            return

        # Binary scoring
        scored = (responses == key.iloc[0]).astype(int)

        # Total scores
        scores = scored.sum(axis=1)
        scored["Total"] = scores

        # Sort by score
        scored = scored.sort_values("Total", ascending=False)

        # 27% groups
        n = len(scored)
        g = max(1, math.floor(0.27 * n))
        top = scored.head(g)
        bottom = scored.tail(g)

        results = []

        for item in common_items:
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

        result_df = pd.DataFrame(results)

        # Reliability
        alpha = kr20(scored[common_items])

        st.markdown("### 📂 Item Analysis Results")
        st.dataframe(result_df, use_container_width=True)

        st.markdown("### 📈 Test Reliability")
        st.metric(
            label="KR-20 Reliability Coefficient",
            value=round(alpha, 3),
            delta=kr_label(alpha)
        )

        # Download
        st.download_button(
            "⬇ Download Item Analysis",
            result_df.to_csv(index=False),
            "item_analysis_results.csv",
            "text/csv"
        )

# ===============================
# APP FLOW
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
