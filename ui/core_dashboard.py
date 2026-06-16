import streamlit as st


def render_core_dashboard(df):
    st.subheader("全球锂资源战略状态")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("LCE价格状态", "偏强")
    col2.metric("市场验证状态", "进行中")
    col3.metric("90%AISC支撑", "有效")
    col4.metric("供需方向", "收紧")
    col5.metric("风险国家", "上升")
