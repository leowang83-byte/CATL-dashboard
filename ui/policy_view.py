import streamlit as st


def render_policy_view(df):
    st.subheader("政策风险结构")
    st.bar_chart(df["policy_risk_score"])
