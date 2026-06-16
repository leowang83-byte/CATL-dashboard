import streamlit as st


def render_market_monitor(df):
    st.subheader("市场信号")
    st.write("GFEX + SC6 + 现货价格 + 价差验证")
