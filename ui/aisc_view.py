import streamlit as st


def render_aisc_view(df):
    st.subheader("AISC成本结构")
    st.dataframe(df[["project_name", "adjusted_aisc", "risk_adjusted_aisc"]])
