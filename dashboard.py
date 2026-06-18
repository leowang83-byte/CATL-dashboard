from pathlib import Path
import html
import textwrap
import streamlit as st
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pydeck as pdk

from dashboard_data_contract import REPORTS_DIR, apply_contract, empty_contract_frame


# =========================
# 基础配置
# =========================

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DATA_HEALTH = []

CATL_BLUE = "#0035A8"
CATL_BLUE_DARK = "#002A85"
CATL_BLUE_LIGHT = "#B3D0F7"
CATL_BLUE_PALE = "#EBF2FD"
CATL_BLUE_2 = CATL_BLUE_DARK
LIGHT_BLUE = CATL_BLUE_PALE
PAGE_BG = "#F7F9FC"
CARD_BG = "#FFFFFF"
BORDER = "#D9E2F2"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#64748B"
TEAL = "#00AB96"
TEAL_LIGHT = "#80DEEA"
TEAL_PALE = "#E0F7FA"
CORAL = "#FF6B35"
CORAL_DARK = "#D84315"
CORAL_LIGHT = "#FFCCBC"
CORAL_PALE = "#FBE9E7"
NEUTRAL = "#6B7280"
NEUTRAL_LIGHT = "#D1D5DB"
NEUTRAL_DARK = "#1F2937"
GREEN = TEAL
ORANGE = CORAL
RED = CORAL_DARK
IMPACT_HIGH = "#58A65A"
IMPACT_MEDIUM = "#E2BE33"
IMPACT_LOW = "#E0A03A"
IMPACT_NEGATIVE = "#C94134"
# =========================
# 论文锚定参数
# 来源：最新版《全球锂资源投资与碳酸锂供需前瞻》
# 单位说明：
# - 供应量：万吨 LCE
# - 价格：万元/吨 LCE
# - 成本：万元/吨 LCE
# =========================

PAPER_GLOBAL_SUPPLY_2025 = 154.2
PAPER_SPODUMENE_SUPPLY_2025 = 79.6
PAPER_BRINE_SUPPLY_2025 = 57.4
PAPER_LEPIDOLITE_SUPPLY_2025 = 17.2

PAPER_SPODUMENE_SHARE_2025 = 0.52
PAPER_BRINE_SHARE_2025 = 0.37
PAPER_LEPIDOLITE_SHARE_2025 = 0.11

PAPER_SPOT_PRICE_WAN = 17.77
PAPER_PRICE_CENTER_WAN = 18.20
PAPER_PRICE_LOW_WAN = 17.00
PAPER_PRICE_HIGH_WAN = 19.50

PAPER_AISC_90_LOW_WAN = 19.00
PAPER_AISC_90_HIGH_WAN = 20.00
PAPER_AISC_90_MID_WAN = 19.50

PAPER_INVENTORY_LEAD_WEEKS_LOW = 2
PAPER_INVENTORY_LEAD_WEEKS_HIGH = 4
PAPER_INVENTORY_THRESHOLD_DAYS = 14
PAPER_INVENTORY_NEUTRAL_DAYS = 21

PAPER_HEDGE_SHORT_PUT_WAN = 16.50
PAPER_HEDGE_LONG_CALL_WAN = 19.50

PAPER_WACC = 0.085
PAPER_LONG_TERM_LCE_PRICE_WAN = 12.00
PAPER_MIN_IRR = 0.12
PAPER_DLE_TARGET_AISC_WAN = 4.50

st.set_page_config(
    page_title="全球锂资源智能决策驾驶舱DEMO--作者：王亮",
    layout="wide",
)


# =========================
# 全局样式
# =========================

st.markdown(
    f"""
    <style>
    :root {{
        --font-page-title: 32px;
        --font-brand: 26px;
        --font-section-title: 20px;
        --font-subsection-title: 18px;
        --font-card-title: 15px;
        --font-body: 15px;
        --font-caption: 12px;
        --font-kpi-xl: 30px;
        --font-kpi-lg: 28px;
        --font-kpi-md: 23px;
        --line-body: 1.6;
        --line-tight: 1.2;
    }}

    html, body {{
        font-size: var(--font-body);
    }}

    .stApp {{
        background-color: {PAGE_BG};
        color: {TEXT_DARK};
    }}

    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] label,
    div[data-testid="stMarkdownContainer"] span,
    .stCaption,
    .stAlert {{
        font-size: var(--font-body);
        line-height: var(--line-body);
    }}

    div[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {BORDER};
    }}

    .main-title {{
        font-size: var(--font-page-title);
        font-weight: 800;
        color: {CATL_BLUE};
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }}

    .sub-title {{
        font-size: 14px;
        color: {TEXT_MUTED};
        margin-bottom: 12px;
    }}

    .catl-logo {{
        font-size: var(--font-brand);
        font-weight: 900;
        color: {CATL_BLUE};
        letter-spacing: 1px;
    }}

    .dashboard-header {{
        display: grid;
        grid-template-columns: 1.1fr 2.4fr 1.2fr;
        align-items: center;
        gap: 18px;
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: 0 2px 8px rgba(0, 58, 140, 0.06);
        margin-bottom: 10px;
    }}

    .header-center {{
        text-align: center;
    }}

    .header-status {{
        text-align: right;
        color: {TEXT_MUTED};
        font-size: 13px;
        font-weight: 700;
        line-height: 1.6;
    }}

    .section-title {{
        background: linear-gradient(90deg, {CATL_BLUE}, {CATL_BLUE_2});
        color: white !important;
        padding: 8px 14px;
        border-radius: 8px 8px 0px 0px;
        font-size: var(--font-section-title);
        font-weight: 800;
        margin-top: 18px;
        margin-bottom: 0px;
    }}

    .section-card {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 0px 0px 12px 12px;
        padding: 18px;
        margin-bottom: 22px;
        box-shadow: 0 2px 8px rgba(0, 58, 140, 0.06);
    }}

    .kpi-card {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER};
        border-left: 6px solid {CATL_BLUE_2};
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 118px;
        box-shadow: 0 2px 8px rgba(0, 58, 140, 0.07);
    }}

    .kpi-label {{
        font-size: var(--font-card-title);
        color: {TEXT_MUTED};
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .kpi-value {{
        font-size: var(--font-kpi-xl);
        color: {CATL_BLUE};
        font-weight: 900;
        line-height: 1.1;
        white-space: normal;
        overflow-wrap: break-word;
        word-break: break-word;
    }}

    .kpi-note {{
        font-size: var(--font-caption);
        color: {TEXT_MUTED};
        margin-top: 8px;
        line-height: 1.35;
    }}

    .executive-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
    }}

    .executive-kpi-card {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-top: 4px solid {CATL_BLUE_2};
        border-radius: 12px;
        padding: 14px 14px 13px 14px;
        min-height: 132px;
        box-shadow: 0 3px 10px rgba(0, 58, 140, 0.07);
    }}

    .executive-kpi-card.risk {{
        border-top-color: {ORANGE};
    }}

    .executive-kpi-label {{
        color: {TEXT_MUTED};
        font-size: 13px;
        font-weight: 800;
        line-height: 1.25;
        margin-bottom: 10px;
    }}

    .executive-kpi-value {{
        color: {CATL_BLUE};
        font-size: var(--font-kpi-lg);
        line-height: 1.1;
        font-weight: 900;
        overflow-wrap: break-word;
    }}

    .executive-kpi-unit {{
        color: {TEXT_MUTED};
        font-size: var(--font-caption);
        font-weight: 800;
        margin-top: 4px;
    }}

    .executive-kpi-note {{
        color: {TEXT_MUTED};
        font-size: var(--font-caption);
        line-height: 1.35;
        margin-top: 8px;
    }}

    .executive-insight-box {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-left: 6px solid {CATL_BLUE_2};
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 3px 10px rgba(0, 58, 140, 0.06);
        min-height: 390px;
    }}

    .executive-insight-box h4 {{
        color: {CATL_BLUE};
        font-size: var(--font-subsection-title);
        font-weight: 900;
        margin: 0 0 12px 0;
    }}

    .executive-insight-item {{
        padding: 10px 0;
        border-bottom: 1px solid #EEF2F7;
        color: {TEXT_DARK};
        font-size: var(--font-body);
        line-height: 1.65;
    }}

    .executive-insight-item:last-child {{
        border-bottom: 0;
    }}

    .signal-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-top: 16px;
    }}

    .signal-card {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-left: 5px solid {CATL_BLUE_2};
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 8px rgba(0, 58, 140, 0.06);
    }}

    .signal-label {{
        color: {TEXT_MUTED};
        font-size: 13px;
        font-weight: 800;
        margin-bottom: 6px;
    }}

    .signal-value {{
        color: {CATL_BLUE};
        font-size: var(--font-kpi-md);
        font-weight: 900;
        margin-bottom: 6px;
    }}

    .signal-note {{
        color: {TEXT_MUTED};
        font-size: var(--font-caption);
        line-height: 1.4;
    }}

    @media (max-width: 1200px) {{
        .executive-kpi-grid {{
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }}

        .signal-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}

    @media (max-width: 760px) {{
        .executive-kpi-grid,
        .signal-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    .compact-card {{
        background-color: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 12px 14px;
        min-height: 92px;
        box-shadow: 0 2px 6px rgba(0, 58, 140, 0.05);
        overflow-wrap: break-word;
        word-break: break-word;
    }}

    .compact-label {{
        font-size: 13px;
        color: {TEXT_MUTED};
        font-weight: 700;
        margin-bottom: 8px;
        line-height: 1.3;
    }}

    .compact-value {{
        font-size: var(--font-kpi-md);
        color: {CATL_BLUE};
        font-weight: 900;
        line-height: 1.25;
        white-space: normal;
        overflow-wrap: break-word;
        word-break: break-word;
    }}

    .compact-note {{
        font-size: var(--font-caption);
        color: {TEXT_MUTED};
        margin-top: 6px;
        line-height: 1.3;
    }}

    .insight-box {{
        background-color: {LIGHT_BLUE};
        border: 1px solid #BFD7FF;
        border-left: 6px solid {CATL_BLUE_2};
        border-radius: 10px;
        padding: 14px 16px;
        color: {TEXT_DARK};
        font-size: var(--font-body);
        line-height: 1.65;
        margin-bottom: 14px;
    }}

    .strategy-box {{
        background-color: #F8FAFC;
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 14px 16px;
        color: {TEXT_DARK};
        font-size: var(--font-body);
        line-height: 1.65;
        margin-bottom: 12px;
    }}

    .small-muted {{
        color: {TEXT_MUTED};
        font-size: var(--font-caption);
    }}

    div[role="radiogroup"] {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 8px;
        margin-top: 8px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0, 58, 140, 0.06);
        gap: 6px;
    }}

    div[role="radiogroup"] label {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 14px;
        margin-right: 6px;
        background: #F8FAFC;
        color: {CATL_BLUE} !important;
        font-weight: 700;
        transition: all 0.15s ease;
    }}

    div[role="radiogroup"] label:hover {{
        background: {LIGHT_BLUE};
        border-color: {CATL_BLUE_2};
    }}

    div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(90deg, {CATL_BLUE}, {CATL_BLUE_2});
        border-color: {CATL_BLUE};
        box-shadow: 0 3px 10px rgba(0, 58, 140, 0.18);
    }}

    div[role="radiogroup"] label:has(input:checked) p,
    div[role="radiogroup"] label:has(input:checked) span {{
        color: #FFFFFF !important;
        font-weight: 800;
    }}

    div[data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 2px 6px rgba(0, 58, 140, 0.05);
    }}

    div[data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED};
        font-size: var(--font-caption);
        font-weight: 700;
    }}

    div[data-testid="stMetricValue"] {{
        color: {CATL_BLUE};
        font-size: var(--font-kpi-md);
        line-height: var(--line-tight);
        font-weight: 900;
    }}

    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: {TEXT_DARK};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 工具函数
# =========================

def ensure_columns(df, columns, default=""):
    if df is None:
        df = pd.DataFrame()
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = default
    return df


def safe_col(df, col, default=None):
    if df is None or col not in df.columns:
        if default is None:
            default = ""
        length = 0 if df is None else len(df)
        return pd.Series([default] * length)
    return df[col]


def safe_get(row, col, default=""):
    try:
        value = row.get(col, default)
        if pd.isna(value):
            return default
        return value
    except Exception:
        return default


def to_num(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _read_csv_with_fallback(file_path):
    last_error = ""
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(file_path, encoding=encoding), f"read_ok:{encoding}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return pd.DataFrame(), f"read_error:{last_error}"


def load_csv(file_name):
    file_path = REPORTS_DIR / file_name

    if not file_path.exists() or file_path.stat().st_size == 0:
        df = empty_contract_frame(file_name)
        status = "missing_file" if not file_path.exists() else "empty_file"
    else:
        df, status = _read_csv_with_fallback(file_path)

    try:
        df, health = apply_contract(df, file_name)
    except Exception as exc:
        df = empty_contract_frame(file_name)
        health = {
            "file_name": file_name,
            "status": "contract_error",
            "read_status": f"{type(exc).__name__}: {exc}",
            "rows": 0,
            "columns": len(df.columns),
            "missing_required_columns": "",
            "is_empty": True,
            "notes": "",
        }

    health["read_status"] = status
    DASHBOARD_DATA_HEALTH.append(health)
    return df


def load_policy_news_risk_data():
    policy_files = {
        "policy_scored_table": "policy_scored_table.csv",
        "policy_timeline_events": "policy_timeline_events.csv",
        "lithium_policy_decomposed_risk": "lithium_policy_decomposed_risk.csv",
        "project_strategic_aisc_v2": "project_strategic_aisc_v2.csv",
        "raw_disclosure_events": "raw_disclosure_events.csv",
    }

    data = {}
    for key, file_name in policy_files.items():
        try:
            file_path = REPORTS_DIR / file_name
            if not file_path.exists():
                data[key] = None
            else:
                data[key] = load_csv(file_name)
        except Exception:
            data[key] = None

    return data


def get_float(row, col, default=0.0):
    try:
        return float(row.get(col, default))
    except Exception:
        return default


def safe_num(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_aisc_dashboard_metrics():
    df = load_csv("aisc_dashboard_metrics.csv")
    if df.empty or "metric_name" not in df.columns or "metric_value" not in df.columns:
        return {}

    metrics = {}
    for _, row in df.iterrows():
        key = str(row.get("metric_name", "")).strip()
        value = row.get("metric_value", "")
        metrics[key] = value
    return metrics


def metric_float(metrics, key, default=0.0):
    try:
        return float(metrics.get(key, default))
    except Exception:
        return default


def metric_text(metrics, key, default=""):
    value = metrics.get(key, default)
    if pd.isna(value):
        return default
    return str(value)


def format_wan(value):
    try:
        return f"{float(value) / 10000:.2f} 万元/吨"
    except Exception:
        return "N/A"


def get_inventory_signal(inventory_days):
    try:
        inventory_days = float(inventory_days)
    except Exception:
        inventory_days = 0

    if inventory_days <= 0:
        return {
            "status": "暂无数据",
            "color": "#64748B",
            "bg": "#F8FAFC",
            "border": "#CBD5E1",
            "price_implication": "当前库存数据缺失，暂不生成价格状态判断。",
            "management_action": "请先检查价格模型输入。",
        }

    if inventory_days <= PAPER_INVENTORY_THRESHOLD_DAYS:
        return {
            "status": "反弹窗口",
            "color": "#16A34A",
            "bg": "#ECFDF5",
            "border": "#86EFAC",
            "price_implication": "库存低于14天阈值，价格由弱势区向紧平衡或反弹窗口切换的概率上升。",
            "management_action": "建议提前准备补库、长协锁价、低成本资源谈判和套保上沿保护。",
        }

    if inventory_days <= PAPER_INVENTORY_NEUTRAL_DAYS:
        return {
            "status": "中性观察",
            "color": "#F59E0B",
            "bg": "#FFFBEB",
            "border": "#FCD34D",
            "price_implication": "库存压力已有缓解，但尚未形成强反弹信号，价格方向仍取决于排产、成交和仓单变化。",
            "management_action": "建议跟踪储能排产、正极开工率、GFEX仓单和现货成交。",
        }

    return {
        "status": "库存压制",
        "color": "#DC2626",
        "bg": "#FEF2F2",
        "border": "#FCA5A5",
        "price_implication": "库存明显高于14天阈值，价格仍处于库存压制区，上行弹性受限。",
        "management_action": "建议控制采购节奏，等待更优价格或资源估值窗口。",
    }


def render_inventory_signal_panel(inventory_days):
    signal = get_inventory_signal(inventory_days)

    try:
        inventory_days_value = float(inventory_days)
    except Exception:
        inventory_days_value = 0

    inventory_display = f"{inventory_days_value:.1f} 天" if inventory_days_value > 0 else "N/A"
    inventory_value_color = CATL_BLUE
    threshold_value_color = signal["color"]
    status_value_color = CATL_BLUE
    lead_window_color = signal["color"]

    st.markdown("#### 库存阈值与价格反弹窗口")

    st.markdown(
        f"""
        <div style="
            background:{signal['bg']};
            border:1px solid {signal['border']};
            border-left:6px solid {signal['color']};
            border-radius:12px;
            padding:16px 18px;
            margin-bottom:14px;
            box-shadow:0 2px 8px rgba(0, 58, 140, 0.06);
        ">
            <div style="
                display:grid;
                grid-template-columns:repeat(4, minmax(0, 1fr));
                gap:12px;
                margin-bottom:14px;
            ">
                <div style="background:#FFFFFF;border:1px solid #D9E2F2;border-radius:10px;padding:12px;">
                    <div style="font-size:13px;color:#64748B;font-weight:800;">当前库存天数</div>
                    <div style="font-size:26px;color:{inventory_value_color};font-weight:900;margin-top:6px;">{inventory_display}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:6px;">来自当前价格模型输入</div>
                </div>
                <div style="background:#FFFFFF;border:1px solid #D9E2F2;border-radius:10px;padding:12px;">
                    <div style="font-size:13px;color:#64748B;font-weight:800;">库存切换阈值</div>
                    <div style="font-size:26px;color:{threshold_value_color};font-weight:900;margin-top:6px;">{PAPER_INVENTORY_THRESHOLD_DAYS} 天</div>
                    <div style="font-size:12px;color:#64748B;margin-top:6px;">低于阈值，反弹概率上升</div>
                </div>
                <div style="background:#FFFFFF;border:1px solid #D9E2F2;border-radius:10px;padding:12px;">
                    <div style="font-size:13px;color:#64748B;font-weight:800;">当前状态</div>
                    <div style="font-size:26px;color:{status_value_color};font-weight:900;margin-top:6px;">{signal['status']}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:6px;">库存驱动的价格状态</div>
                </div>
                <div style="background:#FFFFFF;border:1px solid #D9E2F2;border-radius:10px;padding:12px;">
                    <div style="font-size:13px;color:#64748B;font-weight:800;">领先观察窗口</div>
                    <div style="font-size:26px;color:{lead_window_color};font-weight:900;margin-top:6px;">{PAPER_INVENTORY_LEAD_WEEKS_LOW}-{PAPER_INVENTORY_LEAD_WEEKS_HIGH} 周</div>
                    <div style="font-size:12px;color:#64748B;margin-top:6px;">库存变化领先价格反应</div>
                </div>
            </div>
            <div style="
                background:#FFFFFF;
                border:1px solid #D9E2F2;
                border-radius:10px;
                padding:13px 15px;
                line-height:1.7;
                color:#1F2937;
                font-size:14px;
            ">
                <b style="color:{signal['color']};">价格含义：</b>{signal['price_implication']}<br>
                <b style="color:{signal['color']};">管理动作：</b>{signal['management_action']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "说明：14天库存阈值用于识别价格反弹窗口。"
        "该信号需结合现货价格、正极开工率、储能排产、GFEX仓单和AISC成本支撑共同判断。"
    )


def kpi_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="compact-card">
            <div class="compact-label">{label}</div>
            <div class="compact-value">{value}</div>
            <div class="compact-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(number, title):
    st.markdown(
        f"""
        <div class="section-title">{number}　{title}</div>
        """,
        unsafe_allow_html=True,
    )


def subsection_title(title, subtitle=""):
    st.markdown(
        f"""
        <div style="
            background:#F8FAFC;
            border:1px solid #D9E2F2;
            border-left:6px solid #0052CC;
            border-radius:10px;
            padding:12px 16px;
            margin:18px 0 12px 0;
        ">
            <div style="font-size:var(--font-subsection-title);font-weight:900;color:#003A8C;">{title}</div>
            <div style="font-size:var(--font-caption);color:#64748B;margin-top:4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_open():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def section_close():
    st.markdown("</div>", unsafe_allow_html=True)


def topic_intro(title, body):
    st.markdown(
        f"""
        <div class="insight-box">
        <b>{title}</b><br>
        {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_enterprise_layout(fig, title=None, height=None):
    layout_args = {
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "font": dict(color=TEXT_DARK, size=13),
        "legend": dict(font=dict(color=TEXT_DARK)),
        "margin": dict(l=10, r=10, t=60, b=10),
    }

    if title:
        layout_args["title"] = title
        layout_args["title_font"] = dict(color=CATL_BLUE, size=22)

    if height:
        layout_args["height"] = height

    fig.update_layout(**layout_args)
    fig.update_xaxes(
        gridcolor="#E5E7EB",
        color=TEXT_DARK,
        title_font=dict(color=TEXT_DARK),
    )
    fig.update_yaxes(
        gridcolor="#E5E7EB",
        color=TEXT_DARK,
        title_font=dict(color=TEXT_DARK),
    )
    return fig


def render_policy_timeline_chart(policy_timeline_df):
    timeline_catl_blue = "#003A8C"
    st.markdown("#### IEA\u5168\u7403\u5173\u952e\u77ff\u4ea7\u653f\u7b56\u98ce\u9669\u6f14\u5316\uff082025-2035\uff09")
    st.caption("\u6240\u6709\u56fd\u5bb6\u653f\u7b56\u5df2\u7edf\u4e00\u6620\u5c04\u81f3\u6218\u7565\u65f6\u95f4\u8f74\uff0c\u5c55\u793a\u5b58\u91cf\u653f\u7b56\u7ea6\u675f\u4e0e\u672a\u6765\u5f3a\u5236\u8282\u70b9\u3002")

    if policy_timeline_df.empty:
        st.info(
            "IEA\u653f\u7b56\u65f6\u95f4\u7ebf\u6570\u636e\u5f85\u63a5\u5165\uff0c\u8bf7\u5148\u8fd0\u884c\uff1a\n"
            "python policy_schema_engine.py\n"
            "python policy_scoring_engine.py"
        )
        return

    timeline_df = policy_timeline_df.copy()
    timeline_df["timeline_year"] = pd.to_numeric(
        timeline_df.get("timeline_year", pd.Series(dtype=float)),
        errors="coerce",
    )
    timeline_df = timeline_df[
        timeline_df["timeline_year"].between(2025, 2035, inclusive="both")
    ].copy()

    if timeline_df.empty:
        st.info(
            "IEA\u653f\u7b56\u65f6\u95f4\u7ebf\u6570\u636e\u5f85\u63a5\u5165\uff0c\u8bf7\u5148\u8fd0\u884c\uff1a\n"
            "python policy_schema_engine.py\n"
            "python policy_scoring_engine.py"
        )
        return

    lane_order = [
        "\u51fa\u53e3\u9650\u5236\u4e0e\u672c\u5730\u52a0\u5de5",
        "\u56fd\u5bb6\u63a7\u80a1\u4e0e\u56fd\u5bb6\u53c2\u4e0e",
        "\u7a0e\u8d39\u6743\u5229\u91d1\u4e0e\u8bb8\u53ef\u7ea6\u675f",
        "\u73af\u4fdd\u4fdd\u62a4\u4e0e\u6c34\u8d44\u6e90\u7ea6\u675f",
        "\u653f\u7b56\u652f\u6301\u4e0e\u4f9b\u5e94\u7a33\u5b9a",
        "\u6218\u7565\u89c4\u5212\u4e0e\u4ea7\u4e1a\u652f\u6301",
        "\u56de\u6536\u4e0e\u5faa\u73af\u4f53\u7cfb",
        "\u5176\u4ed6\u653f\u7b56\u7ea6\u675f",
    ]
    lane_y_map = {lane: len(lane_order) - idx for idx, lane in enumerate(lane_order)}
    risk_rank = {"\u6781\u9ad8": 5, "\u9ad8": 4, "\u4e2d\u9ad8": 3, "\u4e2d": 2, "\u4f4e": 1}
    risk_colors = {
        "\u6781\u9ad8": "#FF6835",
        "\u9ad8": "#C94134",
        "\u4e2d\u9ad8": "#FF6B35",
        "\u4e2d": "#E2BE33",
        "\u4f4e": "#58A65A",
    }
    lane_colors = {
        "\u5176\u4ed6\u653f\u7b56\u7ea6\u675f": "#1A5AD4",
    }

    timeline_df["timeline_lane"] = timeline_df.get(
        "timeline_lane",
        pd.Series(lane_order[-1], index=timeline_df.index),
    ).fillna(lane_order[-1])
    timeline_df.loc[~timeline_df["timeline_lane"].isin(lane_order), "timeline_lane"] = lane_order[-1]
    timeline_df["timeline_y"] = timeline_df["timeline_lane"].map(lane_y_map)
    timeline_df["timeline_weight"] = pd.to_numeric(
        timeline_df.get("timeline_weight", pd.Series(0.5, index=timeline_df.index)),
        errors="coerce",
    ).fillna(0.5).clip(0, 1)
    timeline_df["risk_score"] = pd.to_numeric(
        timeline_df.get("risk_score", pd.Series(0.4, index=timeline_df.index)),
        errors="coerce",
    ).fillna(0.4).clip(0, 1)
    timeline_df["risk_level"] = timeline_df.get(
        "risk_level",
        pd.Series("\u4e2d", index=timeline_df.index),
    ).fillna("\u4e2d").astype(str)
    timeline_df.loc[~timeline_df["risk_level"].isin(risk_rank), "risk_level"] = "\u4e2d"
    timeline_df["risk_rank"] = timeline_df["risk_level"].map(risk_rank).fillna(2)
    timeline_df["risk_direction"] = timeline_df.get(
        "risk_direction",
        pd.Series("", index=timeline_df.index),
    ).fillna("").astype(str)
    timeline_df["source_url"] = timeline_df.get(
        "source_url",
        pd.Series("", index=timeline_df.index),
    ).fillna("").astype(str)
    timeline_df["hover_text_safe"] = timeline_df.get(
        "hover_text",
        pd.Series("", index=timeline_df.index),
    ).fillna("").astype(str)
    timeline_df["event_id"] = timeline_df.get(
        "event_id",
        timeline_df.get("policy_id", pd.Series("", index=timeline_df.index)),
    ).fillna("").astype(str)
    timeline_df["policy_name"] = timeline_df.get(
        "policy_name",
        pd.Series("", index=timeline_df.index),
    ).fillna("").astype(str)
    timeline_df["country"] = timeline_df.get(
        "country",
        pd.Series("Unknown", index=timeline_df.index),
    ).fillna("Unknown").astype(str)
    timeline_df["timeline_context"] = timeline_df["timeline_year"].apply(
        lambda year: "\u5b58\u91cf\u7ea6\u675f" if int(year) == 2025 else "\u653f\u7b56\u8282\u70b9"
    )

    continuation_policy_types = {
        "export_control",
        "local_processing",
        "state_control",
        "tax_royalty",
        "permitting",
        "investment_restriction",
        "environment_policy",
    }
    continuation_rows = []
    for _, base_row in timeline_df.iterrows():
        base_year = int(base_row["timeline_year"])
        policy_type = str(base_row.get("policy_type", "") or "")
        if policy_type not in continuation_policy_types:
            continue
        for continuation_year in [2027, 2030, 2035]:
            if continuation_year <= base_year:
                continue
            projected_row = base_row.copy()
            projected_row["timeline_year"] = continuation_year
            projected_row["timeline_context"] = "\u6301\u7eed\u5f71\u54cd\u8282\u70b9"
            projected_row["event_id"] = f"{base_row.get('event_id', '')}_cont_{continuation_year}"
            continuation_rows.append(projected_row)
    timeline_df["is_continuation_node"] = False
    if continuation_rows:
        continuation_df = pd.DataFrame(continuation_rows)
        continuation_df["is_continuation_node"] = True
        timeline_df = pd.concat([timeline_df, continuation_df], ignore_index=True)
    timeline_df["is_continuation_node"] = timeline_df["is_continuation_node"].fillna(False).astype(bool)

    detail_df = timeline_df.copy()
    detail_df["node_id"] = detail_df.apply(
        lambda row: f"{int(row['timeline_year'])}|{row['timeline_lane']}",
        axis=1,
    )

    aggregate_rows = []
    for (year, lane), group in detail_df.groupby(["timeline_year", "timeline_lane"], dropna=False):
        max_idx = group["risk_rank"].idxmax()
        representative = group.loc[max_idx]
        countries = group["country"].dropna().astype(str).unique().tolist()
        original_policy_count = int((~group["is_continuation_node"]).sum())
        continuation_policy_count = int(group["is_continuation_node"].sum())
        policy_count = len(group)
        supportive_count = int(group["risk_direction"].str.lower().eq("supportive").sum())
        is_supportive = supportive_count >= max(1, policy_count / 2)
        risk_level_value = str(representative.get("risk_level", "\u4e2d") or "\u4e2d")
        if continuation_policy_count > 0:
            marker_color = "#FFAB91"
        elif lane in lane_colors:
            marker_color = lane_colors[lane]
        else:
            marker_color = "#00AB96" if is_supportive else risk_colors.get(risk_level_value, "#4B5563")
        aggregate_rows.append(
            {
                "node_id": f"{int(year)}|{lane}",
                "timeline_year": int(year),
                "timeline_lane": lane,
                "timeline_y": lane_y_map.get(lane, 1),
                "risk_level": risk_level_value,
                "risk_rank": float(group["risk_rank"].max()),
                "risk_score": float(group["risk_score"].max()),
                "timeline_weight": float(group["timeline_weight"].max()),
                "policy_count": policy_count,
                "original_policy_count": original_policy_count,
                "continuation_policy_count": continuation_policy_count,
                "country_count": len(countries),
                "countries": "\u3001".join(countries[:8]),
                "marker_color": marker_color,
                "timeline_context": "\u5b58\u91cf\u7ea6\u675f" if int(year) == 2025 else "\u672a\u6765/\u6301\u7eed\u5f71\u54cd\u8282\u70b9" if int(year) >= 2027 else "\u653f\u7b56\u8282\u70b9",
            }
        )
    aggregate_df = pd.DataFrame(aggregate_rows)

    placeholder_rows = []
    placeholder_lanes = lane_order[:4]
    existing_nodes = set(zip(aggregate_df["timeline_year"], aggregate_df["timeline_lane"])) if not aggregate_df.empty else set()
    for year in range(2027, 2036):
        for lane in placeholder_lanes:
            if (year, lane) in existing_nodes:
                continue
            placeholder_rows.append(
                {
                    "node_id": f"placeholder|{year}|{lane}",
                    "timeline_year": year,
                    "timeline_lane": lane,
                    "timeline_y": lane_y_map[lane],
                    "hover_text": (
                        f"\u6982\u5ff5\u5360\u4f4d<br>\u5e74\u4efd\uff1a{year}<br>\u653f\u7b56\u6cf3\u9053\uff1a{lane}<br>"
                        "\u8bf4\u660e\uff1a\u8be5\u8282\u70b9\u4ec5\u8868\u793a\u672a\u6765\u653f\u7b56\u660e\u7ec6\u5f85IEA\u5e95\u5e93\u63a5\u5165\uff0c\u4e0d\u4ee3\u8868\u771f\u5b9e\u65b0\u589e\u653f\u7b56\u3002"
                    ),
                }
            )
    placeholder_df = pd.DataFrame()

    fig = go.Figure()
    if not aggregate_df.empty:
        aggregate_df["marker_size"] = (
            18
            + aggregate_df["timeline_weight"].clip(0, 1) * 24
            + aggregate_df["policy_count"].clip(upper=10) * 2
        )
        aggregate_df["node_group"] = "\u666e\u901a\u653f\u7b56\u8282\u70b9"
        aggregate_df.loc[aggregate_df["timeline_year"] == 2025, "node_group"] = "\u5b58\u91cf\u7ea6\u675f\u8282\u70b9"
        aggregate_df.loc[aggregate_df["timeline_year"] >= 2027, "node_group"] = "\u672a\u6765\u7ea6\u675f\u8282\u70b9"
        aggregate_df["hover_text"] = aggregate_df.apply(
            lambda row: (
                f"<b>{row['timeline_year']}\uff5c{row['timeline_context']}</b><br>"
                f"\u6cf3\u9053\uff1a{row['timeline_lane']}<br>"
                f"\u6700\u9ad8\u98ce\u9669\u7b49\u7ea7\uff1a{row['risk_level']}<br>"
                f"\u56fd\u5bb6\u6570\u91cf\uff1a{row['country_count']}<br>"
                f"\u539f\u59cb\u653f\u7b56\u6761\u6570\uff1a{row['original_policy_count']}<br>"
                f"\u6301\u7eed\u5f71\u54cd\u8282\u70b9\uff1a{row['continuation_policy_count']}<br>"
                f"\u56fd\u5bb6\uff1a{row['countries']}<br>"
                + ("\u8bf4\u660e\uff1a\u6301\u7eed\u5f71\u54cd\u8282\u70b9\uff0c\u4e0d\u4ee3\u8868\u65b0\u589e\u653f\u7b56<br>" if row["continuation_policy_count"] > 0 else "")
                + "\u70b9\u51fb\u6c14\u6ce1\u67e5\u770b\u4e0b\u65b9\u653f\u7b56\u89e3\u91ca"
            ),
            axis=1,
        )
        aggregate_df["display_text"] = aggregate_df.apply(
            lambda row: f"{row['timeline_year']}<br>{row['country_count']}\u56fd/{row['original_policy_count']}\u7b56",
            axis=1,
        )

        trace_styles = {
            "\u666e\u901a\u653f\u7b56\u8282\u70b9": {"line_color": "#E5E7EB", "line_width": 1},
            "\u5b58\u91cf\u7ea6\u675f\u8282\u70b9": {"line_color": timeline_catl_blue, "line_width": 2},
            "\u672a\u6765\u7ea6\u675f\u8282\u70b9": {"line_color": "#C94134", "line_width": 3},
        }
        for group_name, style in trace_styles.items():
            group_df = aggregate_df[aggregate_df["node_group"] == group_name]
            if group_df.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=group_df["timeline_year"],
                    y=group_df["timeline_y"],
                    mode="markers+text",
                    name=group_name,
                    showlegend=False,
                    text=group_df["display_text"],
                    textposition="top center",
                    customdata=group_df[["hover_text", "node_id"]].to_numpy(),
                    hovertemplate="%{customdata[0]}<extra></extra>",
                    selected=dict(marker=dict(opacity=0.96)),
                    unselected=dict(marker=dict(opacity=0.96)),
                    marker=dict(
                        size=group_df["marker_size"],
                        color=group_df["marker_color"],
                        opacity=0.96,
                        line=dict(width=0),
                    ),
                )
            )

    if not placeholder_df.empty:
        fig.add_trace(
            go.Scatter(
                x=placeholder_df["timeline_year"],
                y=placeholder_df["timeline_y"],
                mode="markers",
                name="\u6982\u5ff5\u5360\u4f4d",
                showlegend=False,
                customdata=placeholder_df[["hover_text", "node_id"]].to_numpy(),
                hovertemplate="%{customdata[0]}<extra></extra>",
                selected=dict(marker=dict(opacity=0.82)),
                unselected=dict(marker=dict(opacity=0.82)),
                marker=dict(
                    size=11,
                    color="#D1D5DB",
                    symbol="circle",
                    opacity=0.82,
                    line=dict(width=0),
                ),
            )
        )

    fig.update_layout(
        height=600,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=TEXT_DARK, size=13, family="Microsoft YaHei, SimHei, Arial"),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(color=TEXT_DARK, size=13, family="Microsoft YaHei, SimHei, Arial"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color=TEXT_DARK, size=12),
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            borderwidth=1,
        ),
        margin=dict(l=190, r=30, t=62, b=65),
    )
    fig.update_xaxes(
        range=[2024.5, 2035.5],
        tickmode="array",
        tickvals=list(range(2025, 2036)),
        title_text="2025-2035 \u6218\u7565\u653f\u7b56\u98ce\u9669\u65f6\u95f4\u8f74",
        color=timeline_catl_blue,
        title_font=dict(color=timeline_catl_blue, size=14),
        gridcolor="#E5E7EB",
        zeroline=False,
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=[lane_y_map[lane] for lane in lane_order],
        ticktext=lane_order,
        range=[0.4, len(lane_order) + 0.6],
        color=TEXT_DARK,
        gridcolor="#E5E7EB",
        zeroline=False,
    )

    timeline_selection = st.plotly_chart(
        fig,
        width="stretch",
        key="policy_timeline_events_chart",
        on_select="rerun",
        selection_mode="points",
    )

    selected_node_id = ""
    try:
        selected_points = timeline_selection.selection.points
    except Exception:
        selected_points = (
            timeline_selection.get("selection", {}).get("points", [])
            if isinstance(timeline_selection, dict)
            else []
        )
    if selected_points:
        selected_point = selected_points[0]
        selected_customdata = selected_point.get("customdata", []) if isinstance(selected_point, dict) else []
        if isinstance(selected_customdata, (list, tuple)) and len(selected_customdata) > 1:
            selected_node_id = str(selected_customdata[1] or "")

    if selected_node_id.startswith("placeholder|"):
        parts = selected_node_id.split("|", 2)
        year_label = parts[1] if len(parts) > 1 else ""
        lane_label = parts[2] if len(parts) > 2 else ""
        st.info(f"{year_label}\uff5c{lane_label} \u4e3a\u6982\u5ff5\u5360\u4f4d\uff0c\u8868\u793a\u672a\u6765\u653f\u7b56\u660e\u7ec6\u5f85 IEA \u5e95\u5e93\u63a5\u5165\uff0c\u4e0d\u4ee3\u8868\u771f\u5b9e\u65b0\u589e\u653f\u7b56\u3002")
    elif selected_node_id:
        selected_df = detail_df[detail_df["node_id"].astype(str) == selected_node_id].copy()
        if not selected_df.empty:
            year_value = int(selected_df.iloc[0].get("timeline_year", 0))
            lane_value = str(selected_df.iloc[0].get("timeline_lane", "") or "")
            policy_type_cn = {
                "export_control": "\u51fa\u53e3\u9650\u5236",
                "local_processing": "\u672c\u5730\u52a0\u5de5\u8981\u6c42",
                "state_control": "\u56fd\u5bb6\u53c2\u4e0e\u6216\u63a7\u5236",
                "tax_royalty": "\u7a0e\u8d39\u6216\u6743\u5229\u91d1",
                "environment_policy": "\u73af\u4fdd\u4e0e\u8d44\u6e90\u4fdd\u62a4",
                "investment_restriction": "\u6295\u8d44\u51c6\u5165\u9650\u5236",
                "subsidy_support": "\u653f\u7b56\u652f\u6301",
                "strategic_plan": "\u6218\u7565\u89c4\u5212",
                "permitting": "\u8bb8\u53ef\u4e0e\u5ba1\u6279",
                "recycling": "\u56de\u6536\u4e0e\u5faa\u73af",
                "unknown": "\u5176\u4ed6\u653f\u7b56",
            }
            impact_dimension_cn = {
                "resource_security": "\u8d44\u6e90\u5b89\u5168",
                "investment_access": "\u6295\u8d44\u51c6\u5165",
                "project_schedule": "\u9879\u76ee\u8fdb\u5ea6",
                "valuation_impact": "\u4f30\u503c\u5f71\u54cd",
                "procurement_cost": "\u91c7\u8d2d\u6210\u672c",
                "policy_compliance": "\u653f\u7b56\u5408\u89c4",
                "supply_stability": "\u4f9b\u5e94\u7a33\u5b9a",
            }
            st.markdown(
                f"""
                <style>
                .policy-detail-link {{
                    color:{TEXT_DARK};
                    text-decoration:none;
                    font-weight:900;
                    transition:all 0.2s ease;
                }}
                .policy-detail-link:hover {{
                    color:{timeline_catl_blue};
                    text-decoration:underline;
                    cursor:pointer;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            with st.expander(
                f"{year_value}\uff5c{lane_value}\uff1a{len(selected_df)}\u6761\u653f\u7b56\u660e\u7ec6",
                expanded=True,
            ):
                detail_columns = st.columns(2)
                for display_index, (_, row) in enumerate(selected_df.iterrows()):
                    country = str(row.get("country", "") or "Unknown")
                    policy_name = str(row.get("policy_name", "") or "\u672a\u547d\u540d\u653f\u7b56")
                    policy_type = str(row.get("policy_type", "") or "")
                    policy_type_label = policy_type_cn.get(policy_type, policy_type or "\u5176\u4ed6\u653f\u7b56")
                    risk_level = str(row.get("risk_level", "") or "")
                    impact_dimension = str(row.get("catl_risk_dimension", "") or "")
                    impact_labels = [
                        impact_dimension_cn.get(item.strip(), item.strip())
                        for item in impact_dimension.split(";")
                        if item.strip()
                    ]
                    impact_label_text = "\uff1b".join(impact_labels) if impact_labels else "\u5f85\u8bc4\u4f30"
                    timeline_context = str(row.get("timeline_context", "") or "\u653f\u7b56\u8282\u70b9")
                    source_url = str(row.get("source_url", "") or "")
                    risk_score_value = safe_num(row.get("risk_score", 0), 0)
                    timeline_year_value = str(row.get("timeline_year", "") or "")
                    detail_text = (
                        f"\u56fd\u5bb6\uff1a{country}  \n"
                        f"\u653f\u7b56\u540d\u79f0\uff1a{policy_name}  \n"
                        f"\u653f\u7b56\u7c7b\u578b\uff1a{policy_type_label}  \n"
                        f"\u751f\u6548\u5e74\u4efd\uff1a{timeline_year_value}  \n"
                        f"\u98ce\u9669\u7b49\u7ea7\uff1a{risk_level}  \n"
                        f"\u98ce\u9669\u5206\u6570\uff1a{risk_score_value:.2f}  \n"
                        f"\u5f71\u54cd\u7ef4\u5ea6\uff1a{impact_label_text}"
                    )
                    title_html = html.escape(f"{country}\uff5c{policy_name}")
                    if source_url:
                        title_html = (
                            f'<a class="policy-detail-link" href="{html.escape(source_url)}" '
                            f'target="_blank" rel="noopener noreferrer">{title_html}</a>'
                        )
                    else:
                        title_html = f'<span class="policy-detail-link">{title_html}</span>'
                    with detail_columns[display_index % 2]:
                        with st.container(border=True):
                            st.markdown(title_html, unsafe_allow_html=True)
                            st.caption(f"\u98ce\u9669\u7b49\u7ea7\uff1a{risk_level}\uff5c\u8282\u70b9\u5c5e\u6027\uff1a{timeline_context}")
                            st.caption(f"\u653f\u7b56\u7c7b\u578b\uff1a{policy_type_label}\uff5cCATL\u5f71\u54cd\u7ef4\u5ea6\uff1a{impact_label_text}")
                            st.write(detail_text if detail_text else "\u6682\u65e0\u653f\u7b56\u89e3\u91ca\u3002")
    else:
        st.caption("\u70b9\u51fb\u65f6\u95f4\u7ebf\u4e2d\u7684\u653f\u7b56\u6c14\u6ce1\uff0c\u53ef\u5728\u4e0b\u65b9\u5c55\u5f00\u8be5\u5e74\u4efd\u548c\u653f\u7b56\u6cf3\u9053\u4e0b\u7684\u653f\u7b56\u89e3\u91ca\u548c\u6765\u6e90\u94fe\u63a5\u3002\u7070\u8272\u7a7a\u5fc3\u8282\u70b9\u4e3a\u6982\u5ff5\u5360\u4f4d\uff0c\u4e0d\u4ee3\u8868\u771f\u5b9e\u653f\u7b56\u3002")

    legend_items = [
        ("#58A65A", "\u4f4e\u98ce\u9669"),
        ("#E2BE33", "\u4e2d\u98ce\u9669"),
        ("#FF6B35", "\u4e2d\u9ad8\u98ce\u9669"),
        ("#C94134", "\u9ad8/\u6781\u9ad8\u98ce\u9669"),
        ("#00AB96", "\u652f\u6301\u6027\u653f\u7b56"),
        ("#D1D5DB", "\u6982\u5ff5\u5360\u4f4d"),
        (timeline_catl_blue, "\u5e74\u4efd\u8f74 / \u5b58\u91cf\u8fb9\u6846"),
    ]
    legend_html = "".join(
        f"""
        <span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px;margin-bottom:6px;font-size:13px;font-weight:800;color:{TEXT_DARK};">
            <i style="width:12px;height:12px;border-radius:999px;background:{color};display:inline-block;border:1px solid #FFFFFF;box-shadow:0 0 0 1px #E5E7EB;"></i>{label}
        </span>
        """
        for color, label in legend_items
    )
    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:10px 12px;margin-top:8px;box-shadow:0 2px 6px #D9E2F2;">
            <b style="color:{TEXT_MUTED};font-size:13px;margin-right:10px;">\u89c6\u89c9\u7f16\u7801\uff1a</b>
            {legend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "\u6570\u636e\u6765\u6e90\uff1aIEA Critical Minerals Policy Tracker / IEA Policies Database\uff0c"
        "\u7ecf Policy Schema Engine \u4e0e Policy Scoring Engine \u6807\u51c6\u5316\u3001\u8bc4\u5206\u548c\u65f6\u95f4\u6620\u5c04\u540e\u751f\u6210\u3002"
        "\u6838\u5fc3\u9a7e\u9a76\u8231\u5c55\u793a\u771f\u5b9e\u653f\u7b56\u8282\u70b9\u53ca\u5176\u6301\u7eed\u5f71\u54cd\u5c42\uff0c\u5b8c\u6574\u653f\u7b56\u660e\u7ec6\u8bf7\u5728\u201c\u653f\u7b56\u4e0e\u65b0\u95fb\u98ce\u9669\u201d\u9875\u9762\u67e5\u770b\u3002"
    )

def get_latest_price_forecast(price_forecast_df):
    if price_forecast_df.empty:
        return {}

    row = price_forecast_df.iloc[0]

    return {
        "updated_at": row.get("updated_at", ""),
        "model_version": row.get("model_version", ""),
        "expected_lce_price": get_float(row, "expected_lce_price"),
        "lower_bound": get_float(row, "lower_bound"),
        "upper_bound": get_float(row, "upper_bound"),
        "base_forecast_price": get_float(row, "base_forecast_price"),
        "calibrated_aisc_90": get_float(row, "calibrated_aisc_90"),
        "system_aisc_90": get_float(row, "system_aisc_90"),
        "paper_base_lce_price": get_float(row, "paper_base_lce_price", 182000),
        "paper_price_lower": get_float(row, "paper_price_lower", 170000),
        "paper_price_upper": get_float(row, "paper_price_upper", 195000),
        "gfex_futures_price": get_float(row, "gfex_futures_price"),
        "crude_oil_price": get_float(row, "crude_oil_price"),
        "sc6_price_index_usd_per_tonne": get_float(row, "sc6_price_index_usd_per_tonne"),
        "sc6_price_index": get_float(row, "sc6_price_index"),
        "usd_cny": get_float(row, "usd_cny"),
        "sc6_to_lce_conversion": get_float(row, "sc6_to_lce_conversion"),
        "sc6_pass_through": get_float(row, "sc6_pass_through"),
        "base_sc6_lce_cost": get_float(row, "base_sc6_lce_cost"),
        "current_sc6_lce_cost": get_float(row, "current_sc6_lce_cost"),
        "sc6_lce_cost_change": get_float(row, "sc6_lce_cost_change"),
        "sc6_adjustment": get_float(row, "sc6_adjustment"),
        "cathode_utilization": get_float(row, "cathode_utilization"),
        "inventory_days": get_float(row, "inventory_days"),
        "supply_loss_ratio": get_float(row, "supply_loss_ratio"),
        "aisc_uplift": get_float(row, "aisc_uplift"),
        "gfex_adjustment": get_float(row, "gfex_adjustment"),
        "inventory_adjustment": get_float(row, "inventory_adjustment"),
        "utilization_adjustment": get_float(row, "utilization_adjustment"),
        "aisc_adjustment": get_float(row, "aisc_adjustment"),
        "policy_supply_premium": get_float(row, "policy_supply_premium"),
        "policy_aisc_premium": get_float(row, "policy_aisc_premium"),
        "price_zone": row.get("price_zone", ""),
        "producer_strategy": row.get("producer_strategy", ""),
        "data_quality_note": row.get("data_quality_note", ""),
    }


def render_section_04_long_term_scenario():
    section_header("03", "长期情景预测")
    section_open()

    years = list(range(2026, 2036))

    scenario_data = {
        "保守情景 STEPS": {
            "demand": [150, 170, 190, 212, 235, 245, 255, 265, 275, 285],
            "supply": [158, 177, 196, 219, 242, 252, 262, 272, 282, 292],
            "balance": [8, 7, 6, 7, 7, 7, 7, 7, 7, 7],
            "price": [12, 12, 12, 12, 12, 12, 12, 12, 12, 13],
        },
        "基准情景 APS": {
            "demand": [160, 195, 235, 280, 325, 344, 363, 382, 401, 420],
            "supply": [152, 185, 220, 248, 275, 293, 311, 329, 347, 365],
            "balance": [-8, -10, -15, -32, -50, -51, -52, -53, -54, -55],
            "price": [18, 19, 20, 21, 21, 21, 22, 22, 23, 23],
        },
        "NZE净零情景": {
            "demand": [180, 230, 285, 345, 410, 438, 466, 494, 522, 550],
            "supply": [162, 195, 230, 270, 315, 338, 361, 384, 407, 430],
            "balance": [-18, -35, -55, -75, -95, -100, -105, -110, -115, -120],
            "price": [25, 27, 28, 30, 31, 32, 32, 33, 33, 34],
        },
    }

    rows = []
    for scenario, data in scenario_data.items():
        for i, year in enumerate(years):
            balance = data["balance"][i]
            rows.append({
                "情景": scenario,
                "年份": year,
                "需求": data["demand"][i],
                "供给": data["supply"][i],
                "供需平衡": balance,
                "短缺量": max(-balance, 0),
                "盈余量": max(balance, 0),
                "价格中枢": data["price"][i],
                "状态": "盈余" if balance > 0 else "短缺",
            })

    scenario_df = pd.DataFrame(rows)

    base_2035 = scenario_df[
        (scenario_df["情景"] == "基准情景 APS") & (scenario_df["年份"] == 2035)
    ].iloc[0]

    nze_2035 = scenario_df[
        (scenario_df["情景"] == "NZE净零情景") & (scenario_df["年份"] == 2035)
    ].iloc[0]

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        compact_metric_card(
            "2035基准情景缺口",
            f"{base_2035['短缺量']:.0f} 万吨",
            "LCE，供给不足口径",
        )

    with k2:
        compact_metric_card(
            "2035 NZE缺口",
            f"{nze_2035['短缺量']:.0f} 万吨",
            "LCE，净零情景",
        )

    with k3:
        compact_metric_card(
            "2035基准需求",
            f"{base_2035['需求']:.0f} 万吨",
            "LCE，APS情景",
        )

    with k4:
        compact_metric_card(
            "2035 NZE需求",
            f"{nze_2035['需求']:.0f} 万吨",
            "LCE，极限需求情景",
        )

    st.markdown(
        """
        <div class="insight-box">
        <b>管理层结论：</b>
        2026–2028年仍处于价格与资源资产估值底部窗口。2028年后，基准情景开始出现更明显的结构性供给缺口；
        到2035年，基准情景短缺约55万吨LCE，NZE净零情景短缺约120万吨LCE。
        对买方而言，应在价格和估值尚未完全修复前，优先锁定低成本盐湖、高品位锂辉石和具备本地加工能力的资源权益。
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 三情景供需趋势与供需平衡（2026–2035）")

    fig_sd = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.09,
        row_heights=[0.66, 0.34],
        subplot_titles=(
            "需求 / 供给",
            "供需平衡",
        ),
    )

    scenario_colors = {
        "保守情景 STEPS": TEAL,
        "基准情景 APS": CATL_BLUE,
        "NZE净零情景": CORAL,
    }
    for scenario in scenario_df["情景"].unique():
        tmp = scenario_df[scenario_df["情景"] == scenario].copy()
        color = scenario_colors.get(scenario, CATL_BLUE)
        fig_sd.add_trace(
            go.Scatter(
                x=tmp["年份"],
                y=tmp["需求"],
                mode="lines+markers",
                name=f"{scenario} 需求",
                line=dict(color=color, width=3),
                hovertemplate="年份：%{x}<br>需求：%{y:.0f} 万吨LCE<extra></extra>",
            ),
            row=1,
            col=1,
        )

        fig_sd.add_trace(
            go.Scatter(
                x=tmp["年份"],
                y=tmp["供给"],
                mode="lines+markers",
                name=f"{scenario} 供给",
                line=dict(color=color, width=3, dash="dash"),
                hovertemplate="年份：%{x}<br>供给：%{y:.0f} 万吨LCE<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # =========================
    # 供需平衡叠加柱状图
    # =========================
    # 显示逻辑：
    # STEPS：绿色正值，代表盈余
    # APS：橙色负值，代表基准情景缺口
    # NZE：红色负值，代表相对 APS 进一步扩大的额外缺口
    # 因此红色不是 NZE 总缺口，而是 NZE 相比 APS 的增量缺口。
    # APS + NZE额外缺口 = NZE总缺口
    # =========================

    balance_pivot = (
        scenario_df
        .pivot(index="年份", columns="情景", values="供需平衡")
        .reset_index()
    )
    bar_width = 0.50
    balance_pivot["NZE额外缺口"] = (
        balance_pivot["NZE净零情景"] - balance_pivot["基准情景 APS"]
    )

    fig_sd.add_trace(
        go.Bar(
            x=balance_pivot["年份"],
            y=balance_pivot["保守情景 STEPS"],
            name="STEPS盈余",
            width=bar_width,
            marker=dict(
                color=TEAL_LIGHT,
                line=dict(color=TEAL, width=1),
            ),
            text=[f"{v:+.0f}" for v in balance_pivot["保守情景 STEPS"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=
                "年份：%{x}<br>"
                "STEPS供需平衡：%{y:+.0f} 万吨LCE<br>"
                "正数=盈余"
                "<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig_sd.add_trace(
        go.Bar(
            x=balance_pivot["年份"],
            y=balance_pivot["基准情景 APS"],
            name="APS缺口",
            width=bar_width,
            marker=dict(
                color=CATL_BLUE_LIGHT,
                line=dict(color=CATL_BLUE, width=1),
            ),
            text=[f"{v:+.0f}" for v in balance_pivot["基准情景 APS"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=
                "年份：%{x}<br>"
                "APS缺口：%{y:+.0f} 万吨LCE<br>"
                "负数=短缺"
                "<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig_sd.add_trace(
        go.Bar(
            x=balance_pivot["年份"],
            y=balance_pivot["NZE额外缺口"],
            name="NZE总缺口",
            width=bar_width,
            marker=dict(
                color=CORAL_LIGHT,
                line=dict(color=CORAL, width=1),
            ),
            text=[f"{v:+.0f}" for v in balance_pivot["NZE净零情景"]],
            textposition="outside",
            cliponaxis=False,
            customdata=balance_pivot["NZE净零情景"],
            hovertemplate=
                "年份：%{x}<br>"
                "NZE额外缺口：%{y:+.0f} 万吨LCE<br>"
                "NZE总缺口：%{customdata:+.0f} 万吨LCE<br>"
                "红色柱 = NZE相对APS进一步扩大的缺口"
                "<extra></extra>",
        ),
        row=2,
        col=1,
    )
    plotly_enterprise_layout(
        fig_sd,
        title=None,
        height=660,
    )

    fig_sd.update_xaxes(tickmode="array", tickvals=years, row=1, col=1)
    fig_sd.update_xaxes(title_text="年份", tickmode="array", tickvals=years, row=2, col=1)
    fig_sd.update_yaxes(title_text="需求 / 供给（万吨LCE）", row=1, col=1)
    fig_sd.update_yaxes(title_text="供需平衡（万吨LCE）", zeroline=True, zerolinecolor="#64748B", zerolinewidth=1.5, row=2, col=1)

    fig_sd.update_layout(
        barmode="relative",
        bargap=0.58,
        bargroupgap=0.12,
        hovermode="x unified",
        margin=dict(l=30, r=50, t=55, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="left",
            x=0,
            font=dict(color=TEXT_DARK, size=12),
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            borderwidth=1,
        ),
    )

    fig_sd.add_hline(
        y=0,
        line_dash="dash",
        line_color="#64748B",
        line_width=1.5,
        row=2,
        col=1,
    )

    st.caption(
        "说明：上图实线为需求，虚线为供给；下图柱状图为供需平衡。"
        "STEPS绿色正柱代表盈余；APS橙色负柱代表基准情景缺口；"
        "NZE红色负柱代表相对APS进一步扩大的额外缺口。"
        "橙色与红色叠加后的总高度，对应NZE净零情景下的总缺口。"
    )

    st.plotly_chart(fig_sd, width="stretch")

    st.markdown("#### 三情景价格中枢与战略AISC成本锚")

    price_validation_df = load_csv("policy_adjusted_price_scenarios_2026_2035.csv")
    price_plot_df = pd.DataFrame()
    scenario_name_map = {
        "STEPS": "保守情景 STEPS",
        "APS": "基准情景 APS",
        "NZE": "NZE净零情景",
        "保守情景 STEPS": "保守情景 STEPS",
        "基准情景 APS": "基准情景 APS",
        "NZE净零情景": "NZE净零情景",
    }

    if not price_validation_df.empty:
        validation_df = price_validation_df.copy()
        validation_df.columns = [str(col).strip() for col in validation_df.columns]

        if {"year", "scenario"}.issubset(validation_df.columns):
            price_value_col = next(
                (
                    col
                    for col in [
                        "policy_adjusted_price_wan",
                        "policy_adjusted_price_center_wan",
                        "price_center_wan",
                        "price_wan",
                    ]
                    if col in validation_df.columns
                ),
                None,
            )
            if price_value_col:
                validation_df["年份"] = pd.to_numeric(validation_df["year"], errors="coerce")
                validation_df["情景"] = validation_df["scenario"].astype(str).map(scenario_name_map)
                validation_df["价格中枢"] = pd.to_numeric(
                    validation_df[price_value_col],
                    errors="coerce",
                )
                price_plot_df = (
                    validation_df.dropna(subset=["年份", "情景", "价格中枢"])
                    .pivot_table(index="年份", columns="情景", values="价格中枢", aggfunc="mean")
                    .reset_index()
                )
        elif "year" in validation_df.columns:
            wide_cols = [col for col in ["STEPS", "APS", "NZE"] if col in validation_df.columns]
            if wide_cols:
                validation_df["年份"] = pd.to_numeric(validation_df["year"], errors="coerce")
                price_plot_df = validation_df[["年份"] + wide_cols].copy()
                price_plot_df = price_plot_df.rename(columns=scenario_name_map)
                for col in scenario_name_map.values():
                    if col in price_plot_df.columns:
                        price_plot_df[col] = pd.to_numeric(price_plot_df[col], errors="coerce")

    if price_validation_df.empty:
        st.info("政策调整后三情景价格数据尚未生成，暂使用页面内置价格情景。")

    if price_plot_df.empty:
        price_plot_df = (
            scenario_df
            .pivot_table(index="年份", columns="情景", values="价格中枢", aggfunc="mean")
            .reset_index()
        )

    price_plot_df = price_plot_df.sort_values("年份")

    aisc_metrics = load_aisc_dashboard_metrics()
    strategic_aisc_p90 = metric_float(aisc_metrics, "strategic_aisc_p90_wan", 0.0)
    weighted_avg_strategic_aisc = metric_float(
        aisc_metrics,
        "weighted_avg_strategic_aisc_wan",
        0.0,
    )
    current_lce_price = metric_float(aisc_metrics, "current_lce_price_wan", 18.20)

    if strategic_aisc_p90 <= 0 or weighted_avg_strategic_aisc <= 0:
        strategic_aisc_source_df = load_csv("project_strategic_aisc_v2.csv")
        if not strategic_aisc_source_df.empty and "strategic_aisc_wan" in strategic_aisc_source_df.columns:
            strategic_aisc_source_df = strategic_aisc_source_df.copy()
            strategic_aisc_source_df["strategic_aisc_wan"] = pd.to_numeric(
                strategic_aisc_source_df["strategic_aisc_wan"],
                errors="coerce",
            )
            valid_aisc_df = strategic_aisc_source_df.dropna(subset=["strategic_aisc_wan"])
            valid_aisc_df = valid_aisc_df[valid_aisc_df["strategic_aisc_wan"] > 0].copy()

            if strategic_aisc_p90 <= 0 and not valid_aisc_df.empty:
                strategic_aisc_p90 = float(valid_aisc_df["strategic_aisc_wan"].quantile(0.90))

            if weighted_avg_strategic_aisc <= 0 and not valid_aisc_df.empty:
                capacity_col = next(
                    (
                        col
                        for col in ["effective_capacity", "annual_capacity"]
                        if col in valid_aisc_df.columns
                    ),
                    None,
                )
                if capacity_col:
                    valid_aisc_df[capacity_col] = pd.to_numeric(
                        valid_aisc_df[capacity_col],
                        errors="coerce",
                    ).fillna(0)
                    capacity_sum = valid_aisc_df[capacity_col].sum()
                    if capacity_sum > 0:
                        weighted_avg_strategic_aisc = float(
                            (valid_aisc_df["strategic_aisc_wan"] * valid_aisc_df[capacity_col]).sum()
                            / capacity_sum
                        )

    if strategic_aisc_p90 <= 0:
        st.info("战略AISC样本指标尚未生成，请先运行 aisc_dashboard_metrics.py 或 aisc_policy_bridge_v2.py。")

    price_color_map = {
        "保守情景 STEPS": {
            "line": TEAL,
            "fill": TEAL_PALE,
            "width": 3,
            "legend": "STEPS价格中枢",
            "short": "STEPS",
        },
        "基准情景 APS": {
            "line": CATL_BLUE,
            "fill": CATL_BLUE_PALE,
            "width": 3.5,
            "legend": "APS价格中枢",
            "short": "APS",
        },
        "NZE净零情景": {
            "line": CORAL,
            "fill": CORAL_PALE,
            "width": 3,
            "legend": "NZE价格中枢",
            "short": "NZE",
        },
    }

    fig_price = go.Figure()

    price_scenario_order = [
        "保守情景 STEPS",
        "基准情景 APS",
        "NZE净零情景",
    ]

    price_draw_order = sorted(
        price_scenario_order,
        key=lambda item: scenario_df.loc[
            scenario_df["情景"] == item,
            "价格中枢",
        ].max(),
        reverse=True,
    )
    price_legend_rank = {
        scenario: rank
        for rank, scenario in enumerate(price_scenario_order)
    }

    for scenario in price_draw_order:
        if scenario not in price_plot_df.columns:
            continue
        tmp_price = price_plot_df[["年份", scenario]].dropna().copy()
        color_cfg = price_color_map.get(
            scenario,
            {
                "line": CATL_BLUE,
                "fill": CATL_BLUE_PALE,
                "width": 3,
                "legend": scenario,
                "short": scenario,
            },
        )
        if strategic_aisc_p90 > 0:
            tmp_price["安全垫"] = tmp_price[scenario] - strategic_aisc_p90
            tmp_price["覆盖状态"] = tmp_price["安全垫"].apply(
                lambda gap: "覆盖充分" if gap > 3 else ("边际覆盖" if gap >= 0 else "价格倒挂")
            )
        else:
            tmp_price["安全垫"] = 0.0
            tmp_price["覆盖状态"] = "待验证"

        fig_price.add_trace(
            go.Scatter(
                x=tmp_price["年份"],
                y=tmp_price[scenario],
                mode="lines+markers",
                name=color_cfg["legend"],
                legendrank=price_legend_rank.get(scenario, 99),
                line=dict(
                    color=color_cfg["line"],
                    width=color_cfg["width"],
                    shape="spline",
                ),
                marker=dict(
                    size=8,
                    color=color_cfg["line"],
                    line=dict(color="#FFFFFF", width=1.5),
                ),
                customdata=tmp_price[["安全垫", "覆盖状态"]].values,
                hovertemplate=(
                    "年份：%{x}<br>"
                    "情景：" + color_cfg["short"] + "<br>"
                    "价格中枢：%{y:.2f} 万元/吨<br>"
                    f"样本90%战略AISC：{strategic_aisc_p90:.2f} 万元/吨<br>"
                    "安全垫：%{customdata[0]:.2f} 万元/吨<br>"
                    "覆盖状态：%{customdata[1]}"
                    "<extra></extra>"
                ),
            )
        )

    price_y_values = []
    for scenario in price_scenario_order:
        if scenario in price_plot_df.columns:
            price_y_values.extend(pd.to_numeric(price_plot_df[scenario], errors="coerce").dropna().tolist())

    if price_y_values and strategic_aisc_p90 > 0:
        price_y_range = [
            max(0, min(price_y_values + [strategic_aisc_p90]) - 2),
            max(price_y_values + [strategic_aisc_p90 + 3]) + 3,
        ]
    elif price_y_values:
        price_y_range = [
            max(0, min(price_y_values) - 2),
            max(price_y_values) + 3,
        ]
    else:
        price_y_range = [0, 36]

    if strategic_aisc_p90 > 0:
        fig_price.add_hrect(
            y0=0,
            y1=strategic_aisc_p90,
            fillcolor="rgba(224, 122, 95, 0.08)",
            line_width=0,
            layer="below",
        )
        fig_price.add_hrect(
            y0=strategic_aisc_p90,
            y1=strategic_aisc_p90 + 3,
            fillcolor="rgba(226, 190, 51, 0.10)",
            line_width=0,
            layer="below",
        )

        fig_price.add_trace(
            go.Scatter(
                x=price_plot_df["年份"],
                y=[strategic_aisc_p90] * len(price_plot_df),
                mode="lines",
                name=f"样本90%战略AISC {strategic_aisc_p90:.2f}万",
                legendrank=10,
                line=dict(color="#E2BE33", width=2.5, dash="dash"),
                hovertemplate=(
                    "全球锂资源样本库战略AISC 90分位<br>"
                    "用于判断边际资源可获得成本<br>"
                    "样本90%战略AISC：%{y:.2f} 万元/吨"
                    "<extra></extra>"
                ),
            )
        )

    if weighted_avg_strategic_aisc > 0:
        fig_price.add_trace(
            go.Scatter(
                x=price_plot_df["年份"],
                y=[weighted_avg_strategic_aisc] * len(price_plot_df),
                mode="lines",
                name=f"样本加权平均战略AISC {weighted_avg_strategic_aisc:.2f}万",
                legendrank=11,
                line=dict(color="#4B5563", width=2, dash="dot"),
                opacity=0.75,
                hovertemplate="样本加权平均战略AISC：%{y:.2f} 万元/吨<extra></extra>",
            )
        )

    if strategic_aisc_p90 > 0 and not price_plot_df.empty:
        final_year = int(price_plot_df["年份"].max())
        final_cover_count = 0
        final_scenario_count = 0
        final_row = price_plot_df[price_plot_df["年份"] == final_year]
        if not final_row.empty:
            for scenario in price_scenario_order:
                if scenario in final_row.columns:
                    scenario_value = safe_num(final_row.iloc[0].get(scenario, 0), 0)
                    if scenario_value > 0:
                        final_scenario_count += 1
                        if scenario_value >= strategic_aisc_p90:
                            final_cover_count += 1
        coverage_text = (
            f"{final_year}覆盖：{final_cover_count}/{final_scenario_count}情景高于样本90%战略AISC"
            if final_scenario_count
            else "覆盖状态待更新"
        )
        fig_price.add_annotation(
            x=final_year,
            y=price_y_range[1] - max((price_y_range[1] - price_y_range[0]) * 0.08, 0.8),
            text=coverage_text,
            showarrow=False,
            xanchor="right",
            font=dict(color="#4B5563", size=13),
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            borderwidth=1,
            borderpad=6,
        )

    fig_price.update_layout(
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        font=dict(color=TEXT_DARK, size=13),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            font=dict(color=TEXT_DARK, size=13),
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            borderwidth=1,
        ),
        margin=dict(l=30, r=40, t=35, b=60),
    )

    fig_price.update_xaxes(
        title_text="年份",
        tickmode="array",
        tickvals=years,
        showgrid=False,
        color=TEXT_DARK,
        title_font=dict(color=TEXT_DARK, size=14),
    )

    fig_price.update_yaxes(
        title_text="碳酸锂价格 / 战略AISC（万元/吨 LCE）",
        range=price_y_range,
        gridcolor="#E5E7EB",
        zeroline=False,
        color=TEXT_DARK,
        title_font=dict(color=TEXT_DARK, size=14),
    )

    st.plotly_chart(fig_price, width="stretch")

    validation_caption = ""
    if strategic_aisc_p90 > 0 and not price_plot_df.empty and "基准情景 APS" in price_plot_df.columns:
        validation_df = price_plot_df[["年份", "基准情景 APS"]].dropna().copy()
        aps_2030_gap = None
        aps_2035_gap = None
        if not validation_df.empty:
            aps_2030_row = validation_df[validation_df["年份"] == 2030]
            aps_2035_row = validation_df[validation_df["年份"] == 2035]
            if not aps_2030_row.empty:
                aps_2030_gap = safe_num(aps_2030_row.iloc[0].get("基准情景 APS", 0)) - strategic_aisc_p90
            if not aps_2035_row.empty:
                aps_2035_gap = safe_num(aps_2035_row.iloc[0].get("基准情景 APS", 0)) - strategic_aisc_p90

        gap_records = []
        scenario_short_name = {
            "保守情景 STEPS": "STEPS",
            "基准情景 APS": "APS",
            "NZE净零情景": "NZE",
        }
        for scenario in price_scenario_order:
            if scenario not in price_plot_df.columns:
                continue
            for _, row in price_plot_df[["年份", scenario]].dropna().iterrows():
                price_value = safe_num(row.get(scenario, 0))
                if price_value > 0:
                    gap_records.append(
                        {
                            "scenario": scenario_short_name.get(scenario, scenario),
                            "year": int(row["年份"]),
                            "gap": price_value - strategic_aisc_p90,
                        }
                    )

        if aps_2030_gap is not None and aps_2035_gap is not None and gap_records:
            worst_record = min(gap_records, key=lambda item: item["gap"])
            validation_caption = (
                f"验证结论：APS情景下，2030年价格较样本90%战略AISC高出 {aps_2030_gap:.1f} 万元/吨，"
                f"2035年高出 {aps_2035_gap:.1f} 万元/吨；"
                f"最低安全垫出现在 {worst_record['scenario']} {worst_record['year']} 年，"
                f"为 {worst_record['gap']:.1f} 万元/吨。"
            )

    if validation_caption:
        st.caption(validation_caption)
    else:
        st.info("价格中枢验证数据不足，暂无法计算情景安全垫。")

    st.caption(
        "本图用于验证2026–2035年三情景价格中枢是否覆盖全球锂资源样本的战略AISC。"
        "战略AISC为加入运营调整与政策风险溢价后的资源可获得成本，"
        "不代表CATL已投资项目组合成本。"
    )

    with st.expander("查看2026–2035三情景预测数据"):
        st.dataframe(
            scenario_df[
                ["情景", "年份", "需求", "供给", "供需平衡", "短缺量", "盈余量", "价格中枢", "状态"]
            ],
            width="stretch",
            hide_index=True,
        )

    section_close()


# =========================
# 主程序
# =========================

def main():
    cost_df = load_csv("dynamic_cost_curve.csv")
    project_strategic_aisc_df = load_csv("project_strategic_aisc_v2.csv")
    invest_df = load_csv("investment_recommendations.csv")
    event_risk_df = load_csv("country_event_risk.csv")
    news_event_summary_df = load_csv("news_event_summary.csv")
    policy_price_df = load_csv("policy_price_impact.csv")
    critical_policy_df = load_csv("critical_minerals_policy_tracker.csv")
    policy_timeline_df = load_csv("policy_timeline_events.csv")
    price_forecast_df = load_csv("lce_price_forecast.csv")
    price_timeseries_df = load_csv("lce_price_timeseries.csv")
    weekly_inputs_df = load_csv("weekly_price_inputs.csv")
    supply_demand_df = load_csv("lce_supply_demand_forecast.csv")
    if cost_df.empty or invest_df.empty:
        st.warning("没有找到核心报告数据。请先运行：python weekly_update.py")
        return

    forecast = get_latest_price_forecast(price_forecast_df)

    expected_price = forecast.get("expected_lce_price", 0)
    lower_bound = forecast.get("lower_bound", 0)
    upper_bound = forecast.get("upper_bound", 0)
    aisc_90 = forecast.get("calibrated_aisc_90", 0)

    if aisc_90 <= 0:
        aisc_90 = forecast.get("system_aisc_90", 0)

    # =========================
    # 顶部标题
    # =========================

    updated_at = forecast.get("updated_at", "N/A") if forecast else "N/A"

    st.markdown(
        f"""
        <div class="dashboard-header">
            <div class="catl-logo">CATL 宁德时代</div>
            <div class="header-center">
                <div class="main-title">全球锂资源智能决策驾驶舱</div>
                <div class="sub-title">Global Lithium Resource Intelligent Decision Cockpit</div>
            </div>
            <div class="header-status">数据更新：{updated_at}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_nav = st.radio(
        "顶部导航",
        [
            "CATL资源事业部周报",
            "核心驾驶舱",
            "LCE走势预测",
            "全球资源地图与AISC成本",
            "政策与新闻风险",
            "Market Monitor 市场监测中心",
            "数据与模型说明",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    # =========================
    # 侧边栏筛选
    # =========================

    st.sidebar.header("筛选条件")

    if "country" in invest_df.columns:
        countries = sorted(invest_df["country"].dropna().unique().tolist())
    else:
        countries = []

    selected_countries = st.sidebar.multiselect(
        "选择国家",
        countries,
        default=countries,
    )

    if selected_countries and "country" in invest_df.columns:
        filtered_invest_df = invest_df[invest_df["country"].isin(selected_countries)].copy()
    else:
        filtered_invest_df = invest_df.copy()

    st.sidebar.markdown("---")
    st.sidebar.write("运行建议：")
    st.sidebar.code("python weekly_update.py\nstreamlit run dashboard.py")
    st.sidebar.markdown("---")
    st.sidebar.write("模型输出：")
    st.sidebar.write("- LCE价格预测")
    st.sidebar.write("- 全球矿山地图")
    st.sidebar.write("- AISC成本曲线")
    st.sidebar.write("- 投资优先级")
    st.sidebar.write("- AI按需策略")

    # =========================
    # CATL资源事业部周报
    # =========================

    def render_section_00_weekly_report():
        section_header("CATL", "\u8d44\u6e90\u6218\u7565\u60c5\u62a5\u7b80\u62a5")
        section_open()

        st.markdown(
            f"""
            <style>
            .weekly-brief-title {{
                color: #1F2D3D !important;
                font-size: 17px;
                font-weight: 600;
                line-height: 1.4;
                text-decoration: none !important;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            .weekly-brief-title:hover {{
                color: #003A8C !important;
                text-decoration: underline !important;
            }}
            .weekly-event-card {{
                width: 100%;
                background: #FFFFFF;
                border: 1px solid {BORDER};
                border-left: 5px solid {CATL_BLUE};
                border-radius: 12px;
                padding: 14px 16px;
                margin-bottom: 14px;
                box-shadow: 0 2px 8px #D9E2F2;
            }}
            .weekly-event-grid {{
                display: grid;
                grid-template-columns: minmax(0, 68%) minmax(250px, 32%);
                gap: 16px;
                align-items: stretch;
            }}
            .weekly-event-original {{
                color: {TEXT_MUTED};
                font-size: 13px;
                line-height: 1.45;
                margin-top: 5px;
            }}
            .weekly-event-meta {{
                color: {TEXT_MUTED};
                font-size: 13px;
                margin-top: 7px;
            }}
            .weekly-event-summary {{
                color: {TEXT_DARK};
                font-size: 14px;
                line-height: 1.65;
                margin-top: 10px;
            }}
            .weekly-event-side {{
                background: {CATL_BLUE_PALE};
                border: 1px solid #D8E6FA;
                border-radius: 10px;
                padding: 12px 13px;
                color: {TEXT_DARK};
                font-size: 13px;
                line-height: 1.55;
            }}
            .weekly-side-row {{
                margin-bottom: 8px;
            }}
            .weekly-side-label {{
                color: {TEXT_MUTED};
                font-weight: 800;
                margin-right: 4px;
            }}
            .weekly-score-details {{
                margin-top: 8px;
                color: {CATL_BLUE};
                font-weight: 900;
                cursor: pointer;
            }}
            .weekly-score-details summary {{
                cursor: pointer;
                outline: none;
            }}
            .weekly-score-body {{
                color: {TEXT_MUTED};
                font-weight: 600;
                margin-top: 6px;
                line-height: 1.6;
            }}
            .weekly-market-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
                margin-bottom: 12px;
            }}
            .weekly-market-card {{
                background: #FFFFFF;
                border: 1px solid {BORDER};
                border-top: 6px solid {CATL_BLUE};
                border-radius: 16px;
                padding: 18px 20px 16px 20px;
                box-shadow: 0 3px 10px #D9E2F2;
                min-height: 220px;
            }}
            .weekly-market-title {{
                color: #64748B;
                font-size: 18px;
                font-weight: 900;
                margin-bottom: 16px;
                line-height: 1.2;
            }}
            .weekly-market-status {{
                color: {CATL_BLUE};
                font-size: 15px;
                font-weight: 900;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
            }}
            .weekly-market-text {{
                color: {TEXT_DARK};
                font-size: 14px;
                line-height: 1.8;
            }}
            @media (max-width: 900px) {{
                .weekly-event-grid {{
                    grid-template-columns: 1fr;
                }}
                .weekly-market-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

        critical_events_df = load_csv("weekly_critical_events.csv")
        catl_impact_df = load_csv("weekly_catl_impact.csv")
        decision_actions_df = load_csv("weekly_decision_actions.csv")
        weekly_ai_brief_df = load_csv("weekly_ai_brief.csv")

        TXT_EMPTY = "\u6682\u65e0\u672c\u5468\u91cd\u5927\u4e8b\u4ef6\uff0c\u7b49\u5f85\u81ea\u52a8\u91c7\u96c6\u66f4\u65b0\u3002"
        TXT_VIEW = "\u67e5\u770b\u539f\u6587"
        TXT_WATCH = "\u89c2\u5bdf"
        TXT_POSITIVE = "\u6b63\u9762"
        TXT_NEGATIVE = "\u8d1f\u9762"

        def esc(value):
            if pd.isna(value):
                return ""
            return html.escape(str(value))

        def original_link(url):
            url_text = str(url or "").strip()
            if not url_text or url_text.lower() == "nan":
                return ""
            return f'<a href="{esc(url_text)}" target="_blank" style="color:{CATL_BLUE};font-weight:800;text-decoration:none;">{TXT_VIEW}</a>'

        def level_color(level):
            return {
                "P1": CATL_BLUE,
                "P2": CATL_BLUE_DARK,
                "P3": NEUTRAL,
                "Watch": NEUTRAL,
                TXT_WATCH: NEUTRAL,
            }.get(str(level), CATL_BLUE)

        def direction_label(value):
            raw = str(value or "").lower()
            if any(word in raw for word in ["positive", "\u6b63\u9762", "\u5229\u597d"]):
                return TXT_POSITIVE, IMPACT_HIGH
            return TXT_NEGATIVE, IMPACT_NEGATIVE

        def small_tag(text_value, color):
            return (
                f'<span style="display:inline-block;border:1px solid {color};background:#FFFFFF;color:{color};'
                f'border-radius:999px;padding:3px 8px;font-size:12px;font-weight:900;margin-right:6px;">{esc(text_value)}</span>'
            )

        def impact_level_color(level):
            raw = str(level or "")
            if raw == "\u9ad8":
                return IMPACT_HIGH
            if raw == "\u4e2d":
                return IMPACT_MEDIUM
            return IMPACT_LOW

        def module_title(title):
            st.markdown(
                f"""
                <div style="margin:18px 0 10px 0;padding:10px 14px;background:#FFFFFF;
                    border:1px solid {BORDER};border-left:6px solid {CATL_BLUE};border-radius:10px;
                    color:{CATL_BLUE};font-size:18px;font-weight:900;">
                    {esc(title)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        def empty_state():
            st.markdown(f'<div class="insight-box">{TXT_EMPTY}</div>', unsafe_allow_html=True)

        def trim_text(value, limit=80):
            text = str(value or "").strip()
            if not text or text.lower() == "nan":
                return ""
            return text if len(text) <= limit else text[:limit].rstrip() + "..."

        def split_numbered(value, limit=3):
            text = str(value or "").strip()
            if not text or text.lower() == "nan":
                return []
            lines = []
            for line in text.replace("\r", "").split("\n"):
                line = line.strip()
                if not line:
                    continue
                line = line.lstrip("0123456789.? ")
                if line:
                    lines.append(line)
            return lines[:limit]

        def fallback_action(event_type):
            action_map = {
                "\u4f9b\u7ed9\u6536\u7f29": "\u8bc4\u4f30\u66ff\u4ee3\u8d44\u6e90\u4e0e\u91c7\u8d2d\u5b89\u5168\u5e93\u5b58\u3002",
                "\u653f\u7b56\u6536\u7d27": "\u66f4\u65b0\u8be5\u56fd\u8d44\u6e90\u98ce\u9669\u655e\u53e3\uff0c\u6682\u505c\u65b0\u589e\u9ad8\u98ce\u9669\u9879\u76ee\u63a8\u8fdb\u3002",
                "\u653f\u7b56\u53d8\u5316": "\u8981\u6c42\u6cd5\u52a1\u548c\u8d44\u6e90\u6295\u8d44\u56e2\u961f\u590d\u6838\u9879\u76ee\u5047\u8bbe\u3002",
                "\u6295\u8d44\u4ea4\u6613": "\u8bc4\u4f30\u662f\u5426\u7eb3\u5165\u4f18\u5148\u63a5\u89e6\u6e05\u5355\u3002",
                "\u9879\u76ee\u5ba1\u6279": "\u66f4\u65b0\u9879\u76ee\u5f00\u53d1\u8fdb\u5ea6\u548c\u6295\u4ea7\u6982\u7387\u3002",
                "\u4ef7\u683c\u5f02\u5e38": "\u542f\u52a8\u4ef7\u683c\u4e0e\u91c7\u8d2d\u8282\u594f\u590d\u76d8\u3002",
            }
            return action_map.get(str(event_type), "\u6682\u65e0\u660e\u786e\u52a8\u4f5c\uff0c\u4fdd\u6301\u8ddf\u8e2a\u3002")

        def file_update_text(file_name):
            file_path = REPORTS_DIR / file_name
            if not file_path.exists():
                return "\u7b49\u5f85\u81ea\u52a8\u91c7\u96c6\u66f4\u65b0"
            try:
                return pd.Timestamp(file_path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
            except Exception:
                return "\u7b49\u5f85\u81ea\u52a8\u91c7\u96c6\u66f4\u65b0"

        def format_event_time(value):
            text = str(value or "").strip()
            if not text or text.lower() == "nan":
                return ""
            try:
                ts = pd.to_datetime(text, errors="coerce")
                if pd.isna(ts):
                    return ""
                return ts.strftime("%Y-%m-%d %H:%M")
            except Exception:
                return text

        def event_update_time(row):
            for col in [
                "updated_at",
                "update_time",
                "collected_at",
                "fetched_at",
                "ingested_at",
                "created_at",
            ]:
                display_time = format_event_time(row.get(col, ""))
                if display_time:
                    return display_time
            return file_update_text("weekly_critical_events.csv")

        def score_basis(row, impact_row):
            score = row.get("event_priority_score", "")
            event_type = row.get("event_type", "") or "\u4e8b\u4ef6"
            country = row.get("country", "")
            resource_type = row.get("resource_type", "")
            source = row.get("source", "")
            published_at = row.get("published_at", "")
            level = row.get("priority_level", "") or TXT_WATCH
            severity_text = f"\u4e8b\u4ef6\u4e25\u91cd\u5ea6\uff1a\u8be5\u4e8b\u4ef6\u5c5e\u4e8e{event_type}\uff0c\u5bf9\u8d44\u6e90\u5b89\u5168\u6216\u91c7\u8d2d\u8282\u594f\u5177\u6709\u5b9e\u8d28\u5f71\u54cd\u3002"
            relevance_bits = []
            if str(country or "").strip():
                relevance_bits.append(f"\u6d89\u53ca\u8d44\u6e90\u56fd\uff1a{country}")
            if str(resource_type or "").strip():
                relevance_bits.append(f"\u8d44\u6e90\u7c7b\u578b\uff1a{resource_type}")
            relevance_text = "\u3001".join(relevance_bits) if relevance_bits else "\u4e0e\u9502\u8d44\u6e90\u4ea7\u4e1a\u94fe\u76f8\u5173\u3002"
            source_text = f"\u6765\u6e90\u53ef\u4fe1\u5ea6\uff1a{source}\u3002" if str(source or "").strip() else "\u6765\u6e90\u53ef\u4fe1\u5ea6\uff1a\u5df2\u8fdb\u5165\u81ea\u52a8\u60c5\u62a5\u6c60\u3002"
            time_text = f"\u65f6\u6548\u6027\uff1a{published_at}\u3002" if str(published_at or "").strip() else "\u65f6\u6548\u6027\uff1a\u6309\u6700\u65b0\u91c7\u96c6\u65f6\u95f4\u8bc4\u4f30\u3002"
            score_text = f"event_priority_score\uff1a{score}\uff1b\u5f53\u524d\u7b49\u7ea7\uff1a{level}\u3002"
            return "<br>".join(
                esc(item)
                for item in [
                    severity_text,
                    f"CATL\u76f8\u5173\u6027\uff1a{relevance_text}",
                    source_text,
                    time_text,
                    score_text,
                ]
            )

        def pct_change_from_series(values):
            clean_values = []
            for value in values:
                try:
                    num = float(value)
                    if pd.notna(num):
                        clean_values.append(num)
                except Exception:
                    continue
            if len(clean_values) < 2 or clean_values[0] == 0:
                return None
            return (clean_values[-1] / clean_values[0] - 1) * 100

        def trend_status(change):
            if change is None:
                return "\u4e2d\u6027"
            if change > 3:
                return "\u504f\u5f3a"
            if change < -3:
                return "\u504f\u5f31"
            return "\u4e2d\u6027"

        def signal_tag(text_value):
            color_map = {
                "\u504f\u5f3a": IMPACT_HIGH,
                "\u504f\u5f31": IMPACT_NEGATIVE,
                "\u4e2d\u6027": IMPACT_MEDIUM,
                "\u6570\u636e\u672a\u63a5\u5165": IMPACT_LOW,
            }
            color = color_map.get(str(text_value), NEUTRAL)
            return small_tag(text_value, color)

        def fmt_pct(value):
            if value is None:
                return "\u6682\u65e0\u53ef\u6bd4\u53d8\u5316"
            sign = "+" if value > 0 else ""
            return f"{sign}{value:.1f}%"

        def get_price_validation_signal(top_df):
            gfex_change = None
            try:
                from market_data import fetch_market_monitor_data

                monitor_data = fetch_market_monitor_data()
                commodities = monitor_data.get("commodities", [])
                if commodities:
                    gfex_change = commodities[0].get("change_5d", None)
            except Exception:
                gfex_change = None

            spot_change = None
            if not price_timeseries_df.empty and "actual_lce_price" in price_timeseries_df.columns:
                ts_df = price_timeseries_df.copy()
                if "date" in ts_df.columns:
                    ts_df["date"] = pd.to_datetime(ts_df["date"], errors="coerce")
                    ts_df = ts_df.sort_values("date")
                spot_values = pd.to_numeric(ts_df["actual_lce_price"], errors="coerce").dropna().tail(2).tolist()
                spot_change = pct_change_from_series(spot_values)
            if spot_change is None:
                history_df = load_csv("lce_price_history.csv")
                if not history_df.empty and "actual_lce_price" in history_df.columns:
                    if "date" in history_df.columns:
                        history_df["date"] = pd.to_datetime(history_df["date"], errors="coerce")
                        history_df = history_df.sort_values("date")
                    spot_values = pd.to_numeric(history_df["actual_lce_price"], errors="coerce").dropna().tail(2).tolist()
                    spot_change = pct_change_from_series(spot_values)

            weekly_price_df = weekly_inputs_df.copy()
            latest_input = weekly_price_df.iloc[-1] if not weekly_price_df.empty else pd.Series(dtype="object")
            gfex_price = safe_num(latest_input.get("gfex_futures_price", 0))
            spot_price = safe_num(latest_input.get("mmlc_spot_price", 0)) or safe_num(latest_input.get("battery_lce_mid", 0))
            sc6_price = safe_num(latest_input.get("sc6_price_index_usd_per_tonne", 0)) or safe_num(latest_input.get("sc6_price_index", 0))
            sc6_change = None
            if len(weekly_price_df) >= 2:
                sc6_col = "sc6_price_index_usd_per_tonne" if "sc6_price_index_usd_per_tonne" in weekly_price_df.columns else "sc6_price_index"
                sc6_change = pct_change_from_series(pd.to_numeric(weekly_price_df[sc6_col], errors="coerce").dropna().tail(2).tolist())
            basis = gfex_price - spot_price if gfex_price and spot_price else None

            available_changes = [change for change in [gfex_change, spot_change, sc6_change] if change is not None]
            composite_change = sum(available_changes) / len(available_changes) if available_changes else None
            status = trend_status(composite_change)

            event_types = top_df.get("event_type", pd.Series(dtype=str)).astype(str).tolist()
            supply_event_hit = any(
                any(keyword in event_type for keyword in ["\u4f9b\u7ed9\u6536\u7f29", "\u505c\u4ea7", "\u51cf\u4ea7", "\u51fa\u53e3\u9650\u5236", "\u653f\u7b56\u6536\u7d27"])
                for event_type in event_types
            )
            if supply_event_hit and status == "\u504f\u5f3a":
                validation_text = "\u5df2\u9a8c\u8bc1TOP5\u4f9b\u7ed9\u6270\u52a8\u9884\u671f"
            else:
                validation_text = "\u672a\u5bf9\u91cd\u5927\u4e8b\u4ef6\u5f62\u6210\u4e00\u81f4\u9a8c\u8bc1"

            gfex_text = f"GFEX\u78b3\u9178\u9502\u672c\u5468{'\u4e0a\u6da8' if (gfex_change or 0) >= 0 else '\u4e0b\u8dcc'}{fmt_pct(abs(gfex_change) if gfex_change is not None else None)}"
            spot_text = f"\u73b0\u8d27{'\u4e0a\u6da8' if (spot_change or 0) >= 0 else '\u4e0b\u8dcc'}{fmt_pct(abs(spot_change) if spot_change is not None else None)}"
            sc6_text = f"SC6\u9502\u8f89\u77f3{'\u4e0a\u6da8' if (sc6_change or 0) >= 0 else '\u4e0b\u8dcc'}{fmt_pct(abs(sc6_change) if sc6_change is not None else None)}"
            if basis is not None:
                basis_text = f"\u671f\u8d27-\u73b0\u8d27\u4ef7\u5dee\u7ea6{basis / 10000:+.2f}\u4e07\u5143/\u5428"
            else:
                basis_text = "\u671f\u8d27-\u73b0\u8d27\u4ef7\u5dee\u6682\u65e0\u53ef\u6bd4\u6570\u636e"

            summary = f"{gfex_text}\uff0c{spot_text}\uff0c{sc6_text}\uff0c{basis_text}\u3002{validation_text}\u3002"
            return status, summary

        st.markdown(
            f"""
            <div style="color:{TEXT_MUTED};font-size:13px;margin:-6px 0 14px 2px;">
                \u66f4\u65b0\u65f6\u95f4\uff1a{file_update_text('weekly_critical_events.csv')}\uff5c
                \u6570\u636e\u6765\u6e90\uff1aRSS / Google News\uff1bMining.com\uff1b\u516c\u53f8\u516c\u544a / \u4ea4\u6613\u6240\u62ab\u9732
            </div>
            """,
            unsafe_allow_html=True,
        )

        if critical_events_df.empty:
            empty_state()
            section_close()
            return

        # TOP5：按CSV中最新事件所在自然周筛选，不再依赖历史 is_top_event 标记
        top_events_df = critical_events_df.copy()
        top_events_df["event_priority_score"] = pd.to_numeric(
            top_events_df.get("event_priority_score", 0),
            errors="coerce",
        ).fillna(0)
        top_events_df["published_at_dt"] = pd.to_datetime(
            top_events_df.get("published_at", pd.Series(dtype="object")),
            errors="coerce",
            utc=True,
        )

        valid_date_df = top_events_df.dropna(subset=["published_at_dt"]).copy()
        if valid_date_df.empty:
            top_events_df = (
                top_events_df
                .sort_values("event_priority_score", ascending=False)
                .head(5)
                .copy()
            )
        else:
            latest_event_time = valid_date_df["published_at_dt"].max()
            week_start = (latest_event_time - pd.Timedelta(days=int(latest_event_time.weekday()))).normalize()
            week_end = week_start + pd.Timedelta(days=7)
            weekly_df = valid_date_df[
                (valid_date_df["published_at_dt"] >= week_start)
                & (valid_date_df["published_at_dt"] < week_end)
            ].copy()

            if weekly_df.empty:
                weekly_df = valid_date_df[
                    valid_date_df["published_at_dt"] >= latest_event_time - pd.Timedelta(days=14)
                ].copy()

            top_events_df = (
                weekly_df
                .sort_values(["event_priority_score", "published_at_dt"], ascending=[False, False])
                .head(5)
                .copy()
            )

        if top_events_df.empty:
            empty_state()
            section_close()
            return

        impact_lookup = {}
        if not catl_impact_df.empty and "event_id" in catl_impact_df.columns:
            impact_lookup = {str(row.get("event_id", "")): row for _, row in catl_impact_df.iterrows()}

        action_lookup = {}
        if not decision_actions_df.empty and "event_id" in decision_actions_df.columns:
            for _, action_row in decision_actions_df.iterrows():
                event_id = str(action_row.get("event_id", ""))
                if event_id and event_id not in action_lookup:
                    action_lookup[event_id] = action_row

        module_title("\u672c\u5468\u91cd\u5927\u4e8b\u4ef6 TOP5")
        for _, row in top_events_df.iterrows():
            event_id = str(row.get("event_id", ""))
            impact_row = impact_lookup.get(event_id, pd.Series(dtype="object"))
            action_row = action_lookup.get(event_id, pd.Series(dtype="object"))
            level = row.get("priority_level", "") or TXT_WATCH
            color = level_color(level)
            direction, direction_color = direction_label(row.get("impact_direction", ""))
            title_cn = row.get("title_cn", "") or row.get("title", "")
            title_raw = row.get("title", "")
            source_url = str(row.get("source_url", "") or "").strip()
            link_html = original_link(source_url)
            published_time = format_event_time(row.get("published_at", "")) or "暂无发布时间"
            updated_time = event_update_time(row)
            if source_url and source_url.lower() != "nan":
                title_html = f'<a class="weekly-brief-title" href="{esc(source_url)}" target="_blank" title="{esc(title_raw)}">{esc(title_cn)}</a>'
            else:
                title_html = f'<span class="weekly-brief-title" title="{esc(title_raw)}">{esc(title_cn)}</span>'
            impact_summary = impact_row.get("impact_summary", "") if not impact_row.empty else ""
            one_line_impact = trim_text(impact_summary, 80)
            if not one_line_impact:
                one_line_impact = trim_text(row.get("summary_cn", "") or row.get("summary", ""), 80)
            if not one_line_impact:
                one_line_impact = f"{title_cn}\uff0c\u9700\u8bc4\u4f30\u5bf9\u4f9b\u5e94\u5b89\u5168\u548c\u91c7\u8d2d\u8282\u594f\u7684\u5f71\u54cd\u3002"
            event_summary = trim_text(row.get("summary_cn", "") or row.get("summary", ""), 120)
            if not event_summary:
                event_summary = one_line_impact
            action_text = action_row.get("recommended_action", "") if not action_row.empty else ""
            if not str(action_text or "").strip() or str(action_text).lower() == "nan":
                action_text = fallback_action(row.get("event_type", ""))
            impact_level = impact_row.get("impact_level", "") if not impact_row.empty else ""
            if not str(impact_level or "").strip() or str(impact_level).lower() == "nan":
                impact_level = "\u4e2d" if str(level) in ["P2", "P3"] else "\u9ad8"
            impact_color = impact_level_color(impact_level)
            score_body = score_basis(row, impact_row)
            st.markdown(
                f"""
                <div class="weekly-event-card">
                    <div class="weekly-event-grid">
                        <div>
                            <div>{title_html}</div>
                            <div class="weekly-event-original">\u539f\u6587\uff1a{esc(title_raw)}</div>
                            <div class="weekly-event-meta">{esc(row.get('source', ''))} \uff5c {link_html}</div>
                            <div class="weekly-event-meta">发布时间：{esc(published_time)} ｜ 更新时间：{esc(updated_time)}</div>
                            <div class="weekly-event-summary">{esc(event_summary)}</div>
                        </div>
                        <div class="weekly-event-side">
                            <div class="weekly-side-row">
                                <span class="weekly-side-label">\u5bf9CATL\u5f71\u54cd\uff1a</span>{small_tag(impact_level, impact_color)}
                            </div>
                            <div class="weekly-side-row">
                                <span class="weekly-side-label">\u5f71\u54cd\u65b9\u5411\uff1a</span>{small_tag(direction, direction_color)}
                            </div>
                            <div class="weekly-side-row">
                                <span class="weekly-side-label">\u5efa\u8bae\u52a8\u4f5c\uff1a</span>{esc(action_text)}
                            </div>
                            <div class="weekly-side-row">
                                <span class="weekly-side-label">\u4e8b\u4ef6\u7b49\u7ea7\uff1a</span>{small_tag(level, color)}
                            </div>
                            <details class="weekly-score-details">
                                <summary>\u8bc4\u5206\u4f9d\u636e</summary>
                                <div class="weekly-score-body">{score_body}</div>
                            </details>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        module_title("\u5e02\u573a\u9a8c\u8bc1\u4fe1\u53f7")
        price_status, price_summary = get_price_validation_signal(top_events_df)
        latest_inventory_input = weekly_inputs_df.iloc[-1] if not weekly_inputs_df.empty else pd.Series(dtype="object")
        current_inventory_days = safe_num(latest_inventory_input.get("inventory_days", 0))
        smm_inventory_tonnes = safe_num(latest_inventory_input.get("smm_inventory_tonnes", 0))
        gfex_receipts_tonnes = safe_num(latest_inventory_input.get("gfex_registered_receipts_tonnes", 0))
        gfex_inventory_change = safe_num(latest_inventory_input.get("gfex_inventory_change_tonnes", 0))
        inventory_signal = get_inventory_signal(current_inventory_days)
        inventory_status = inventory_signal.get("status", "暂无数据")

        if current_inventory_days > 0:
            inventory_status_tag = signal_tag(inventory_status)
            inventory_summary_parts = [
                f"当前碳酸锂库存天数约 {current_inventory_days:.1f} 天，处于{inventory_status}状态。"
            ]
            if smm_inventory_tonnes > 0:
                inventory_summary_parts.append(f"SMM周度库存约 {smm_inventory_tonnes:,.0f} 吨。")
            if gfex_receipts_tonnes > 0:
                inventory_summary_parts.append(f"东方财富/GFEX库存与仓单约 {gfex_receipts_tonnes:,.0f} 吨。")
            if gfex_inventory_change != 0:
                inventory_summary_parts.append(f"最新增减 {gfex_inventory_change:+,.0f} 吨。")
            inventory_summary_parts.append(
                inventory_signal.get("price_implication", "")
            )
            inventory_summary = "".join(inventory_summary_parts)
        else:
            inventory_status_tag = signal_tag("\u6570\u636e\u672a\u63a5\u5165")
            inventory_summary = "当前系统未接入库存天数数据，暂无法判断去库或累库趋势对价格的验证情况。"
        st.markdown(
            f"""
            <div class="weekly-market-grid">
                <div class="weekly-market-card">
                    <div class="weekly-market-title">\u4ef7\u683c\u4fe1\u53f7</div>
                    <div class="weekly-market-status">
                        {signal_tag(price_status)}
                    </div>
                    <div class="weekly-market-text">{esc(price_summary)}</div>
                </div>
                <div class="weekly-market-card">
                    <div class="weekly-market-title">\u5e93\u5b58\u4fe1\u53f7</div>
                    <div class="weekly-market-status">
                        {inventory_status_tag}
                    </div>
                    <div class="weekly-market-text">{esc(inventory_summary)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        module_title("\u672c\u5468AI\u7814\u5224\u4e0e\u51b3\u7b56\u5efa\u8bae")
        if weekly_ai_brief_df.empty:
            st.info("\u6682\u65e0AI\u7814\u5224\uff0c\u7b49\u5f85\u81ea\u52a8\u91c7\u96c6\u66f4\u65b0\u3002")
        else:
            brief = weekly_ai_brief_df.iloc[0]
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid {BORDER};border-left:5px solid {CATL_BLUE};border-radius:10px;padding:14px 16px;margin-bottom:12px;line-height:1.8;">
                    <div style="color:{CATL_BLUE};font-size:16px;font-weight:900;margin-bottom:6px;">\u672c\u5468\u603b\u4f53\u5224\u65ad</div>
                    <div style="color:{TEXT_DARK};font-size:14px;">{esc(brief.get('overall_judgement', ''))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            outlook_cols = st.columns(4)
            outlook_items = [
                ("\u4ef7\u683c", brief.get("price_outlook", "")),
                ("\u4f9b\u5e94", brief.get("supply_outlook", "")),
                ("\u6295\u8d44", brief.get("investment_outlook", "")),
                ("\u98ce\u9669", brief.get("risk_outlook", "")),
            ]
            for idx, (label, value) in enumerate(outlook_items):
                with outlook_cols[idx]:
                    st.markdown(
                        f"""
                        <div style="background:#FFFFFF;border:1px solid {BORDER};border-radius:10px;padding:12px 13px;margin-bottom:10px;">
                            <div style="color:{TEXT_MUTED};font-size:13px;font-weight:800;">{label}</div>
                            <div style="color:{CATL_BLUE};font-size:19px;font-weight:900;margin-top:4px;">{esc(value)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            action_items = split_numbered(brief.get("recommended_actions", ""), 3)
            watch_items = split_numbered(brief.get("watch_items", ""), 3)
            ai_col_1, ai_col_2 = st.columns(2)
            with ai_col_1:
                st.markdown(f"<div class='strategy-box'><b>AI\u5efa\u8bae\u52a8\u4f5c</b><br>{'<br>'.join(esc(item) for item in action_items)}</div>", unsafe_allow_html=True)
            with ai_col_2:
                st.markdown(f"<div class='strategy-box'><b>\u7ee7\u7eed\u8ddf\u8e2a</b><br>{'<br>'.join(esc(item) for item in watch_items)}</div>", unsafe_allow_html=True)

        module_title("\u6570\u636e\u6765\u6e90\u4e0e\u66f4\u65b0\u65f6\u95f4")
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid {BORDER};border-radius:10px;padding:14px 16px;color:{TEXT_DARK};font-size:14px;line-height:1.8;">
                <b>\u6570\u636e\u6765\u6e90\uff1a</b> RSS / Google News\uff1bMining.com\uff1b\u516c\u53f8\u516c\u544a / \u4ea4\u6613\u6240\u62ab\u9732\uff1bSMM / Fastmarkets / Benchmark\uff08\u5982\u672a\u6765\u63a5\u5165\uff09<br>
                raw_news_events.csv\uff1a{file_update_text('raw_news_events.csv')}<br>
                raw_disclosure_events.csv\uff1a{file_update_text('raw_disclosure_events.csv')}<br>
                weekly_critical_events.csv\uff1a{file_update_text('weekly_critical_events.csv')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        section_close()

    def render_section_01_command_center():
        section_header("01", "核心驾驶舱")
        section_open()

        # Decision Cockpit v3: keep the first screen focused on one decision,
        # four signals, and one portfolio matrix. Data/model logic stays upstream.
        aisc_metrics = load_aisc_dashboard_metrics()
        investment_rebalance_df = load_csv("investment_recommendations_v2.csv")
        document_market_inputs_df = load_csv("document_market_inputs.csv")
        weekly_market_signals_df = load_csv("weekly_market_signals.csv")

        def dashboard_file_status(file_name):
            file_path = REPORTS_DIR / file_name
            if not file_path.exists():
                return "等待自动采集更新"
            try:
                return pd.Timestamp(file_path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
            except Exception:
                return "等待自动采集更新"

        def latest_data_update(df_source, file_name):
            if df_source is not None and not df_source.empty and "updated_at" in df_source.columns:
                updated_at = str(df_source.iloc[-1].get("updated_at", "") or "").strip()
                if updated_at and updated_at.lower() != "nan":
                    return updated_at[:16]
            return dashboard_file_status(file_name)

        def clean_text(value, default="N/A"):
            text = str(value or "").strip()
            if not text or text.lower() == "nan":
                return default
            return text

        strategic_aisc_p90 = metric_float(aisc_metrics, "strategic_aisc_p90_wan", 0.0)
        current_lce_price_wan = metric_float(aisc_metrics, "current_lce_price_wan", 18.20)
        high_policy_premium_count = metric_float(aisc_metrics, "high_policy_premium_project_count", 0.0)
        project_count = metric_float(aisc_metrics, "project_count", 0.0)
        high_policy_premium_ratio = metric_float(aisc_metrics, "high_policy_premium_project_ratio", 0.0)
        strategic_aisc_below_price_ratio = metric_float(aisc_metrics, "strategic_aisc_below_price_ratio", 0.0)

        cost_pressure = 0.0
        if current_lce_price_wan > 0 and strategic_aisc_p90 > 0:
            cost_pressure = max(0.0, min(strategic_aisc_p90 / current_lce_price_wan, 1.0))

        if high_policy_premium_ratio > 0:
            policy_constraint = max(0.0, min(high_policy_premium_ratio, 1.0))
        elif project_count > 0:
            policy_constraint = max(0.0, min(high_policy_premium_count / project_count, 1.0))
        else:
            policy_constraint = 0.0

        supply_strength = max(0.0, min(strategic_aisc_below_price_ratio, 1.0))
        if supply_strength <= 0 and not investment_rebalance_df.empty and "strategic_aisc_wan" in investment_rebalance_df.columns:
            strategic_aisc_series = pd.to_numeric(investment_rebalance_df["strategic_aisc_wan"], errors="coerce")
            strategic_aisc_series = strategic_aisc_series.dropna()
            if len(strategic_aisc_series) > 0 and current_lce_price_wan > 0:
                supply_strength = float((strategic_aisc_series <= current_lce_price_wan).mean())
                supply_strength = max(0.0, min(supply_strength, 1.0))

        supply_tightness = max(0.0, min(1.0 - supply_strength, 1.0))
        rpi_score = (0.40 * cost_pressure + 0.35 * policy_constraint + 0.25 * supply_tightness) * 100
        rpi_score = max(0.0, min(rpi_score, 100.0))

        df = pd.DataFrame({"RPI": [rpi_score]})
        rpi = df["RPI"].iloc[-1]
        cost_gap = current_lce_price_wan - strategic_aisc_p90

        market_input_df = document_market_inputs_df if not document_market_inputs_df.empty else weekly_inputs_df
        latest_market_input = market_input_df.iloc[-1] if not market_input_df.empty else pd.Series(dtype="object")
        inventory_days = safe_num(latest_market_input.get("inventory_days", 0))
        gfex_change = safe_num(latest_market_input.get("gfex_inventory_change_tonnes", 0))
        spot_price_wan = safe_num(latest_market_input.get("mmlc_spot_price", 0)) / 10000
        if spot_price_wan > 0:
            current_lce_price_wan = spot_price_wan
            cost_gap = current_lce_price_wan - strategic_aisc_p90

        if not weekly_market_signals_df.empty:
            latest_market_signal = weekly_market_signals_df.iloc[-1]
            price_signal = clean_text(
                latest_market_signal.get("price_signal", "")
                or latest_market_signal.get("market_validation_status", "")
                or latest_market_signal.get("status", ""),
                "验证中",
            )
        elif cost_gap >= 1.0 and inventory_days > 0 and inventory_days <= 25:
            price_signal = "偏强验证"
        elif cost_gap < 0 or inventory_days >= 30 or gfex_change >= 1000:
            price_signal = "偏弱验证"
        else:
            price_signal = "验证中"

        if supply_tightness >= 0.55:
            supply_signal = "Tight"
        elif supply_tightness >= 0.30:
            supply_signal = "Balanced"
        else:
            supply_signal = "Loose"

        if rpi >= 70:
            decision = "防御观察（Underweight）"
            decision_class = "defensive"
            decision_action = "降低高成本、高政策风险新增暴露，优先保留现金流和锁量弹性。"
        elif rpi >= 40:
            decision = "谨慎布局（Neutral）"
            decision_class = "neutral"
            decision_action = "当前不是全面扩张窗口，也不是防御收缩窗口。价格仍覆盖AISC90，但政策约束偏高，因此只推进低成本、低政策风险、可形成长期锁量能力的项目。"
        else:
            decision = "精选锁量（Overweight）"
            decision_class = "overweight"
            decision_action = "优先锁定低AISC、低政策风险且可形成长期供应弹性的资源。"

        if cost_gap >= 1:
            cost_gap_label = f"+{cost_gap:.1f} 万元/吨"
        else:
            cost_gap_label = f"{cost_gap:.1f} 万元/吨"

        matrix_source_df = investment_rebalance_df.copy() if not investment_rebalance_df.empty else project_strategic_aisc_df.copy()
        matrix_source_name = "investment_recommendations_v2.csv" if not investment_rebalance_df.empty else "project_strategic_aisc_v2.csv"
        matrix_plot_df = pd.DataFrame()

        if not matrix_source_df.empty:
            matrix_df = matrix_source_df.copy()
            if "project_name" not in matrix_df.columns:
                for candidate_col in ["project", "name", "asset_name", "mine_name"]:
                    if candidate_col in matrix_df.columns:
                        matrix_df["project_name"] = matrix_df[candidate_col]
                        break
            if "project_name" not in matrix_df.columns:
                matrix_df["project_name"] = "N/A"
            if "lce_capacity" not in matrix_df.columns:
                for capacity_col in ["effective_capacity", "annual_capacity"]:
                    if capacity_col in matrix_df.columns:
                        matrix_df["lce_capacity"] = matrix_df[capacity_col]
                        break
            if "lce_capacity" not in matrix_df.columns:
                matrix_df["lce_capacity"] = 0
            if "strategic_aisc_wan" not in matrix_df.columns:
                for aisc_col in ["adjusted_aisc_wan", "base_aisc_wan"]:
                    if aisc_col in matrix_df.columns:
                        matrix_df["strategic_aisc_wan"] = matrix_df[aisc_col]
                        break
            if "strategic_aisc_wan" not in matrix_df.columns and "adjusted_aisc" in matrix_df.columns:
                matrix_df["strategic_aisc_wan"] = pd.to_numeric(matrix_df["adjusted_aisc"], errors="coerce") / 10000
            if "policy_risk_score_norm" not in matrix_df.columns:
                risk_candidates = [col for col in ["policy_risk_score", "risk_score", "event_risk_score", "country_risk_score"] if col in matrix_df.columns]
                if risk_candidates:
                    matrix_df["policy_risk_score_norm"] = matrix_df[risk_candidates].apply(pd.to_numeric, errors="coerce").max(axis=1)
            if "policy_risk_score_norm" not in matrix_df.columns:
                matrix_df["policy_risk_score_norm"] = 0
            if "strategic_aisc_percentile" not in matrix_df.columns and "strategic_aisc_wan" in matrix_df.columns:
                matrix_df["strategic_aisc_percentile"] = pd.to_numeric(matrix_df["strategic_aisc_wan"], errors="coerce").rank(pct=True)
            if "investment_tier" not in matrix_df.columns:
                matrix_df["investment_tier"] = "Tier 3｜观察储备"
            if "country" not in matrix_df.columns:
                matrix_df["country"] = "N/A"
            if "resource_type" not in matrix_df.columns:
                matrix_df["resource_type"] = "N/A"

            for col in ["lce_capacity", "strategic_aisc_wan", "policy_risk_score_norm", "strategic_aisc_percentile"]:
                matrix_df[col] = pd.to_numeric(matrix_df[col], errors="coerce")

            required_cols = ["project_name", "strategic_aisc_percentile", "policy_risk_score_norm", "strategic_aisc_wan", "lce_capacity"]
            matrix_plot_df = matrix_df.dropna(subset=required_cols).copy()
            matrix_plot_df = matrix_plot_df[matrix_plot_df["strategic_aisc_wan"] > 0].copy()
            matrix_plot_df["strategic_aisc_percentile"] = matrix_plot_df["strategic_aisc_percentile"].clip(0, 1)
            matrix_plot_df["policy_risk_score_norm"] = matrix_plot_df["policy_risk_score_norm"].clip(0, 1)
            matrix_plot_df["lce_capacity"] = matrix_plot_df["lce_capacity"].fillna(0).clip(lower=0)

        tier12_ratio = 0.0
        if not matrix_plot_df.empty and "investment_tier" in matrix_plot_df.columns:
            tier_text = matrix_plot_df["investment_tier"].astype(str)
            tier12_ratio = float(tier_text.str.contains("Tier 1|Tier 2", regex=True, na=False).mean())

        st.markdown(
            f"""
            <style>
            div[data-testid="stMetric"] {{
                min-height:96px;
                padding:12px 14px;
            }}
            div[data-testid="stMetricValue"] {{
                font-size:var(--font-kpi-md);
                line-height:var(--line-tight);
            }}
            div[data-testid="stMetricLabel"] {{
                font-size:var(--font-caption);
            }}
            .decision-v3-hero {{
                background:linear-gradient(135deg, #FFFFFF 0%, #F3F7FF 58%, #EAF7F7 100%);
                border:1px solid #D9E2F2;
                border-left:8px solid {CATL_BLUE};
                border-radius:16px;
                padding:20px 22px;
                box-shadow:0 4px 14px rgba(0, 58, 140, 0.10);
                margin-bottom:16px;
            }}
            .decision-v3-title {{
                color:{CATL_BLUE};
                font-size:28px;
                font-weight:900;
                line-height:1.2;
                margin-bottom:8px;
            }}
            .decision-v3-main {{
                font-size:30px;
                font-weight:900;
                color:{TEXT_DARK};
                line-height:1.25;
                margin-bottom:8px;
            }}
            .decision-v3-action {{
                color:{TEXT_DARK};
                font-size:16px;
                line-height:1.65;
                margin-bottom:8px;
            }}
            .decision-v3-basis {{
                display:inline-flex;
                align-items:center;
                border:1px solid #D9E2F2;
                border-radius:999px;
                padding:6px 12px;
                color:{TEXT_MUTED};
                background:#FFFFFF;
                font-size:13px;
                font-weight:800;
            }}
            .decision-v3-section {{
                color:{CATL_BLUE};
                font-size:22px;
                font-weight:900;
                margin:18px 0 10px 0;
                display:flex;
                align-items:center;
                gap:9px;
            }}
            .decision-v3-section span {{
                display:inline-block;
                width:7px;
                height:22px;
                border-radius:99px;
                background:{CATL_BLUE};
            }}
            .decision-v3-note {{
                background:#FFFFFF;
                border:1px solid #E5E7EB;
                border-left:5px solid {CATL_BLUE};
                border-radius:12px;
                padding:14px 16px;
                color:{TEXT_DARK};
                line-height:1.6;
                box-shadow:0 2px 8px rgba(0, 58, 140, 0.06);
            }}
            .decision-v3-update-card {{
                background:#FFFFFF;
                border:1px solid #D9E2F2;
                border-left:7px solid {CATL_BLUE};
                border-radius:12px;
                padding:18px 20px;
                color:{TEXT_DARK};
                line-height:1.8;
                font-size:16px;
                box-shadow:0 2px 8px rgba(0, 58, 140, 0.06);
                margin-top:10px;
            }}
            .decision-v3-update-card b {{
                color:{TEXT_DARK};
                font-weight:900;
            }}
            .decision-v3-explain-grid {{
                display:grid;
                grid-template-columns:repeat(4, minmax(180px, 1fr));
                gap:12px;
                margin:10px 0 14px 0;
            }}
            .decision-v3-explain-card {{
                background:#FFFFFF;
                border:1px solid #E5E7EB;
                border-top:4px solid {CATL_BLUE};
                border-radius:12px;
                padding:13px 14px;
                min-height:136px;
                box-shadow:0 2px 8px rgba(0, 58, 140, 0.06);
            }}
            .decision-v3-explain-title {{
                color:{CATL_BLUE};
                font-size:15px;
                font-weight:900;
                margin-bottom:7px;
            }}
            .decision-v3-explain-body {{
                color:{TEXT_DARK};
                font-size:13px;
                line-height:1.55;
            }}
            .decision-v3-explain-foot {{
                color:{TEXT_MUTED};
                font-size:12px;
                line-height:1.35;
                margin-top:7px;
            }}
            @media (max-width: 1200px) {{
                .decision-v3-explain-grid {{
                    grid-template-columns:repeat(2, minmax(0, 1fr));
                }}
            }}
            @media (max-width: 760px) {{
                .decision-v3-explain-grid {{
                    grid-template-columns:1fr;
                }}
            }}
            </style>
            <div class="decision-v3-hero">
                <div class="decision-v3-title">资源配置决策</div>
                <div class="decision-v3-main">{decision}</div>
                <div class="decision-v3-action">{decision_action}</div>
                <div class="decision-v3-basis">决策依据：RPI + 价格信号 + 成本压力 + 供给状态</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sig1, sig2, sig3, sig4 = st.columns(4)
        with sig1:
            st.metric("RPI资源压力", f"{rpi:.0f}")
        with sig2:
            st.metric("价格信号", price_signal)
        with sig3:
            st.metric("成本压力", cost_gap_label)
        with sig4:
            st.metric("供给状态", supply_signal)

        st.markdown(
            f"""
            <div class="decision-v3-section"><span></span>信号解读｜How to Read</div>
            <div class="decision-v3-explain-grid">
                <div class="decision-v3-explain-card">
                    <div class="decision-v3-explain-title">RPI资源压力</div>
                    <div class="decision-v3-explain-body">公式：40% 成本压力 + 35% 政策约束 + 25% 供给紧张度。当前RPI为 <b>{rpi:.0f}</b>，用于判断资源配置应扩张、谨慎或防御。</div>
                    <div class="decision-v3-explain-foot">区间：低于40精选锁量；40-70谨慎布局；70以上防御观察。</div>
                </div>
                <div class="decision-v3-explain-card">
                    <div class="decision-v3-explain-title">价格信号</div>
                    <div class="decision-v3-explain-body">由价格安全垫、库存天数和GFEX仓单增减共同验证。当前判断为 <b>{price_signal}</b>。</div>
                    <div class="decision-v3-explain-foot">库存天数约{inventory_days:.1f}天，仓单增减{gfex_change:+,.0f}吨。</div>
                </div>
                <div class="decision-v3-explain-card">
                    <div class="decision-v3-explain-title">成本压力</div>
                    <div class="decision-v3-explain-body">口径：当前LCE价格 - AISC90。当前安全垫为 <b>{cost_gap_label}</b>。</div>
                    <div class="decision-v3-explain-foot">正值代表价格覆盖边际成本；负值代表成本倒挂风险。</div>
                </div>
                <div class="decision-v3-explain-card">
                    <div class="decision-v3-explain-title">供给状态</div>
                    <div class="decision-v3-explain-body">口径：Supply Tightness = 1 - Supply Strength。当前供给状态为 <b>{supply_signal}</b>。</div>
                    <div class="decision-v3-explain-foot">Tight偏紧，Balanced均衡，Loose表示当前价格覆盖样本比例较高。</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="decision-v3-section"><span></span>资源配置状态｜Portfolio Health</div>', unsafe_allow_html=True)
        matrix_col, side_col = st.columns([1.65, 0.75])
        with matrix_col:
            if matrix_plot_df.empty:
                st.info("资源配置矩阵缺少有效的AISC、政策风险或产能字段，等待数据更新。")
            else:
                max_capacity = matrix_plot_df["lce_capacity"].max()
                if max_capacity > 0:
                    matrix_plot_df["bubble_size"] = (matrix_plot_df["lce_capacity"] / max_capacity * 42).fillna(12).clip(lower=10)
                else:
                    matrix_plot_df["bubble_size"] = 12

                def tier_key(value):
                    value_text = str(value)
                    if "Tier 1" in value_text:
                        return "Tier 1"
                    if "Tier 2" in value_text:
                        return "Tier 2"
                    if "Tier 4" in value_text:
                        return "Tier 4"
                    return "Tier 3"

                matrix_plot_df["tier_key"] = matrix_plot_df["investment_tier"].apply(tier_key)
                tier_colors = {"Tier 1": "#00AB96", "Tier 2": "#1677FF", "Tier 3": "#E2BE33", "Tier 4": "#C94134"}
                fig_matrix = go.Figure()
                fig_matrix.add_shape(type="rect", x0=0, x1=0.5, y0=0, y1=0.5, fillcolor="rgba(0, 171, 150, 0.08)", line_width=0, layer="below")
                fig_matrix.add_shape(type="rect", x0=0.5, x1=1, y0=0, y1=0.5, fillcolor="rgba(22, 119, 255, 0.07)", line_width=0, layer="below")
                fig_matrix.add_shape(type="rect", x0=0, x1=0.5, y0=0.5, y1=1, fillcolor="rgba(226, 190, 51, 0.10)", line_width=0, layer="below")
                fig_matrix.add_shape(type="rect", x0=0.5, x1=1, y0=0.5, y1=1, fillcolor="rgba(201, 65, 52, 0.08)", line_width=0, layer="below")
                fig_matrix.add_hline(y=0.5, line_dash="dot", line_color="#94A3B8")
                fig_matrix.add_vline(x=0.5, line_dash="dot", line_color="#94A3B8")

                for tier_name, color in tier_colors.items():
                    tier_df = matrix_plot_df[matrix_plot_df["tier_key"] == tier_name]
                    if tier_df.empty:
                        continue
                    fig_matrix.add_trace(
                        go.Scatter(
                            x=tier_df["strategic_aisc_percentile"],
                            y=tier_df["policy_risk_score_norm"],
                            mode="markers",
                            name=tier_name,
                            marker=dict(size=tier_df["bubble_size"], color=color, opacity=0.78, line=dict(width=1, color="#FFFFFF")),
                            customdata=tier_df[["project_name", "country", "resource_type", "strategic_aisc_wan", "lce_capacity", "investment_tier"]],
                            hovertemplate="项目：%{customdata[0]}<br>国家：%{customdata[1]}<br>资源：%{customdata[2]}<br>战略AISC：%{customdata[3]:.2f}万元/吨<br>产能：%{customdata[4]:,.0f}吨<br>分级：%{customdata[5]}<extra></extra>",
                        )
                    )

                fig_matrix.update_layout(
                    height=460,
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                )
                fig_matrix.update_xaxes(title="战略AISC成本分位", range=[0, 1], tickformat=".0%", gridcolor="#E5E7EB")
                fig_matrix.update_yaxes(title="政策约束强度", range=[0, 1], tickformat=".0%", gridcolor="#E5E7EB")
                st.plotly_chart(fig_matrix, width="stretch")

        with side_col:
            st.markdown(
                f"""
                <div class="decision-v3-note">
                <b>矩阵读法</b><br>
                左下象限为优先配置区；右上象限为防御观察区。<br><br>
                Tier 1+2 样本占比：<b>{tier12_ratio * 100:.0f}%</b><br>
                数据源：{matrix_source_name}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("IEA全球关键矿产政策风险（2025–2035）"):
            lane_order_for_summary = [
                "出口限制与本地加工",
                "国家控股与国家参与",
                "税费权利金与许可约束",
                "环保保护与水资源约束",
                "政策支持与供应稳定",
                "战略规划与产业支持",
                "回收与循环体系",
                "其他政策约束",
            ]
            if policy_timeline_df.empty:
                st.info("政策时间线数据尚未生成，无法按统一泳道口径统计原始政策条数。")
            else:
                timeline_summary_df = policy_timeline_df.copy()
                timeline_summary_df["timeline_year"] = pd.to_numeric(
                    timeline_summary_df.get("timeline_year", pd.Series(dtype=float)),
                    errors="coerce",
                )
                timeline_summary_df = timeline_summary_df[
                    timeline_summary_df["timeline_year"].between(2025, 2035, inclusive="both")
                ].copy()
                timeline_summary_df["timeline_lane"] = timeline_summary_df.get(
                    "timeline_lane",
                    pd.Series("其他政策约束", index=timeline_summary_df.index),
                ).fillna("其他政策约束")
                lane_counts = timeline_summary_df["timeline_lane"].value_counts().to_dict()
                lane_cols = st.columns(4)
                for idx, lane_name in enumerate(lane_order_for_summary):
                    with lane_cols[idx % 4]:
                        st.write(f"{lane_name}：{int(lane_counts.get(lane_name, 0))} 条原始政策")
                st.caption("统计口径：policy_timeline_events.csv 的 timeline_lane 原始政策条数，不包含2027/2030/2035持续影响投影节点。")

        st.markdown('<div class="decision-v3-section"><span></span>长期政策演化（2025–2035）</div>', unsafe_allow_html=True)
        render_policy_timeline_chart(policy_timeline_df)

        st.markdown(
            f"""
            <div class="decision-v3-section"><span></span>数据来源与更新时间</div>
            <div class="decision-v3-update-card">
                <b>数据来源：</b> GFEX / 东方财富；五矿期货周报；IEA政策追踪；全球锂资源样本库<br>
                lce_price_forecast.csv：{dashboard_file_status('lce_price_forecast.csv')}<br>
                document_market_inputs.csv：{dashboard_file_status('document_market_inputs.csv')}<br>
                lce_supply_demand_forecast.csv：{dashboard_file_status('lce_supply_demand_forecast.csv')}<br>
                {matrix_source_name}：{dashboard_file_status(matrix_source_name)}<br>
                policy_timeline_events.csv：{dashboard_file_status('policy_timeline_events.csv')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        section_close()
        return
    # =========================
    # 02 LCE价格预测与生产者策略
    # =========================

    def render_section_02_price_forecast():
        section_header("01", "LCE走势预测")
        section_open()
    
        if price_forecast_df.empty:
            st.warning("暂无 lce_price_forecast.csv。请先运行：python weekly_update.py")
        else:
            updated_at = forecast.get("updated_at", "")
            price_zone = forecast.get("price_zone", "")
            producer_strategy = forecast.get("producer_strategy", "")
    
            if expected_price > 0 and lower_bound > 0 and upper_bound > 0:
                insight_text = (
                    f"未来6个月LCE价格预计运行在 "
                    f"<b>{lower_bound / 10000:.2f}–{upper_bound / 10000:.2f} 万元/吨</b> 区间，"
                    f"中枢约 <b>{expected_price / 10000:.2f} 万元/吨</b>。"
                    f"当前模型阶段判断为：<b>{price_zone}</b>。"
                )
            else:
                insight_text = "当前价格预测数据不完整，请先运行 weekly_update.py。"
    
            st.markdown(
                f"""
                <div class="insight-box">
                <b>系统结论：</b>{insight_text}
                <br>
                当前价格判断采用“成本支撑 + 需求强度 + 库存周期 + 期货预期 + 政策扰动”的综合框架。
                其中 SC6 锂精矿价格决定上游成本传导，正极开工率反映需求强度，
                库存天数用于捕捉短周期去库/累库信号，决策锚 19.5 构成管理层价格判断参考线，
                GFEX 期货价格用于反映市场预期。
                </div>
                """,
                unsafe_allow_html=True,
            )
    
            st.caption(
                f"最近更新时间：{updated_at if updated_at else 'N/A'} ｜ "
                f"模型版本：{forecast.get('model_version', 'N/A')}"
            )
    
            chart_col, strategy_col = st.columns([2.2, 1])
    
            with chart_col:
                st.markdown("#### LCE现货价格走势与未来半年预测")
    
                if price_timeseries_df.empty:
                    st.info("暂无 lce_price_timeseries.csv。请先运行：python price_timeseries.py")
                else:
                    ts_df = price_timeseries_df.copy()
                    ts_df["date"] = pd.to_datetime(ts_df["date"], errors="coerce")
                    ts_df = ts_df.dropna(subset=["date"]).copy()
                    ts_df = ts_df[
                        ts_df["date"].between(
                            pd.Timestamp("2026-01-01"),
                            pd.Timestamp("2027-01-01"),
                            inclusive="both",
                        )
                    ].copy()
    
                    for col in [
                        "actual_lce_price",
                        "forecast_center",
                        "forecast_lower",
                        "forecast_upper",
                    ]:
                        if col in ts_df.columns:
                            ts_df[col] = pd.to_numeric(
                                ts_df[col],
                                errors="coerce"
                            ) / 10000
                    # 预测曲线显示模型真实输出；17.0、18.2、19.5只作为决策参考锚，不再裁剪预测值。
                    actual_plot_df = ts_df.dropna(subset=["actual_lce_price"]).copy() if "actual_lce_price" in ts_df.columns else pd.DataFrame()
                    forecast_plot_df = ts_df[
                        ts_df[["forecast_center", "forecast_lower", "forecast_upper"]]
                        .notna()
                        .any(axis=1)
                    ].copy() if all(col in ts_df.columns for col in ["forecast_center", "forecast_lower", "forecast_upper"]) else pd.DataFrame()

                    has_forecast_band_correction = False
                    if not forecast_plot_df.empty:
                        forecast_plot_df["forecast_upper_display"] = forecast_plot_df["forecast_upper"]
                        forecast_plot_df["forecast_lower_display"] = forecast_plot_df["forecast_lower"]
                        forecast_plot_df["center_above_upper_mask"] = (
                            forecast_plot_df["forecast_center"].notna()
                            & forecast_plot_df["forecast_upper"].notna()
                            & (forecast_plot_df["forecast_center"] > forecast_plot_df["forecast_upper"])
                        )
                        forecast_plot_df["center_below_lower_mask"] = (
                            forecast_plot_df["forecast_center"].notna()
                            & forecast_plot_df["forecast_lower"].notna()
                            & (forecast_plot_df["forecast_center"] < forecast_plot_df["forecast_lower"])
                        )
                        forecast_plot_df["upper_correction_note"] = forecast_plot_df["center_above_upper_mask"].map(
                            lambda value: "<br>说明：展示已校正" if value else ""
                        )
                        forecast_plot_df["lower_correction_note"] = forecast_plot_df["center_below_lower_mask"].map(
                            lambda value: "<br>说明：展示已校正" if value else ""
                        )
                        forecast_plot_df.loc[
                            forecast_plot_df["center_above_upper_mask"],
                            "forecast_upper_display",
                        ] = forecast_plot_df.loc[
                            forecast_plot_df["center_above_upper_mask"],
                            "forecast_center",
                        ]
                        forecast_plot_df.loc[
                            forecast_plot_df["center_below_lower_mask"],
                            "forecast_lower_display",
                        ] = forecast_plot_df.loc[
                            forecast_plot_df["center_below_lower_mask"],
                            "forecast_center",
                        ]
                        has_forecast_band_correction = bool(
                            forecast_plot_df["center_above_upper_mask"].any()
                            or forecast_plot_df["center_below_lower_mask"].any()
                        )

                    if not actual_plot_df.empty and not forecast_plot_df.empty:
                        last_actual = actual_plot_df.sort_values("date").iloc[-1]
                        first_forecast_date = forecast_plot_df["date"].min()
                        if last_actual["date"] < first_forecast_date:
                            bridge_row = {
                                "date": last_actual["date"],
                                "forecast_center": last_actual["actual_lce_price"],
                                "forecast_lower": max(PAPER_PRICE_LOW_WAN, last_actual["actual_lce_price"] - 0.30),
                                "forecast_upper": last_actual["actual_lce_price"] + 0.30,
                                "forecast_lower_display": max(PAPER_PRICE_LOW_WAN, last_actual["actual_lce_price"] - 0.30),
                                "forecast_upper_display": last_actual["actual_lce_price"] + 0.30,
                                "center_above_upper_mask": False,
                                "center_below_lower_mask": False,
                            }
                            forecast_plot_df = pd.concat(
                                [pd.DataFrame([bridge_row]), forecast_plot_df],
                                ignore_index=True,
                            ).sort_values("date")
                    fig_ts = go.Figure()

                    stage_bands = [
                        (
                            pd.Timestamp("2026-01-01"),
                            pd.Timestamp("2026-07-01"),
                            "2026H1：库存压制期",
                            "rgba(148, 163, 184, 0.07)",
                        ),
                        (
                            pd.Timestamp("2026-07-01"),
                            pd.Timestamp("2027-01-01"),
                            "2026H2：去库 + 反弹",
                            "rgba(22, 119, 255, 0.06)",
                        ),
                    ]
                    for x0, x1, label, fill_color in stage_bands:
                        fig_ts.add_vrect(
                            x0=x0,
                            x1=x1,
                            fillcolor=fill_color,
                            line_width=0,
                            layer="below",
                        )
                        fig_ts.add_annotation(
                            x=x0 + (x1 - x0) / 2,
                            y=1.03,
                            xref="x",
                            yref="paper",
                            text=label,
                            showarrow=False,
                            font=dict(color="#475569", size=12),
                            bgcolor="rgba(255,255,255,0.78)",
                            bordercolor="#E5E7EB",
                            borderwidth=1,
                            borderpad=4,
                        )

                    fig_ts.add_annotation(
                        x=pd.Timestamp("2027-01-01"),
                        y=1.03,
                        xref="x",
                        yref="paper",
                        text="2027：高位震荡",
                        showarrow=False,
                        xanchor="left",
                        font=dict(color="#475569", size=12),
                        bgcolor="rgba(255,255,255,0.78)",
                        bordercolor="#E5E7EB",
                        borderwidth=1,
                        borderpad=4,
                    )
    
                    # 预测区间阴影：先画上沿，再画下沿形成填充区
                    if not forecast_plot_df.empty and "forecast_upper_display" in forecast_plot_df.columns:
                        fig_ts.add_trace(
                            go.Scatter(
                                x=forecast_plot_df["date"],
                                y=forecast_plot_df["forecast_upper_display"],
                                mode="lines",
                                name="预测上沿",
                                line=dict(
                                    color="rgba(22, 119, 255, 0.45)",
                                    width=1,
                                ),
                                customdata=forecast_plot_df[["upper_correction_note"]].values,
                                hovertemplate=
                                    "日期：%{x|%Y-%m-%d}<br>"
                                    "预测上沿：%{y:.2f} 万元/吨"
                                    "%{customdata[0]}"
                                    "<extra></extra>",
                            )
                        )
    
                    if not forecast_plot_df.empty and "forecast_lower_display" in forecast_plot_df.columns:
                        fig_ts.add_trace(
                            go.Scatter(
                                x=forecast_plot_df["date"],
                                y=forecast_plot_df["forecast_lower_display"],
                                mode="lines",
                                name="预测下沿",
                                line=dict(
                                    color="rgba(255, 138, 101, 0.45)",
                                    width=1,
                                ),
                                fill="tonexty",
                                fillcolor="rgba(22, 119, 255, 0.14)",
                                customdata=forecast_plot_df[["lower_correction_note"]].values,
                                hovertemplate=
                                    "日期：%{x|%Y-%m-%d}<br>"
                                    "预测下沿：%{y:.2f} 万元/吨"
                                    "%{customdata[0]}"
                                    "<extra></extra>",
                            )
                        )
    
                    # 历史价格
                    if not actual_plot_df.empty and "actual_lce_price" in actual_plot_df.columns:
                        fig_ts.add_trace(
                            go.Scatter(
                                x=actual_plot_df["date"],
                                y=actual_plot_df["actual_lce_price"],
                                mode="lines+markers",
                                name="历史LCE价格",
                                line=dict(
                                    color=CATL_BLUE,
                                    width=4,
                                ),
                                marker=dict(
                                    size=7,
                                    color=CATL_BLUE,
                                ),
                                hovertemplate=
                                    "日期：%{x|%Y-%m-%d}<br>"
                                    "历史价格：%{y:.2f} 万元/吨"
                                    "<extra></extra>",
                            )
                        )
    
                    # 预测中枢
                    if not forecast_plot_df.empty and "forecast_center" in forecast_plot_df.columns:
                        fig_ts.add_trace(
                            go.Scatter(
                                x=forecast_plot_df["date"],
                                y=forecast_plot_df["forecast_center"],
                                mode="lines+markers",
                                name="未来预测中枢",
                                line=dict(
                                    color=TEAL,
                                    width=5.2,
                                    dash="dash",
                                ),
                                marker=dict(
                                    size=8,
                                    color=TEAL,
                                ),
                                hovertemplate=
                                    "日期：%{x|%Y-%m-%d}<br>"
                                    "预测中枢：%{y:.2f} 万元/吨"
                                    "<extra></extra>",
                            )
                        )
    
                    # 参考线数值：使用系统投资决策锚，不再使用旧CSV里的低AISC口径
                    price_center_wan = PAPER_PRICE_CENTER_WAN
                    price_floor_wan = PAPER_PRICE_LOW_WAN
                    price_upper_wan = PAPER_PRICE_HIGH_WAN
    
                    # 固定19.5是管理层决策锚，不等同于项目库真实90%战略AISC。
                    aisc_90_wan = PAPER_AISC_90_MID_WAN
    
                    if aisc_90_wan > 0:
                        fig_ts.add_hline(
                            y=aisc_90_wan,
                            line_dash="dash",
                            line_color=CORAL,
                            line_width=2,
                        )
    
                    fig_ts.add_hline(
                        y=price_center_wan,
                        line_dash="solid",
                        line_color=CATL_BLUE,
                        line_width=3,
                    )
    
                    fig_ts.add_hline(
                            y=price_floor_wan,
                            line_dash="dot",
                            line_color=CORAL,
                            line_width=2,
                    )
    
                    fig_ts.add_hline(
                        y=price_upper_wan,
                        line_dash="dot",
                        line_color="#94A3B8",
                        line_width=1.5,
                    )
                    # 右侧标注，避免文字重叠
                    if not ts_df.empty:
                        max_date = pd.Timestamp("2027-01-01")
    
                        if aisc_90_wan > 0:
                            fig_ts.add_annotation(
                                x=max_date,
                                y=aisc_90_wan,
                                text=f"决策锚：{aisc_90_wan:.2f}",
                                showarrow=False,
                                xanchor="left",
                                yanchor="bottom",
                                font=dict(
                                    color=CORAL,
                                    size=13,
                                ),
                                bgcolor="#FFFFFF",
                            )
    
                        fig_ts.add_annotation(
                            x=max_date,
                            y=price_center_wan,
                            text=f"价格中枢：{price_center_wan:.2f}",
                            showarrow=False,
                            xanchor="left",
                            yanchor="top",
                            font=dict(
                                color=CATL_BLUE,
                                size=13,
                            ),
                            bgcolor="#FFFFFF",
                        )
    
                        fig_ts.add_annotation(
                            x=max_date,
                            y=price_floor_wan,
                            text=f"成本铁底：{price_floor_wan:.2f}",
                            showarrow=False,
                            xanchor="left",
                            yanchor="top",
                                font=dict(
                                    color=CORAL,
                                    size=13,
                            ),
                            bgcolor="#FFFFFF",
                        )
    
                        fig_ts.add_annotation(
                            x=max_date,
                            y=price_upper_wan,
                            text=f"区间上沿：{price_upper_wan:.2f}",
                            showarrow=False,
                            xanchor="left",
                            yanchor="bottom",
                            font=dict(
                                color="#64748B",
                                size=13,
                            ),
                            bgcolor="#FFFFFF",
                        )
    
                    # 自动计算更合理的Y轴范围，不再从0开始
                    y_values = []
    
                    if "actual_lce_price" in actual_plot_df.columns:
                        y_values.extend(actual_plot_df["actual_lce_price"].dropna().tolist())
                    for col in ["forecast_center", "forecast_lower_display", "forecast_upper_display"]:
                        if col in forecast_plot_df.columns:
                            y_values.extend(forecast_plot_df[col].dropna().tolist())
    
                    if aisc_90_wan > 0:
                        y_values.append(aisc_90_wan)
                    y_values.extend([
                        price_center_wan,
                        price_floor_wan,
                        price_upper_wan,
                        aisc_90_wan,
                    ])
                    if y_values:
                        y_min = min(y_values)
                        y_max = max(y_values)
                        y_padding = max((y_max - y_min) * 0.25, 0.8)
                        y_range = [
                            max(0, y_min - y_padding),
                            y_max + y_padding,
                        ]
                    else:
                        y_range = [16, 21]
    
                    fig_ts.update_layout(
                        xaxis_title="日期",
                        yaxis_title="LCE价格（万元/吨）",
                        height=520,
                        hovermode="x unified",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.04,
                            xanchor="left",
                            x=0,
                            font=dict(
                                color=TEXT_DARK,
                                size=12,
                            ),
                            bgcolor="#FFFFFF",
                        ),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        margin=dict(
                            l=20,
                            r=90,
                            t=40,
                            b=40,
                        ),
                        font=dict(
                            color=TEXT_DARK,
                            size=13,
                        ),
                    )
    
                    fig_ts.update_xaxes(
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        zeroline=False,
                        color=TEXT_DARK,
                        range=[
                            pd.Timestamp("2026-01-01"),
                            pd.Timestamp("2027-01-01"),
                        ],
                        tickformat="%Y.%m",
                        title_font=dict(
                            color=TEXT_DARK,
                            size=14,
                        ),
                        tickfont=dict(
                            color=TEXT_DARK,
                            size=12,
                        ),
                    )
    
                    fig_ts.update_yaxes(
                        range=y_range,
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        zeroline=False,
                        color=TEXT_DARK,
                        title_font=dict(
                            color=TEXT_DARK,
                            size=14,
                        ),
                        tickfont=dict(
                            color=TEXT_DARK,
                            size=12,
                        ),
                    )
    
                    st.plotly_chart(fig_ts, width="stretch")
                    if has_forecast_band_correction:
                        st.caption("部分未来预测区间已按中枢自动校正，用于避免展示冲突；原始CSV数据未被修改。")
    
            with strategy_col:
                inventory_signal = get_inventory_signal(
                    safe_num(forecast.get("inventory_days", 0))
                )
                inventory_signal_color = inventory_signal.get("color", TEXT_MUTED)
                inventory_signal_status = inventory_signal.get("status", "暂无数据")

                st.markdown("#### 价格区间判断")
                st.markdown(
                    f"""
                    <div class="strategy-box">
                    <b>{price_zone if price_zone else "暂无判断"}</b><br>
                    <span style="color:{inventory_signal_color};font-weight:800;">
                    库存状态：{inventory_signal_status}
                    </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
                st.markdown("#### 生产者策略建议")
                st.markdown(
                    f"""
                    <div class="strategy-box">
                    {producer_strategy if producer_strategy else "暂无生产者策略建议。"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
                st.markdown("#### 核心输入")
    
                input_m1, input_m2 = st.columns(2)
    
                with input_m1:
                    compact_metric_card(
                        "GFEX期货价格",
                        format_wan(forecast.get("gfex_futures_price", 0)),
                        "元/吨LCE口径",
                    )
    
                with input_m2:
                    sc6_price = forecast.get("sc6_price_index_usd_per_tonne", 0)
                    if sc6_price <= 0:
                        sc6_price = forecast.get("sc6_price_index", 0)
    
                    compact_metric_card(
                        "SC6价格",
                        f"{sc6_price:.0f} 美元/吨",
                        "锂精矿价格",
                    )
    
                input_m3, input_m4 = st.columns(2)
    
                with input_m3:
                    compact_metric_card(
                        "库存天数",
                        f"{forecast.get('inventory_days', 0):.1f} 天",
                        "下游库存周转",
                    )
    
                with input_m4:
                    compact_metric_card(
                        "正极开工率",
                        f"{forecast.get('cathode_utilization', 0):.1%}",
                        "需求侧强度",
                    )
            # =========================
            # 价格模型因子贡献
            # =========================
    
                   # =========================
            # 价格驱动因子强度
            # =========================
    
            inventory_days = forecast.get("inventory_days", 0)

            current_inventory_days = safe_num(forecast.get("inventory_days", 0))

            render_inventory_signal_panel(current_inventory_days)

            st.markdown("#### 价格模型因子贡献")
    
            # 当前输入变量
            sc6_price = forecast.get("sc6_price_index_usd_per_tonne", 0)
            if sc6_price <= 0:
                sc6_price = forecast.get("sc6_price_index", 0)
    
            usd_cny = forecast.get("usd_cny", 7.2)
            sc6_to_lce_conversion = forecast.get("sc6_to_lce_conversion", 8.0)
            sc6_pass_through = forecast.get("sc6_pass_through", 0.30)
    
            cathode_utilization = forecast.get("cathode_utilization", 0)
            gfex_adjustment = forecast.get("gfex_adjustment", 0)
    
            if cathode_utilization <= 0:
                cathode_utilization = 0.72
    
            if inventory_days <= 0:
                inventory_days = 24.7
    
            # =========================
            # 按当前模型口径重新计算
            # =========================
            # 1. SC6：删除基准SC6后，直接使用当前SC6折算LCE成本 × 传导系数
            current_sc6_lce_cost = sc6_price * usd_cny * sc6_to_lce_conversion
            sc6_adjustment = current_sc6_lce_cost * sc6_pass_through
    
            # 2. 正极开工率：用65%作为中性开工率，超过部分视为需求强度正向压力
            #    0.15为当前系统采用的需求弹性参数
            neutral_utilization = 0.65
            utilization_beta = 0.15
            utilization_adjustment = (
                max(cathode_utilization - neutral_utilization, 0)
                * PAPER_PRICE_CENTER_WAN
                * 10000
                * utilization_beta
            )
    
            # 3. 库存周期：论文中库存天数为负向变量，库存越高，对价格越压制
            #    这里按当前库存天数直接体现负向压力，不再显示为0
            inventory_beta = -0.42
            inventory_adjustment = inventory_beta * inventory_days * 1000
    
            # 4. AISC成本支撑：用90% AISC中位与价格下沿之间的安全垫衡量支撑强度
            aisc_support_gap_wan = PAPER_AISC_90_MID_WAN - PAPER_PRICE_LOW_WAN
            aisc_beta = 0.58
            aisc_adjustment = aisc_support_gap_wan * 10000 * aisc_beta
    
            # 5. GFEX：保留后端计算结果。如果没有，则用0
            gfex_adjustment = forecast.get("gfex_adjustment", 0)
    
            factor_c1, factor_c2, factor_c3, factor_c4, factor_c5 = st.columns(5)
    
            with factor_c1:
                compact_metric_card(
                    "当前SC6成本压力",
                    format_wan(sc6_adjustment),
                    "当前SC6折算成本 × 传导系数",
                )
    
            with factor_c2:
                compact_metric_card(
                    "正极开工率压力",
                    format_wan(utilization_adjustment),
                    f"当前开工率 {cathode_utilization:.1%}",
                )
    
            with factor_c3:
                compact_metric_card(
                    "库存周期压力",
                    format_wan(inventory_adjustment),
                    f"库存 {inventory_days:.1f} 天，领先价格约 {PAPER_INVENTORY_LEAD_WEEKS_LOW}–{PAPER_INVENTORY_LEAD_WEEKS_HIGH} 周",
                )
    
            with factor_c4:
                compact_metric_card(
                    "AISC成本支撑",
                    format_wan(aisc_adjustment),
                    f"90% AISC支撑带 {PAPER_AISC_90_LOW_WAN:.1f}–{PAPER_AISC_90_HIGH_WAN:.1f} 万元/吨",
                )
    
            with factor_c5:
                compact_metric_card(
                    "GFEX预期修正",
                    format_wan(gfex_adjustment),
                    "期货价格反映市场预期",
                )
    
            factor_df = pd.DataFrame(
                {
                    "因子": [
                        "SC6成本压力",
                        "正极开工率",
                        "库存周期",
                        "AISC支撑",
                        "GFEX预期",
                    ],
                    "价格压力/修正": [
                        sc6_adjustment / 10000,
                        utilization_adjustment / 10000,
                        inventory_adjustment / 10000,
                        aisc_adjustment / 10000,
                        gfex_adjustment / 10000,
                    ],
                }
            )
            factor_df["压力强度"] = factor_df["价格压力/修正"].abs()
            max_factor_pressure = factor_df["压力强度"].max()
            factor_pressure_palette = [
                TEAL_LIGHT,
                TEAL,
                CORAL_LIGHT,
                CORAL,
                CORAL_DARK,
            ]

            def factor_pressure_color(value):
                if max_factor_pressure <= 0:
                    return factor_pressure_palette[0]

                ratio = value / max_factor_pressure

                if ratio <= 0.20:
                    return factor_pressure_palette[0]
                if ratio <= 0.40:
                    return factor_pressure_palette[1]
                if ratio <= 0.60:
                    return factor_pressure_palette[2]
                if ratio <= 0.80:
                    return factor_pressure_palette[3]
                return factor_pressure_palette[4]

            factor_df["颜色"] = factor_df["压力强度"].apply(factor_pressure_color)
            factor_df.loc[
                factor_df["因子"].isin(["正极开工率", "GFEX预期"]),
                "颜色",
            ] = "#FFCCBC"
            factor_df.loc[
                factor_df["因子"] == "AISC支撑",
                "颜色",
            ] = "#FF6B35"
    
            fig_factor = go.Figure()
    
            fig_factor.add_trace(
                go.Bar(
                    x=factor_df["因子"],
                    y=factor_df["价格压力/修正"],
                    marker=dict(
                        color=factor_df["颜色"],
                        line=dict(color="#FFFFFF", width=1),
                    ),
                    text=[f"{v:+.2f}" for v in factor_df["价格压力/修正"]],
                    textposition="outside",
                    hovertemplate=
                        "因子：%{x}<br>"
                        "价格压力/修正：%{y:+.2f} 万元/吨"
                        "<extra></extra>",
                )
            )
    
            fig_factor.add_hline(
                y=0,
                line_color="#64748B",
                line_width=1,
            )
    
            fig_factor.update_layout(
                xaxis_title="模型因子",
                yaxis_title="价格压力 / 修正（万元/吨）",
                height=430,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(
                    l=30,
                    r=30,
                    t=35,
                    b=60,
                ),
                font=dict(
                    color=TEXT_DARK,
                    size=13,
                ),
                showlegend=False,
            )
    
            fig_factor.update_xaxes(
                tickfont=dict(color=TEXT_DARK, size=13),
                title_font=dict(color=TEXT_DARK, size=14),
                showgrid=False,
            )
    
            fig_factor.update_yaxes(
                tickfont=dict(color=TEXT_DARK, size=13),
                title_font=dict(color=TEXT_DARK, size=14),
                gridcolor="#E5E7EB",
                zeroline=False,
            )
    
            st.plotly_chart(fig_factor, width="stretch")
    
            st.markdown(
                f"""
                <div class="insight-box">
                <b>模型判读：</b>
                本模块不再读取后端 CSV 中可能为0的修正字段，而是直接依据当前高频输入重新计算价格驱动强度。
                当前SC6成本压力来自锂精矿价格折算LCE成本后的传导；正极开工率反映需求端强度；
                库存周期为负向变量，库存天数偏高会压制现货价格；90% AISC体现价格下沿的边际成本支撑；
                GFEX主力合约反映市场预期。
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("#### SC6单位转换与成本传导")
            sc6_c1, sc6_c2, sc6_c3, sc6_c4 = st.columns(4)
    
            with sc6_c1:
                compact_metric_card(
                    "当前SC6价格",
                    f"{sc6_price:.0f} 美元/吨",
                    "澳洲SC6锂精矿CIF口径",
                )
    
            with sc6_c2:
                compact_metric_card(
                    "SC6折算LCE成本",
                    format_wan(current_sc6_lce_cost),
                    "当前SC6 × 汇率 × 单耗",
                )
    
            with sc6_c3:
                compact_metric_card(
                    "SC6传导系数",
                    f"{sc6_pass_through:.0%}",
                    "矿端成本向LCE价格传导比例",
                )
    
            with sc6_c4:
                compact_metric_card(
                    "当前SC6成本压力",
                    format_wan(sc6_adjustment),
                    "当前SC6折算成本 × 传导系数",
                )
        section_close()


    # =========================
    # Market Monitor 市场监测中心
    # =========================

    def render_section_02_market_monitor():
        section_header("Market Monitor", "市场监测中心")
        section_open()

        @st.cache_data(ttl=900, show_spinner=False)
        def cached_market_monitor_data(cache_version):
            from market_data import fetch_market_monitor_data

            return fetch_market_monitor_data()

        try:
            monitor_data = cached_market_monitor_data("inventory_monitor_v2")
        except Exception:
            monitor_data = {
                "commodities": [],
                "inventory": [],
                "fx": [],
                "equities": [],
                "macro": [],
            }

        if not monitor_data.get("inventory"):
            latest_input = weekly_inputs_df.iloc[-1] if not weekly_inputs_df.empty else pd.Series(dtype="object")
            inventory_value = safe_num(latest_input.get("gfex_registered_receipts_tonnes", 0))
            inventory_change = safe_num(latest_input.get("gfex_inventory_change_tonnes", 0))
            if inventory_value > 0:
                monitor_data["inventory"] = [
                    {
                        "label": "碳酸锂库存/仓单",
                        "latest": inventory_value,
                        "change_5d": 0,
                        "sparkline": [inventory_value],
                        "source": latest_input.get("exchange_inventory_source", "weekly_price_inputs.csv"),
                        "change_label": f"最新增减 {inventory_change:+,.0f} 吨",
                        "unit_label": "吨",
                    }
                ]

        monitor_sections = [
            ("商品价格监测", monitor_data.get("commodities", [])),
            ("库存与仓单监测", monitor_data.get("inventory", [])),
            ("汇率监测", monitor_data.get("fx", [])),
            ("矿企股价监测", monitor_data.get("equities", [])),
            ("宏观因子", monitor_data.get("macro", [])),
        ]

        def format_monitor_value(value):
            try:
                value = float(value)
            except Exception:
                return "N/A"

            if abs(value) >= 1000:
                return f"{value:,.0f}"
            if abs(value) >= 10:
                return f"{value:,.2f}"
            return f"{value:,.4f}"

        def render_monitor_card(item):
            label = item.get("label", "N/A")
            latest = format_monitor_value(item.get("latest", 0))
            change_5d = item.get("change_5d", 0)
            source = item.get("source", "N/A")
            sparkline = item.get("sparkline", [])

            try:
                change_text = f"{float(change_5d):+.2f}%"
            except Exception:
                change_text = "N/A"
            change_label = item.get("change_label", f"5日变化 {change_text}")
            unit_label = item.get("unit_label", "")
            latest_display = f"{latest} {unit_label}".strip()

            fig_spark = go.Figure()
            fig_spark.add_trace(
                go.Scatter(
                    x=list(range(len(sparkline))),
                    y=sparkline,
                    mode="lines",
                    line=dict(color="#1677FF", width=3),
                    fill="tozeroy",
                    fillcolor="#E6F4FF",
                    hoverinfo="skip",
                )
            )
            fig_spark.update_layout(
                height=82,
                margin=dict(l=0, r=0, t=4, b=0),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
            )

            st.markdown(
                f"""
                <div style="
                    background:#FFFFFF;
                    border:1px solid #D9E2F2;
                    border-radius:10px;
                    padding:14px 14px 8px 14px;
                    box-shadow:0 2px 8px #D9E2F2;
                    min-height:178px;
                ">
                    <div style="font-size:13px;color:#64748B;font-weight:800;">{label}</div>
                    <div style="font-size:25px;color:#003A8C;font-weight:900;margin-top:6px;">{latest_display}</div>
                    <div style="font-size:12px;color:#0052CC;font-weight:800;margin-top:4px;">{change_label}</div>
                    <div style="font-size:11px;color:#6B7280;margin-top:2px;">数据源：{source}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                fig_spark,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown(
            """
            <div class="insight-box">
            <b>市场监测中心：</b>
            聚合商品价格、汇率、矿企股价与宏观因子，跟踪锂资源配置相关的外部市场变量。
            </div>
            """,
            unsafe_allow_html=True,
        )

        for section_title, items in monitor_sections:
            st.markdown(f"#### {section_title}")

            if not items:
                st.info(f"暂无{section_title}数据。")
                continue

            cols = st.columns(4)

            for idx, item in enumerate(items):
                with cols[idx % 4]:
                    render_monitor_card(item)

        section_close()

    # =========================
    # 03 LCE年度供需缺口与可兑现供应预测
    # =========================

    def render_section_03_supply_demand():
        section_header("02", "2026–2035中期预测")
        section_open()
    
        if supply_demand_df.empty:
            st.warning("暂无 lce_supply_demand_forecast.csv。请先运行：python supply_demand_forecast.py")
        else:
            sd_df = supply_demand_df.copy()
    
            numeric_cols = [
                "adjusted_demand_lce",
                "effective_supply_lce",
                "balance_lce",
                "gap_ratio",
                "base_demand_lce",
                "ess_uplift_lce",
                "inventory_restocking_lce",
                "announced_supply_lce",
                "policy_disruption_lce",
                "logistics_delay_lce",
            ]
    
            for col in numeric_cols:
                if col in sd_df.columns:
                    sd_df[col] = pd.to_numeric(sd_df[col], errors="coerce")
    
            # =========================
            # 年度口径统一
            # =========================
            # 只保留年度维度：2026、2027、2028、2029、2030
            # 若原数据里有“未来12个月”，映射为2026。
            # “未来6个月”不进入年度主图，避免半年度和年度混合比较。
            # =========================
    
            def infer_year(row):
                if "year" in row and pd.notna(row.get("year")):
                    try:
                        return int(row.get("year"))
                    except Exception:
                        pass
    
                period = str(row.get("period", ""))
    
                if period == "未来12个月":
                    return 2026
    
                for y in [2026, 2027, 2028, 2029, 2030]:
                    if str(y) in period:
                        return y
    
                return None
    
            sd_df["year_display"] = sd_df.apply(infer_year, axis=1)
            annual_df = sd_df[sd_df["year_display"].isin([2026, 2027, 2028, 2029, 2030])].copy()
    
            if annual_df.empty:
                st.warning("当前供需预测数据中没有 2026-2030 年度口径。请检查 lce_supply_demand_forecast.csv。")
            else:
                # 若同一年有多条记录，优先保留最后一条
                annual_df = (
                    annual_df
                    .sort_values("year_display")
                    .drop_duplicates(subset=["year_display"], keep="last")
                    .sort_values("year_display")
                    .reset_index(drop=True)
                )
    
                # 字段兜底
                if "announced_supply_lce" not in annual_df.columns:
                    annual_df["announced_supply_lce"] = annual_df.get("effective_supply_lce", 0)
    
                if "effective_supply_lce" not in annual_df.columns:
                    annual_df["effective_supply_lce"] = annual_df.get("announced_supply_lce", 0)
    
                if "adjusted_demand_lce" not in annual_df.columns:
                    annual_df["adjusted_demand_lce"] = 0
    
                annual_df["supply_discount_lce"] = (
                    annual_df["announced_supply_lce"] - annual_df["effective_supply_lce"]
                )
    
                annual_df["display_gap_lce"] = (
                    annual_df["adjusted_demand_lce"] - annual_df["effective_supply_lce"]
                )
    
                annual_df["display_gap_lce"] = annual_df["display_gap_lce"].fillna(0)
                annual_df["supply_discount_lce"] = annual_df["supply_discount_lce"].fillna(0)
                
                # =========================
                # 与第三层 APS 基准情景统一
                # =========================
                # 第二层中期供需平衡统一采用第三层 APS 情景的 2026–2030 截取版。
                # 注意：
                # 第三层“供需平衡”口径 = 供给 - 需求，负数代表短缺。
                # 第二层“LCE缺口”口径 = 需求 - 供给，正数代表短缺。
                # 因此这里将 APS 的负平衡值转为正缺口。
                # =========================        
                annual_df = pd.DataFrame({
                "year_display": [2026, 2027, 2028, 2029, 2030],
                "adjusted_demand_lce": [160, 195, 235, 280, 325],
                "effective_supply_lce": [152, 185, 220, 248, 275],
                "display_gap_lce": [8, 10, 15, 32, 50],
                "announced_supply_lce": [152, 185, 220, 248, 275],
                "supply_discount_lce": [0, 0, 0, 0, 0],
                "market_status": ["短缺", "短缺", "短缺", "短缺", "短缺"],
            }) 
                # =========================
                # 顶部指标
                # =========================
    
                row_2026 = annual_df[annual_df["year_display"] == 2026]
                row_2030 = annual_df[annual_df["year_display"] == 2030]
    
                gap_2026 = float(row_2026["display_gap_lce"].iloc[0]) if not row_2026.empty else 0
                gap_2030 = float(row_2030["display_gap_lce"].iloc[0]) if not row_2030.empty else 0
    
                max_gap_row = annual_df.loc[annual_df["display_gap_lce"].idxmax()]
                max_gap_year = int(max_gap_row["year_display"])
                max_gap_value = float(max_gap_row["display_gap_lce"])
    
                cumulative_discount = float(annual_df["supply_discount_lce"].sum())
                shortage_years = int((annual_df["display_gap_lce"] > 0).sum())
    
                c1, c2, c3, c4, c5 = st.columns(5)
                
    
                with c1:
                    compact_metric_card(
                        "2026供需缺口",
                        f"{gap_2026:.1f} 万吨",
                        "年度口径：需求 - 可兑现供应",
                    )
    
                with c2:
                    compact_metric_card(
                        "2030基准缺口",
                        f"{gap_2030:.1f} 万吨",
                         "APS情景，需求 - 可兑现供应",
                    )
    
                with c3:
                    compact_metric_card(
                        "最大缺口年份",
                        f"{max_gap_year}",
                        f"缺口约 {max_gap_value:.1f} 万吨",
                    )
    
                with c4:
                    compact_metric_card(
                        "2026–2030累计缺口",
                        f"{annual_df['display_gap_lce'].sum():.1f} 万吨",
                        "APS情景累计短缺",
                    )
    
                with c5:
                    compact_metric_card(
                        "短缺年份数量",
                        f"{shortage_years} 年",
                        "年度缺口 > 0",
                    )
    
                st.markdown(
                    """
                    <div class="insight-box">
                    <b>模型解释：</b>
                    本模块统一采用年度口径，横坐标仅展示 2026、2027、2028、2029、2030。
                    主图不再堆叠展示过多柱状图，而是用“调整后需求线、可兑现供应线、LCE缺口线”呈现供需关系。
                    名义供应和供给折损不放入主图，以避免视觉复杂化；相关数据保留在下方明细表中。
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
                # =========================
                # 优化主图：需求/供给折线 + 缺口柱状图
                # =========================

                st.markdown("#### 中期供需平衡：APS基准情景（2026–2030）")

                fig_balance = make_subplots(specs=[[{"secondary_y": True}]])

                bar_width = 0.34

                # 缺口柱状图：右轴，放在背景层
                fig_balance.add_trace(
                    go.Bar(
                        x=annual_df["year_display"],
                        y=annual_df["display_gap_lce"],
                        name="LCE缺口",
                        width=bar_width,
                        zorder=0,
                        marker=dict(
                            color=CORAL_LIGHT,
                            line=dict(color=CORAL_DARK, width=1),
                        ),
                        text=[f"{v:.0f}" for v in annual_df["display_gap_lce"]],
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate=(
                            "年份：%{x}<br>"
                            "LCE缺口：%{y:.1f} 万吨<br>"
                            "缺口 = 需求 - 可兑现供应"
                            "<extra></extra>"
                        ),
                    ),
                    secondary_y=True,
                )

                # 需求折线：左轴
                fig_balance.add_trace(
                    go.Scatter(
                        x=annual_df["year_display"],
                        y=annual_df["adjusted_demand_lce"],
                        name="需求",
                        mode="lines+markers",
                        zorder=3,
                        line=dict(
                            color=CATL_BLUE,
                            width=4,
                            shape="spline",
                        ),
                        marker=dict(
                            size=9,
                            color=CATL_BLUE,
                            line=dict(color="#FFFFFF", width=1.5),
                        ),
                        hovertemplate=(
                            "年份：%{x}<br>"
                            "需求：%{y:.1f} 万吨LCE"
                            "<extra></extra>"
                        ),
                    ),
                    secondary_y=False,
                )

                # 可兑现供应折线：左轴
                fig_balance.add_trace(
                    go.Scatter(
                        x=annual_df["year_display"],
                        y=annual_df["effective_supply_lce"],
                        name="可兑现供应",
                        mode="lines+markers",
                        zorder=3,
                        line=dict(
                            color=TEAL,
                            width=4,
                            dash="dash",
                            shape="spline",
                        ),
                        marker=dict(
                            size=9,
                            color=TEAL,
                            line=dict(color="#FFFFFF", width=1.5),
                        ),
                        hovertemplate=(
                            "年份：%{x}<br>"
                            "可兑现供应：%{y:.1f} 万吨LCE"
                            "<extra></extra>"
                        ),
                    ),
                    secondary_y=False,
                )

                fig_balance.update_layout(
                    height=560,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    hovermode="x unified",
                    barmode="overlay",
                    bargap=0.58,
                    font=dict(color=TEXT_DARK, size=13),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.08,
                        xanchor="left",
                        x=0,
                        font=dict(color=TEXT_DARK, size=13),
                        bgcolor="#FFFFFF",
                        bordercolor=BORDER,
                        borderwidth=1,
                    ),
                    margin=dict(l=30, r=70, t=45, b=70),
                )

                fig_balance.update_xaxes(
                    title_text="年份",
                    tickmode="array",
                    tickvals=[2026, 2027, 2028, 2029, 2030],
                    ticktext=["2026", "2027", "2028", "2029", "2030"],
                    showgrid=False,
                    color=TEXT_DARK,
                    title_font=dict(color=TEXT_DARK, size=14),
                )

                fig_balance.update_yaxes(
                    title_text="需求 / 供应（万吨LCE）",
                    secondary_y=False,
                    gridcolor="#E5E7EB",
                    zeroline=False,
                    color=TEXT_DARK,
                    title_font=dict(color=TEXT_DARK, size=14),
                )

                fig_balance.update_yaxes(
                    title_text="LCE缺口（万吨）",
                    secondary_y=True,
                    showgrid=False,
                    zeroline=False,
                    color=CORAL,
                    title_font=dict(color=CORAL, size=14),
                )

                st.plotly_chart(fig_balance, width="stretch")

                st.caption(
                    "说明：第二层采用第三层 APS 基准情景的 2026–2030 截取数据。"
                    "蓝色实线为需求，绿色虚线为可兑现供应，橙色柱状图为LCE缺口。"
                    "这里的缺口采用“需求 - 可兑现供应”口径，因此正数代表短缺。"
                )
    
                # =========================
                # 未来预测依据说明
                # =========================
    
                basis_left, basis_right = st.columns([1.1, 1])
    
                with basis_left:
                    st.markdown(
                        """
                        <div class="insight-box">
                        <b>未来预测依据：</b><br>
                        1. <b>需求端：</b>以新能源汽车、储能、电池排产和补库需求为核心驱动，储能需求上修会直接抬高调整后需求。<br>
                        2. <b>供给端：</b>不直接使用公告产能，而是将名义供应按项目兑现率、爬坡节奏、运营率、政策扰动和物流时滞折减为可兑现供应。<br>
                        3. <b>缺口定义：</b>LCE缺口 = 调整后需求 - 可兑现供应。缺口为正，代表市场偏紧；缺口扩大，代表价格上行压力增强。
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    
                with basis_right:
                    st.markdown(
                        """
                        <div class="strategy-box">
                        <b>投资含义：</b><br>
                        年度缺口扩大时，买方应优先锁定低成本、低政策风险、爬坡确定性强的资源。
                        若名义供应高但可兑现供应不足，说明市场表面过剩并不等于真实宽松。
                        因此资源配置应重点关注可兑现性，而不是仅看公告产能。
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    
                with st.expander("查看年度供需预测明细数据"):
                    show_cols = [
                        "year_display",
                        "adjusted_demand_lce",
                        "announced_supply_lce",
                        "effective_supply_lce",
                        "supply_discount_lce",
                        "display_gap_lce",
                        "balance_lce",
                        "gap_ratio",
                        "base_demand_lce",
                        "ess_uplift_lce",
                        "inventory_restocking_lce",
                        "policy_disruption_lce",
                        "logistics_delay_lce",
                        "market_status",
                    ]
    
                    show_cols = [
                        col for col in show_cols
                        if col in annual_df.columns
                    ]
    
                    show_df = annual_df[show_cols].copy()
    
                    rename_map = {
                        "year_display": "年份",
                        "adjusted_demand_lce": "调整后需求",
                        "announced_supply_lce": "名义供应",
                        "effective_supply_lce": "可兑现供应",
                        "supply_discount_lce": "供给折损",
                        "display_gap_lce": "LCE缺口",
                        "balance_lce": "原始平衡值",
                        "gap_ratio": "缺口比例",
                        "base_demand_lce": "基础需求",
                        "ess_uplift_lce": "储能需求增量",
                        "inventory_restocking_lce": "补库需求",
                        "policy_disruption_lce": "政策扰动",
                        "logistics_delay_lce": "物流延迟",
                        "market_status": "市场状态",
                    }
    
                    show_df = show_df.rename(columns=rename_map)
    
                    st.dataframe(
                        show_df,
                        width="stretch",
                        hide_index=True,
                    )
    
        section_close()


    # =========================
    # 04 全球锂矿战略分布图
    # =========================

    def render_section_03_long_term_scenario():
        return

    def render_section_04_resource_map():
        section_header("04", "全球资源地图")
        section_open()
    
        map_df = cost_df.copy()
        # =========================
        # 战略资源池分类
        # =========================
    
        def classify_resource_strategy(row):
            country = str(row.get("country", "")).lower()
            resource_type = str(row.get("resource_type", "")).lower()
            name = str(row.get("name", "")).lower()
    
            if country in ["chile", "argentina"] and "brine" in resource_type:
                return "南美低成本盐湖"
    
            if country == "australia" and "spodumene" in resource_type:
                return "澳洲高品位锂辉石"
    
            if country in ["zimbabwe", "mali", "ghana"] or any(
                key in name for key in ["bikita", "arcadia", "goulamina", "ewoyaa"]
            ):
                return "非洲本地化资源"
    
            if country == "china" or "lepidolite" in resource_type:
                return "中国锂云母/冶炼体系"
    
            if country in ["canada", "united states"]:
                return "北美战略资源"
    
            return "其他观察资源"
    
        map_df["strategy_pool"] = map_df.apply(classify_resource_strategy, axis=1)
        if not invest_df.empty and "name" in invest_df.columns and "country" in invest_df.columns:
            invest_cols = [
                col for col in [
                    "name",
                    "country",
                    "investment_score",
                    "risk_score",
                    "recommended_action",
                ]
                if col in invest_df.columns
            ]
    
            if "investment_score" in invest_cols:
                map_df = map_df.merge(
                    invest_df[invest_cols],
                    on=["name", "country"],
                    how="left",
                    suffixes=("", "_invest"),
                )
    
        if "investment_score_invest" in map_df.columns:
            if "investment_score" in map_df.columns:
                map_df["investment_score"] = map_df["investment_score_invest"].fillna(
                    map_df["investment_score"]
                )
            else:
                map_df["investment_score"] = map_df["investment_score_invest"].fillna(0.5)
    
        if "risk_score_invest" in map_df.columns:
            if "risk_score" in map_df.columns:
                map_df["risk_score"] = map_df["risk_score_invest"].fillna(map_df["risk_score"])
            else:
                map_df["risk_score"] = map_df["risk_score_invest"].fillna(0.5)
    
        if "latitude" not in map_df.columns or "longitude" not in map_df.columns:
            st.warning("当前数据缺少 latitude / longitude 字段。请先运行 python geocode_missing_projects.py。")
        else:
            map_df["latitude"] = pd.to_numeric(map_df["latitude"], errors="coerce")
            map_df["longitude"] = pd.to_numeric(map_df["longitude"], errors="coerce")
            map_df = map_df.dropna(subset=["latitude", "longitude"]).copy()
    
            if map_df.empty:
                st.warning("没有可用于地图显示的项目。")
            else:
                for col, default in [
                    ("annual_capacity", 0),
                    ("investment_score", 0.5),
                    ("risk_score", 0.5),
                    ("aisc_cost", 0),
                    ("adjusted_aisc", 0),
                ]:
                    if col not in map_df.columns:
                        map_df[col] = default
                    map_df[col] = pd.to_numeric(map_df[col], errors="coerce").fillna(default)
    
                if "status" not in map_df.columns:
                    map_df["status"] = "Unknown"
    
                if "resource_type" not in map_df.columns:
                    map_df["resource_type"] = "Unknown"
    
                if "recommended_action" not in map_df.columns:
                    map_df["recommended_action"] = "N/A"
    
                # =========================
                # PyDeck 数据准备
                # =========================
    
                def score_to_color(score):
                    try:
                        score = float(score)
                    except Exception:
                        score = 0.5
    
                    if score >= 0.70:
                        return [22, 163, 74, 190]       # 绿色
                    if score >= 0.55:
                        return [250, 204, 21, 190]      # 黄色
                    if score >= 0.40:
                        return [245, 158, 11, 190]      # 橙色
                    return [220, 38, 38, 190]           # 红色
    
                def risk_to_border_color(risk):
                    try:
                        risk = float(risk)
                    except Exception:
                        risk = 0.5
    
                    if risk >= 0.70:
                        return [220, 38, 38, 255]
                    if risk >= 0.50:
                        return [245, 158, 11, 255]
                    return [0, 58, 140, 255]
    
                map_df["fill_color"] = map_df["investment_score"].apply(score_to_color)
                map_df["line_color"] = map_df["risk_score"].apply(risk_to_border_color)
    
                map_df["annual_capacity"] = pd.to_numeric(
                    map_df["annual_capacity"],
                    errors="coerce",
                ).fillna(0)
    
                max_capacity = map_df["annual_capacity"].max()
    
                if max_capacity <= 0:
                    map_df["radius"] = 65000
                else:
                    map_df["radius"] = (
                        35000
                        + (map_df["annual_capacity"] / max_capacity).clip(0, 1) * 95000
                    )
    
                map_df["tooltip_text"] = (
                    "<b>" + map_df["name"].astype(str) + "</b><br/>"
                    + "战略分类：" + map_df["strategy_pool"].astype(str) + "<br/>"
                    + "国家：" + map_df["country"].astype(str) + "<br/>"
                    + "资源类型：" + map_df["resource_type"].astype(str) + "<br/>"
                    + "状态：" + map_df["status"].astype(str) + "<br/>"
                    + "年产能：" + map_df["annual_capacity"].round(0).astype(int).astype(str) + "<br/>"
                    + "调整后AISC：" + map_df["adjusted_aisc"].round(0).astype(int).astype(str) + "<br/>"
                    + "投资评分：" + map_df["investment_score"].round(2).astype(str) + "<br/>"
                    + "风险评分：" + map_df["risk_score"].round(2).astype(str)
                )
    
                # =========================
                # 地图上方摘要
                # =========================
    
                total_projects = len(map_df)
                high_score_projects = int((map_df["investment_score"] >= 0.70).sum())
                high_risk_projects = int((map_df["risk_score"] >= 0.70).sum())
    
                # =========================
                # 地图上方摘要：战略资源池
                # =========================
    
                total_projects = len(map_df)
                high_score_projects = int((map_df["investment_score"] >= 0.70).sum())
                high_risk_projects = int((map_df["risk_score"] >= 0.70).sum())
    
                south_america_count = int((map_df["strategy_pool"] == "南美低成本盐湖").sum())
                australia_count = int((map_df["strategy_pool"] == "澳洲高品位锂辉石").sum())
                africa_count = int((map_df["strategy_pool"] == "非洲本地化资源").sum())
    
                m1, m2, m3, m4, m5, m6 = st.columns(6)
    
                with m1:
                    compact_metric_card(
                        "地图项目数",
                        f"{total_projects} 个",
                        "具备经纬度的项目",
                    )
    
                with m2:
                    compact_metric_card(
                        "南美盐湖",
                        f"{south_america_count} 个",
                        "长期低成本资源池",
                    )
    
                with m3:
                    compact_metric_card(
                        "澳洲锂辉石",
                        f"{australia_count} 个",
                        "高品位稳定供应",
                    )
    
                with m4:
                    compact_metric_card(
                        "非洲资源",
                        f"{africa_count} 个",
                        "本地化加工与政策风险并存",
                    )
    
                with m5:
                    compact_metric_card(
                        "高评分项目",
                        f"{high_score_projects} 个",
                        "投资评分 ≥ 0.70",
                    )
    
                with m6:
                    compact_metric_card(
                        "高风险项目",
                        f"{high_risk_projects} 个",
                        "风险评分 ≥ 0.70",
                    )
    
                st.markdown(
                    """
                    <div class="insight-box">
                    <b>地图战略判读：</b>
                    点位代表全球主要锂资源项目；圆点大小代表年产能；圆点颜色代表投资评分；
                    边框颜色代表风险水平。本模块的核心不是简单看项目分布，而是识别三类战略资源池：
                    南美低成本盐湖、澳洲高品位锂辉石、非洲本地化资源。
                    对买方而言，低成本、低政策风险、爬坡确定性和可长期锁量能力，是优先级排序的核心。
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
                # =========================
                # PyDeck 图层
                # =========================
    
                midpoint_lat = float(map_df["latitude"].mean())
                midpoint_lon = float(map_df["longitude"].mean())
    
                view_state = pdk.ViewState(
                    latitude=midpoint_lat,
                    longitude=midpoint_lon,
                    zoom=1.1,
                    pitch=0,
                    bearing=0,
                )
                highlight_df = map_df[map_df["investment_score"] >= 0.70].copy()
                highlight_df["highlight_radius"] = highlight_df["radius"] * 1.65
                highlight_df["highlight_color"] = highlight_df["fill_color"].apply(
                lambda c: [c[0], c[1], c[2], 70]
    )
    
                highlight_layer = pdk.Layer(
                "ScatterplotLayer",
                data=highlight_df,
                get_position="[longitude, latitude]",
                get_radius="highlight_radius",
                get_fill_color="highlight_color",
                pickable=False,
                stroked=False,
                filled=True,
                radius_min_pixels=16,
                radius_max_pixels=70,
    )
                scatter_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df,
                    get_position="[longitude, latitude]",
                    get_radius="radius",
                    get_fill_color="fill_color",
                    get_line_color="line_color",
                    pickable=True,
                    stroked=True,
                    filled=True,
                    line_width_min_pixels=1.5,
                    radius_min_pixels=5,
                    radius_max_pixels=26,
                )
    
                text_layer = pdk.Layer(
                    "TextLayer",
                    data=map_df[map_df["investment_score"] >= 0.70].copy(),
                    get_position="[longitude, latitude]",
                    get_text="name",
                    get_size=12,
                    get_color=[0, 58, 140, 220],
                    get_angle=0,
                    get_text_anchor="middle",
                    get_alignment_baseline="bottom",
                    pickable=False,
                )
    
                deck = pdk.Deck(
                    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                    initial_view_state=view_state,
                    layers=[
                        highlight_layer,
                        scatter_layer,
                        text_layer,
                    ],
                    tooltip={
                        "html": "{tooltip_text}",
                        "style": {
                            "backgroundColor": "white",
                            "color": "#1F2937",
                            "border": "1px solid #D9E2F2",
                            "borderRadius": "8px",
                            "padding": "10px",
                            "fontSize": "13px",
                        },
                    },
                )
    
                map_col, insight_col = st.columns([1.55, 1])

                with map_col:
                    st.pydeck_chart(deck, width="stretch")
        
                    # =========================
                    # 地图图例
                    # =========================
        
                    st.markdown(
                        """
                        <div style="
                            background-color:#FFFFFF;
                            border:1px solid #D9E2F2;
                            border-radius:10px;
                            padding:12px 14px;
                            margin-top:10px;
                            font-size:13px;
                            color:#1F2937;
                        ">
                            <b>图例：</b>
                            <span style="color:#16A34A;font-weight:800;">● 高投资评分</span>
                            &nbsp;&nbsp;
                            <span style="color:#FACC15;font-weight:800;">● 中等评分</span>
                            &nbsp;&nbsp;
                            <span style="color:#F59E0B;font-weight:800;">● 偏低评分</span>
                            &nbsp;&nbsp;
                            <span style="color:#DC2626;font-weight:800;">● 低评分/高风险</span>
                            &nbsp;&nbsp;
                            圆点越大代表年产能越高。
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with insight_col:
                    st.markdown(
                        """
                        <div style="
                            background:#FFFFFF;
                            border:1px solid #D9E2F2;
                            border-left:7px solid #0035A8;
                            border-radius:12px;
                            padding:26px 28px;
                            min-height:435px;
                            box-shadow:0 3px 10px rgba(0, 58, 140, 0.06);
                            color:#1F2937;
                        ">
                            <h4 style="
                                margin:0 0 28px 0;
                                color:#1F2937;
                                font-size:22px;
                                font-weight:900;
                            ">资源配置洞察</h4>
                            <div style="font-size:16px;line-height:1.75;padding:0 0 16px 0;border-bottom:1px solid #E5E7EB;">
                                <b>南美盐湖：</b>低成本长期权益资源，适合优先锁定包销和股权机会。
                            </div>
                            <div style="font-size:16px;line-height:1.75;padding:16px 0;border-bottom:1px solid #E5E7EB;">
                                <b>澳洲锂辉石：</b>供应稳定性强，是短中期资源安全底座。
                            </div>
                            <div style="font-size:16px;line-height:1.75;padding:16px 0;border-bottom:1px solid #E5E7EB;">
                                <b>非洲资源：</b>具备增量弹性，但需重点关注出口限制、本地冶炼政策和物流风险。
                            </div>
                            <div style="font-size:16px;line-height:1.75;padding:16px 0;border-bottom:1px solid #E5E7EB;">
                                <b>中国云母：</b>更多体现边际成本和价格弹性，不宜作为优先锁定方向。
                            </div>
                            <div style="font-size:16px;line-height:1.75;padding:16px 0 0 0;">
                                <b>配置建议：</b>优先关注低成本盐湖、头部锂辉石和具备本地加工能力的资源权益。
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    
                # =========================
                # 右侧/下方资源集中度表
                # =========================
                with st.expander("查看地图项目明细"):
                    display_cols = [
                        "name",
                        "strategy_pool",
                        "country",
                        "resource_type",
                        "status",
                        "annual_capacity",
                        "aisc_cost",
                        "adjusted_aisc",
                        "risk_score",
                        "investment_score",
                        "recommended_action",
                    ]
    
                    display_cols = [
                        col for col in display_cols
                        if col in map_df.columns
                    ]
    
                    map_display_df = map_df[display_cols].copy()
    
                    column_rename_map = {
                        "name": "项目名称",
                        "strategy_pool": "战略分类",
                        "country": "国家",
                        "resource_type": "资源类型",
                        "status": "项目状态",
                        "annual_capacity": "年产能",
                        "aisc_cost": "基础AISC",
                        "adjusted_aisc": "政策调整后AISC",
                        "risk_score": "风险评分",
                        "investment_score": "投资评分",
                        "recommended_action": "建议动作",
                    }
    
                    map_display_df = map_display_df.rename(
                        columns=column_rename_map
                    )
    
                    if "国家" in map_display_df.columns:
                        country_map = {
                            "Chile": "智利",
                            "Argentina": "阿根廷",
                            "Australia": "澳大利亚",
                            "China": "中国",
                            "United States": "美国",
                            "Canada": "加拿大",
                            "Brazil": "巴西",
                            "Zimbabwe": "津巴布韦",
                            "Mali": "马里",
                            "Ghana": "加纳",
                        }
    
                        map_display_df["国家"] = map_display_df["国家"].replace(
                            country_map
                        )
    
                    if "资源类型" in map_display_df.columns:
                        resource_type_map = {
                            "brine": "盐湖",
                            "spodumene": "锂辉石",
                            "lepidolite": "锂云母",
                            "clay": "锂粘土",
                            "recycling": "回收",
                            "Unknown": "未知",
                        }
    
                        map_display_df["资源类型"] = map_display_df["资源类型"].replace(
                            resource_type_map
                        )
    
                    if "项目状态" in map_display_df.columns:
                        status_map = {
                            "Operating": "在产",
                            "Developing": "开发中",
                            "Construction": "建设中",
                            "Planned": "规划中",
                            "Suspended": "暂停",
                            "Unknown": "未知",
                        }
    
                        map_display_df["项目状态"] = map_display_df["项目状态"].replace(
                            status_map
                        )
    
                    if "建议动作" in map_display_df.columns:
                        action_map = {
                            "Prioritize investment": "优先投资",
                            "Strategic offtake": "战略包销",
                            "Monitor": "持续观察",
                            "Avoid": "暂缓进入",
                            "N/A": "暂无",
                        }
    
                        map_display_df["建议动作"] = map_display_df["建议动作"].replace(
                            action_map
                        )
    
                    for col in ["年产能", "基础AISC", "政策调整后AISC"]:
                        if col in map_display_df.columns:
                            map_display_df[col] = pd.to_numeric(
                                map_display_df[col],
                                errors="coerce",
                            ).round(0)
    
                    for col in ["风险评分", "投资评分"]:
                        if col in map_display_df.columns:
                            map_display_df[col] = pd.to_numeric(
                                map_display_df[col],
                                errors="coerce",
                            ).round(2)
    
                    if "投资评分" in map_display_df.columns:
                        map_display_df = map_display_df.sort_values(
                            "投资评分",
                            ascending=False,
                        )
    
                    st.dataframe(
                        map_display_df,
                        width="stretch",
                        hide_index=True,
                    )
                st.markdown("#### 战略资源池汇总")
    
                strategy_summary_df = (
                    map_df
                    .groupby("strategy_pool", as_index=False)
                    .agg(
                        项目数量=("name", "count"),
                        年产能合计=("annual_capacity", "sum"),
                        平均投资评分=("investment_score", "mean"),
                        平均风险评分=("risk_score", "mean"),
                        平均调整后AISC=("adjusted_aisc", "mean"),
                    )
                )
    
                strategy_summary_df = strategy_summary_df.rename(
                    columns={
                        "strategy_pool": "战略资源池",
                    }
                )
    
                for col in ["年产能合计", "平均调整后AISC"]:
                    if col in strategy_summary_df.columns:
                        strategy_summary_df[col] = pd.to_numeric(
                            strategy_summary_df[col],
                            errors="coerce",
                        ).round(0)
    
                for col in ["平均投资评分", "平均风险评分"]:
                    if col in strategy_summary_df.columns:
                        strategy_summary_df[col] = pd.to_numeric(
                            strategy_summary_df[col],
                            errors="coerce",
                        ).round(2)
    
                st.dataframe(
                    strategy_summary_df.sort_values("平均投资评分", ascending=False),
                    width="stretch",
                    hide_index=True,
                )
    
        section_close()


    # =========================
    # 05 全球AISC成本曲线与90%成本支撑
    # =========================

    def render_section_05_aisc_curve():
        section_header("05", "战略AISC / 资源可获得成本模型")
        section_open()

        st.markdown(
            """
            <div class="insight-box">
            <b>战略AISC口径：</b>
            本模块同时展示项目原始AISC、现有调整后AISC与战略AISC。原始AISC反映项目物理成本，
            现有调整后AISC反映能源、运输、运营和既有风险修正，战略AISC进一步结合IEA锂相关政策风险，
            用于评估CATL视角下的资源可获得成本。战略AISC不是对项目真实现金成本的改写，而是资源投资决策口径。
            </div>
            """,
            unsafe_allow_html=True,
        )

        if project_strategic_aisc_df.empty:
            st.info("战略AISC数据待接入，请先运行：\npython policy_risk_engine_v2.py\npython aisc_policy_bridge_v2.py")
            section_close()
            return

        strategic_df = project_strategic_aisc_df.copy()

        def first_existing_column(df, candidates):
            for column in candidates:
                if column in df.columns:
                    return column
            return None

        unit_audit_records = []

        def to_wan_series(series, source_col=""):
            """统一把 AISC / 溢价字段转换为“万元/吨 LCE”。
            规则：
            - 字段名含 _wan 且中位数 <= 100：视为已是万元/吨；
            - 字段名不含 _wan 或数值中位数 > 100：视为元/吨，除以 10000；
            - 转换后保留单位审计记录，避免图表出现“元/吨”和“万元/吨”混用。
            """
            numeric = pd.to_numeric(series, errors="coerce")
            positive = numeric[numeric > 0]
            source_name = str(source_col or "")
            source_median = float(positive.median()) if not positive.empty else 0.0

            if positive.empty:
                conversion = "无有效正数"
                converted = numeric
            elif source_name.endswith("_wan") and source_median <= 100:
                conversion = "已是万元/吨，未转换"
                converted = numeric
            elif source_median > 100:
                conversion = "按元/吨转万元/吨，除以10000"
                converted = numeric / 10000
            else:
                conversion = "按万元/吨处理，未转换"
                converted = numeric

            converted_positive = converted[converted > 0]
            converted_median = float(converted_positive.median()) if not converted_positive.empty else 0.0
            unit_audit_records.append(
                {
                    "字段": source_name or "unknown",
                    "原始正数中位数": round(source_median, 4),
                    "转换规则": conversion,
                    "绘图中位数（万元/吨）": round(converted_median, 4),
                }
            )
            return converted

        project_col = first_existing_column(strategic_df, ["project", "project_name", "name"])
        company_col = first_existing_column(strategic_df, ["company", "owner"])
        country_col = first_existing_column(strategic_df, ["country"])
        resource_col = first_existing_column(strategic_df, ["resource_type"])
        if project_col is None:
            strategic_df["project"] = strategic_df.index.astype(str)
            project_col = "project"
        if company_col is None:
            strategic_df["company"] = ""
            company_col = "company"
        if country_col is None:
            strategic_df["country"] = ""
            country_col = "country"
        if resource_col is None:
            strategic_df["resource_type"] = ""
            resource_col = "resource_type"

        base_col = first_existing_column(strategic_df, ["base_aisc_wan", "aisc_cost"])
        adjusted_col = first_existing_column(strategic_df, ["adjusted_aisc_wan", "adjusted_aisc", "realtime_aisc", "delivered_cost"])
        strategic_col = first_existing_column(strategic_df, ["strategic_aisc_wan"])
        if base_col is None or adjusted_col is None or strategic_col is None:
            st.warning("project_strategic_aisc_v2.csv 缺少 AISC 口径字段，无法绘制战略AISC曲线。")
            section_close()
            return

        strategic_df["base_aisc_plot"] = to_wan_series(strategic_df[base_col], base_col)
        strategic_df["adjusted_aisc_plot"] = to_wan_series(strategic_df[adjusted_col], adjusted_col)
        strategic_df["strategic_aisc_plot"] = to_wan_series(strategic_df[strategic_col], strategic_col)
        strategic_df["policy_risk_premium_pct_plot"] = pd.to_numeric(strategic_df.get("policy_risk_premium_pct", pd.Series(0, index=strategic_df.index)), errors="coerce").fillna(0)
        strategic_df["policy_risk_premium_wan_plot"] = to_wan_series(strategic_df.get("policy_risk_premium_wan", pd.Series(0, index=strategic_df.index)), "policy_risk_premium_wan").fillna(0)
        strategic_df["policy_risk_score_plot"] = pd.to_numeric(strategic_df.get("policy_risk_score", strategic_df.get("risk_score", pd.Series(0, index=strategic_df.index))), errors="coerce").fillna(0)
        strategic_df["is_investable_plot"] = strategic_df.get("is_investable", pd.Series("", index=strategic_df.index)).fillna("").astype(str)
        strategic_df["adjustment_reason_plot"] = strategic_df.get("adjustment_reason", pd.Series("", index=strategic_df.index)).fillna("").astype(str)

        valid_df = strategic_df.dropna(subset=["base_aisc_plot", "adjusted_aisc_plot", "strategic_aisc_plot"]).copy()
        valid_df = valid_df[(valid_df["base_aisc_plot"] > 0) & (valid_df["adjusted_aisc_plot"] > 0) & (valid_df["strategic_aisc_plot"] > 0)].copy()
        if valid_df.empty:
            st.warning("project_strategic_aisc_v2.csv 中没有可用于绘图的有效 AISC 数据。")
            section_close()
            return

        unit_audit_df = pd.DataFrame(unit_audit_records)
        if not unit_audit_df.empty:
            with st.expander("AISC单位校验（元/吨 → 万元/吨）", expanded=False):
                st.caption("本表用于确认原始AISC、调整后AISC、战略AISC与政策风险溢价均已统一为万元/吨 LCE 后再绘图。")
                st.dataframe(unit_audit_df.drop_duplicates(subset=["字段"], keep="last"), width="stretch", hide_index=True)

        project_count = valid_df[project_col].nunique() if project_col in valid_df.columns else len(valid_df)
        avg_premium = valid_df["policy_risk_premium_pct_plot"].mean()
        strategic_p90 = valid_df["strategic_aisc_plot"].quantile(0.90)
        core_count = int((valid_df["is_investable_plot"] == "核心配置").sum())

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            compact_metric_card("项目数量", f"{project_count:.0f}", "战略AISC项目样本")
        with k2:
            compact_metric_card("平均政策风险溢价", f"{avg_premium:.1%}", "基于 bridge 输出字段")
        with k3:
            compact_metric_card("战略AISC 90分位", f"{strategic_p90:.2f} 万元/吨", "资源可获得成本上沿")
        with k4:
            compact_metric_card("核心配置项目数量", f"{core_count}", "is_investable=核心配置")

        st.markdown("#### 排序口径")
        cost_basis = st.radio("排序口径", ["原始AISC", "调整后AISC", "战略AISC"], horizontal=True, key="strategic_aisc_cost_basis")
        st.caption("说明：堆叠柱始终展示战略AISC构成，按钮仅用于切换横轴项目排序基准。")
        sort_col = {"原始AISC": "base_aisc_plot", "调整后AISC": "adjusted_aisc_plot", "战略AISC": "strategic_aisc_plot"}[cost_basis]
        chart_df = valid_df.sort_values([country_col, sort_col], ascending=[True, True]).reset_index(drop=True).copy()

        def shorten_name(value, max_len=11):
            value = str(value)
            return value if len(value) <= max_len else value[:max_len] + "…"

        chart_df["project_display"] = chart_df[project_col].astype(str).apply(shorten_name)
        chart_df["project_full"] = chart_df[project_col].astype(str)
        chart_df["company_display"] = chart_df[company_col].astype(str)
        chart_df["country_display"] = chart_df[country_col].astype(str)
        chart_df["resource_display"] = chart_df[resource_col].astype(str)
        chart_df["base_component_wan"] = chart_df["base_aisc_plot"]
        chart_df["operational_adjustment_wan"] = (
            chart_df["adjusted_aisc_plot"] - chart_df["base_aisc_plot"]
        ).clip(lower=0)
        chart_df["strategic_risk_premium_wan"] = (
            chart_df["strategic_aisc_plot"] - chart_df["adjusted_aisc_plot"]
        ).clip(lower=0)
        hover_columns = [
            "project_full",
            "company_display",
            "country_display",
            "resource_display",
            "base_aisc_plot",
            "adjusted_aisc_plot",
            "strategic_aisc_plot",
            "policy_risk_premium_pct_plot",
            "policy_risk_score_plot",
            "is_investable_plot",
            "adjustment_reason_plot",
            "operational_adjustment_wan",
            "strategic_risk_premium_wan",
        ]
        aisc_hovertemplate = (
            "项目：%{customdata[0]}<br>公司：%{customdata[1]}<br>"
            "国家：%{customdata[2]}<br>资源类型：%{customdata[3]}<br>"
            "原始AISC：%{customdata[4]:.2f} 万元/吨<br>"
            "运营调整：%{customdata[11]:.2f} 万元/吨<br>"
            "调整后AISC：%{customdata[5]:.2f} 万元/吨<br>"
            "政策/战略风险溢价：%{customdata[12]:.2f} 万元/吨<br>"
            "战略AISC：%{customdata[6]:.2f} 万元/吨<br>"
            "政策风险溢价：%{customdata[7]:.1%}<br>"
            "政策风险评分：%{customdata[8]:.2f}<br>"
            "投资判断：%{customdata[9]}<br>"
            "调整原因：%{customdata[10]}<extra></extra>"
        )

        fig_aisc = go.Figure()
        fig_aisc.add_trace(
            go.Bar(
                x=chart_df["project_display"],
                y=chart_df["base_component_wan"],
                name="原始AISC",
                marker=dict(color=CATL_BLUE, line=dict(color="#FFFFFF", width=0.8)),
                customdata=chart_df[hover_columns].to_numpy(),
                hovertemplate=aisc_hovertemplate,
            )
        )
        fig_aisc.add_trace(
            go.Bar(
                x=chart_df["project_display"],
                y=chart_df["operational_adjustment_wan"],
                name="运营调整",
                marker=dict(color=NEUTRAL_LIGHT, line=dict(color="#FFFFFF", width=0.8)),
                customdata=chart_df[hover_columns].to_numpy(),
                hovertemplate=aisc_hovertemplate,
            )
        )
        fig_aisc.add_trace(
            go.Bar(
                x=chart_df["project_display"],
                y=chart_df["strategic_risk_premium_wan"],
                name="政策/战略风险溢价",
                marker=dict(color=CORAL, line=dict(color="#FFFFFF", width=0.8)),
                customdata=chart_df[hover_columns].to_numpy(),
                hovertemplate=aisc_hovertemplate,
            )
        )
        strategic_p90 = chart_df["strategic_aisc_plot"].quantile(0.90)
        fig_aisc.add_trace(go.Scatter(x=chart_df["project_display"], y=[strategic_p90] * len(chart_df), mode="lines", name=f"项目库90%战略AISC线 {strategic_p90:.2f}万", line=dict(color="#E2BE33", width=2.5, dash="dash"), hoverinfo="skip"))
        weighted_avg_strategic_aisc = None
        capacity_candidates = [
            "effective_capacity",
            "annual_capacity",
            "capacity_lce",
            "annual_capacity_lce",
            "capacity",
        ]
        capacity_col = next((c for c in capacity_candidates if c in chart_df.columns), None)
        if capacity_col:
            capacity_values = pd.to_numeric(chart_df[capacity_col], errors="coerce")
            valid_capacity_mask = capacity_values.notna() & (capacity_values > 0)
            if valid_capacity_mask.any() and capacity_values[valid_capacity_mask].sum() > 0:
                weighted_avg_strategic_aisc = (
                    chart_df.loc[valid_capacity_mask, "strategic_aisc_plot"]
                    * capacity_values[valid_capacity_mask]
                ).sum() / capacity_values[valid_capacity_mask].sum()
                fig_aisc.add_trace(
                    go.Scatter(
                        x=chart_df["project_display"],
                        y=[weighted_avg_strategic_aisc] * len(chart_df),
                        mode="lines",
                        name=f"产能加权平均战略AISC {weighted_avg_strategic_aisc:.2f}万",
                        line=dict(color="#4B5563", width=2.5, dash="longdash"),
                        hoverinfo="skip",
                    )
                )
        country_abbrev_map = {
            "Argentina": "ARG",
            "Australia": "AUS",
            "Brazil": "BRA",
            "Canada": "CAN",
            "Chile": "CHL",
            "Czech Republic": "CZE",
            "Democratic Republic of Congo": "DRC",
            "Germany": "GER",
            "Ghana": "GHA",
            "Mali": "MLI",
            "Portugal": "POR",
            "United States": "US",
            "Zimbabwe": "ZWE",
        }

        group_meta = []
        for country_name, group_df in chart_df.groupby(country_col, sort=False):
            group_meta.append((country_name, int(group_df.index[0]), int(group_df.index[-1])))
        group_top_y = max(chart_df["strategic_aisc_plot"].max(), strategic_p90, PAPER_PRICE_CENTER_WAN)
        if weighted_avg_strategic_aisc is not None:
            group_top_y = max(group_top_y, weighted_avg_strategic_aisc)
        label_y = group_top_y * 1.06
        for idx, (country_name, start_idx, end_idx) in enumerate(group_meta):
            mid_idx = (start_idx + end_idx) // 2
            fig_aisc.add_annotation(
                x=chart_df["project_display"].iloc[mid_idx],
                y=label_y,
                text=f"<b>{country_abbrev_map.get(str(country_name), str(country_name))}</b>",
                showarrow=False,
                font=dict(color="#000000", size=15, family="Microsoft YaHei, SimHei, Arial"),
                xanchor="center",
                yanchor="bottom",
            )
            if idx < len(group_meta) - 1:
                boundary_x = chart_df["project_display"].iloc[end_idx]
                fig_aisc.add_vline(
                    x=boundary_x,
                    line=dict(color="#E5E7EB", width=1, dash="dot"),
                    layer="below",
                )
        fig_aisc.add_trace(
            go.Scatter(
                x=chart_df["project_display"],
                y=[PAPER_PRICE_CENTER_WAN] * len(chart_df),
                mode="lines",
                name=f"当前LCE价格线 {PAPER_PRICE_CENTER_WAN:.1f}万",
                line=dict(
                    color=TEAL,
                    width=2.5,
                    dash="dot",
                ),
                hoverinfo="skip",
            )
        )
        fig_aisc.update_layout(
            title=dict(
                text="全球锂项目战略AISC构成：从矿山成本到资源可获得成本",
                font=dict(
                    color=CATL_BLUE,
                    size=22,
                ),
            ),
            xaxis_title=f"锂资源项目（按{cost_basis}升序）", yaxis_title="AISC / 战略可获得成本（万元/吨 LCE）", height=680,
            plot_bgcolor="white", paper_bgcolor="white", hovermode="closest", barmode="stack", margin=dict(l=30, r=40, t=135, b=170),
            font=dict(color=TEXT_DARK, size=13, family="Microsoft YaHei, SimHei, Arial"),
            legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0, font=dict(color=TEXT_DARK, size=12), bgcolor="#FFFFFF", bordercolor=BORDER, borderwidth=1),
            bargap=0.18,
        )
        fig_aisc.update_xaxes(tickangle=-55, showgrid=False, color=TEXT_DARK, title_font=dict(color=TEXT_DARK, size=14), automargin=True)
        reference_values = [strategic_p90, PAPER_PRICE_CENTER_WAN]
        if weighted_avg_strategic_aisc is not None:
            reference_values.append(weighted_avg_strategic_aisc)
        y_max = max(chart_df[["base_aisc_plot", "adjusted_aisc_plot", "strategic_aisc_plot"]].max().max(), *reference_values, group_top_y * 1.06) * 1.25
        fig_aisc.update_yaxes(range=[0, y_max], gridcolor="#E5E7EB", zeroline=False, color=TEXT_DARK, title_font=dict(color=TEXT_DARK, size=14))
        st.plotly_chart(fig_aisc, width="stretch")
        st.caption(
            "判读逻辑：堆叠柱总高度代表战略AISC；深蓝部分为原始AISC，灰色部分为运营调整，"
            "橙色部分为政策/战略风险溢价。项目库90%战略AISC线用于识别边际高成本项目；"
            "产能加权平均战略AISC线代表项目组合成本中枢；当前LCE价格线用于判断价格安全垫。"
        )

        st.markdown("#### 政策风险溢价最高的项目 Top 10")
        top_df = valid_df.sort_values("policy_risk_premium_wan_plot", ascending=False).head(10).copy()
        top_df["项目"] = top_df[project_col]
        top_df["国家"] = top_df[country_col]
        top_df["原始AISC（万元/吨）"] = top_df["base_aisc_plot"].round(2)
        top_df["政策风险溢价（万元/吨）"] = top_df["policy_risk_premium_wan_plot"].round(2)
        top_df["战略AISC（万元/吨）"] = top_df["strategic_aisc_plot"].round(2)
        top_df["政策风险溢价"] = top_df["policy_risk_premium_pct_plot"].map(lambda x: f"{x:.1%}")
        top_df["投资判断"] = top_df["is_investable_plot"]
        top_df["调整原因"] = top_df["adjustment_reason_plot"]
        st.dataframe(top_df[["项目", "国家", "原始AISC（万元/吨）", "政策风险溢价（万元/吨）", "战略AISC（万元/吨）", "政策风险溢价", "投资判断", "调整原因"]], width="stretch", hide_index=True)

        st.markdown(
            """
            <div class="insight-box">
            <b>管理层解读：</b>
            本图不再单纯比较三条AISC曲线，
            而是拆解每个项目的战略AISC构成。

            深蓝色代表原始矿山成本；
            灰色代表运营、运输、能源等现实调整；
            橙色代表政策风险与资源可获得性溢价。

            柱体总高度越高，
            说明项目实际资源获取成本越高。

            黄色虚线为项目库90%战略AISC线；
            绿色虚线为当前LCE价格线。
            </div>
            """,
            unsafe_allow_html=True,
        )

        section_close()


    def render_section_06_resource_portfolio_allocation():
        section_header("06", "CATL资源锁量策略与样本观察池")
        section_open()

        portfolio_df = project_strategic_aisc_df.copy()

        if portfolio_df.empty:
            st.info("暂无 project_strategic_aisc_v2.csv，暂无法生成 CATL资源锁量策略与样本观察池。")
            section_close()
            return

        investment_rebalance_df = load_csv("investment_recommendations_v2.csv")
        if not investment_rebalance_df.empty and "project" in investment_rebalance_df.columns:
            rebalance_cols = [
                col for col in [
                    "project",
                    "strategic_investment_score",
                    "investment_tier",
                    "recommended_action_v2",
                    "strategy_detail_v2",
                    "key_risk_note",
                ]
                if col in investment_rebalance_df.columns
            ]
            portfolio_df = portfolio_df.merge(
                investment_rebalance_df[rebalance_cols],
                on="project",
                how="left",
                suffixes=("", "_rebalance"),
            )

        for col, default in [
            ("annual_capacity", 0),
            ("strategic_aisc_wan", 0),
            ("policy_risk_premium_wan", 0),
            ("price_margin_wan", 0),
            ("strategic_investment_score", 50),
        ]:
            if col not in portfolio_df.columns:
                portfolio_df[col] = default
            portfolio_df[col] = pd.to_numeric(portfolio_df[col], errors="coerce").fillna(default)

        if "resource_type" not in portfolio_df.columns:
            portfolio_df["resource_type"] = "Unknown"
        if "country" not in portfolio_df.columns:
            portfolio_df["country"] = "Unknown"
        if "project_name" not in portfolio_df.columns:
            portfolio_df["project_name"] = portfolio_df.get("project", portfolio_df.get("name", "Unknown"))
        if "investment_tier" not in portfolio_df.columns:
            portfolio_df["investment_tier"] = "未分层"
        if "recommended_action_v2" not in portfolio_df.columns:
            portfolio_df["recommended_action_v2"] = "持续跟踪"
        if "key_risk_note" not in portfolio_df.columns:
            portfolio_df["key_risk_note"] = portfolio_df.get("adjustment_reason", "")

        portfolio_df = portfolio_df[portfolio_df["strategic_aisc_wan"] > 0].copy()
        if portfolio_df.empty:
            st.info("暂无有效战略AISC项目数据，暂无法生成 CATL资源锁量策略与样本观察池。")
            section_close()
            return

        def portfolio_resource_bucket(resource_type):
            resource_type = str(resource_type).lower()
            if "brine" in resource_type or "盐湖" in resource_type:
                return "盐湖"
            if "spodumene" in resource_type or "锂辉石" in resource_type:
                return "锂辉石"
            if "lepidolite" in resource_type or "mica" in resource_type or "zinnwaldite" in resource_type or "云母" in resource_type:
                return "云母"
            return "黏土 / 其他"

        resource_value_map = {
            "锂辉石": 1.00,
            "盐湖": 0.90,
            "云母": 0.55,
            "黏土 / 其他": 0.40,
        }

        portfolio_df["portfolio_resource_type"] = portfolio_df["resource_type"].apply(portfolio_resource_bucket)
        portfolio_df["annual_capacity"] = portfolio_df["annual_capacity"].clip(lower=0)

        current_lce_price_wan = (
            pd.to_numeric(portfolio_df.get("current_lce_price_wan", pd.Series(dtype=float)), errors="coerce")
            .dropna()
            .iloc[0]
            if "current_lce_price_wan" in portfolio_df.columns
            and not pd.to_numeric(portfolio_df["current_lce_price_wan"], errors="coerce").dropna().empty
            else PAPER_PRICE_CENTER_WAN
        )

        cap_max = max(float(portfolio_df["annual_capacity"].max()), 1.0)
        premium_ceiling = max(float(portfolio_df["policy_risk_premium_wan"].max()), 1.0)
        score_max = max(float(portfolio_df["strategic_investment_score"].max()), 1.0)

        portfolio_df["cost_safety_score"] = (portfolio_df["price_margin_wan"] / max(current_lce_price_wan, 1.0)).clip(lower=0, upper=1)
        portfolio_df["capacity_delivery_score"] = (portfolio_df["annual_capacity"] / cap_max).clip(lower=0, upper=1)
        portfolio_df["policy_access_score"] = (1 - portfolio_df["policy_risk_premium_wan"] / premium_ceiling).clip(lower=0, upper=1)
        portfolio_df["resource_value_score"] = portfolio_df["portfolio_resource_type"].map(resource_value_map).fillna(0.50)
        portfolio_df["project_readiness_score"] = (portfolio_df["strategic_investment_score"] / score_max).clip(lower=0, upper=1)

        portfolio_df["catl_lock_priority_score"] = (
            portfolio_df["cost_safety_score"] * 0.30
            + portfolio_df["capacity_delivery_score"] * 0.25
            + portfolio_df["policy_access_score"] * 0.20
            + portfolio_df["resource_value_score"] * 0.15
            + portfolio_df["project_readiness_score"] * 0.10
        ) * 100

        def star_label(score):
            if score >= 85:
                return "★★★★★"
            if score >= 70:
                return "★★★★☆"
            if score >= 55:
                return "★★★☆☆"
            if score >= 40:
                return "★★☆☆☆"
            return "★☆☆☆☆"

        portfolio_df["sample_priority_star"] = portfolio_df["catl_lock_priority_score"].apply(star_label)

        def risk_label(x):
            if x > 0.70:
                return "高"
            if x > 0.30:
                return "较高"
            if x > 0.05:
                return "中"
            return "低"

        portfolio_df["risk_review_level"] = portfolio_df["policy_risk_premium_wan"].apply(risk_label)

        def catl_action(row):
            if row["price_margin_wan"] > 0 and row["policy_risk_premium_wan"] <= 0.30 and row["annual_capacity"] > 0:
                return "长协 / 包销评估"
            if row["price_margin_wan"] > 0 and row["policy_risk_premium_wan"] > 0.30:
                return "政策复核 / 谈判保护"
            if row["catl_lock_priority_score"] >= 55:
                return "联合开发评估"
            if row["policy_risk_premium_wan"] > 0.70 or row["price_margin_wan"] < 0:
                return "风险观察"
            return "持续跟踪"

        portfolio_df["catl_action_guidance"] = portfolio_df.apply(catl_action, axis=1)

        portfolio_df["priority_weight_base"] = (
            portfolio_df["annual_capacity"].where(portfolio_df["annual_capacity"] > 0, 1)
            * portfolio_df["catl_lock_priority_score"].clip(lower=1)
            / portfolio_df["strategic_aisc_wan"]
        )

        allocation_df = (
            portfolio_df.groupby("portfolio_resource_type", as_index=False)
            .agg(weight_base=("priority_weight_base", "sum"))
        )
        total_weight_base = allocation_df["weight_base"].sum()
        if total_weight_base > 0:
            allocation_df["weight"] = allocation_df["weight_base"] / total_weight_base
        else:
            allocation_df["weight"] = 1 / max(len(allocation_df), 1)
        allocation_df = allocation_df.sort_values("weight", ascending=False)

        country_df = (
            portfolio_df.groupby("country", as_index=False)
            .agg(
                exposure_base=("priority_weight_base", "sum"),
                avg_policy_premium=("policy_risk_premium_wan", "mean"),
                sample_count=("project_name", "count"),
            )
        )
        max_exposure = max(float(country_df["exposure_base"].max()), 1.0)
        country_df["exposure_score"] = (country_df["exposure_base"] / max_exposure * 30).round(0)
        country_df["risk_flag"] = country_df["avg_policy_premium"].apply(lambda x: "较高风险" if x > 0.30 else "中低风险")
        country_df = country_df.sort_values(["exposure_score", "avg_policy_premium"], ascending=[False, False]).head(10)
        country_df = country_df.sort_values("exposure_score", ascending=True)

        capacity_weight = portfolio_df["annual_capacity"].clip(lower=0)
        if capacity_weight.sum() <= 0:
            capacity_weight = pd.Series(1, index=portfolio_df.index)
        weighted_strategic_aisc = (portfolio_df["strategic_aisc_wan"] * capacity_weight).sum() / capacity_weight.sum()
        covered_ratio = float((portfolio_df["price_margin_wan"] > 0).mean())
        policy_review_ratio = float((portfolio_df["policy_risk_premium_wan"] > 0.30).mean())
        top_resource = allocation_df.iloc[0]["portfolio_resource_type"] if not allocation_df.empty else "锂资源样本"

        st.markdown(
            """
            <div style="background:#F7FBFF;border:1px solid #B3D0F7;border-radius:12px;padding:12px 16px;margin-bottom:14px;">
                <div style="font-size:14px;color:#003A8C;font-weight:800;margin-bottom:4px;">说明</div>
                <div style="font-size:13px;color:#374151;line-height:1.6;">
                本模块基于33个全球锂资源观察样本进行结构化测算，仅用于评估资源类型、国家风险、成本安全垫与锁量优先级，
                不代表CATL实际持仓、投资计划或资产配置比例。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            compact_metric_card("锁量优先资源类型", top_resource, "样本优先级最高")
        with kpi2:
            compact_metric_card("样本加权可获得成本", f"{weighted_strategic_aisc:.2f}", "万元/吨 LCE")
        with kpi3:
            compact_metric_card("价格安全垫样本占比", f"{covered_ratio:.0%}", f"当前LCE {current_lce_price_wan:.1f} 万元/吨")
        with kpi4:
            compact_metric_card("政策风险需复核比例", f"{policy_review_ratio:.0%}", "出口限制 / 税费 / 审批")

        st.markdown(
            """
            <div class="insight-box">
            <b>CATL锁量优先级口径：</b>
            成本安全垫 × 30% ＋ 产能兑现能力 × 25% ＋ 政策可获得性 × 20% ＋ 资源类型战略价值 × 15% ＋ 项目进度确定性 × 10%。
            该口径用于把33个行业资源样本转化为锁量、采购、尽调和风险监控优先级，而不是模拟真实资产配置。
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart_left, chart_right = st.columns([1, 1])
        with chart_left:
            resource_bar_colors = ["#0035A8", "#1A5AD4", "#7DB3FF", "#CFE1FF"]
            fig_resource = go.Figure(
                go.Bar(
                    x=(allocation_df["weight"] * 100).round(1),
                    y=allocation_df["portfolio_resource_type"],
                    orientation="h",
                    marker=dict(
                        color=resource_bar_colors[: len(allocation_df)],
                        line=dict(color="rgba(0,0,0,0)", width=0),
                    ),
                    text=[f"{v:.0f}%" for v in allocation_df["weight"] * 100],
                    textposition="outside",
                    hovertemplate="资源类型：%{y}<br>样本优先级权重：%{x:.1f}%<extra></extra>",
                )
            )
            fig_resource.update_layout(
                title=dict(text="资源类型优先级结构｜样本测算", font=dict(color="#003A8C", size=20)),
                height=420,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                margin=dict(l=80, r=30, t=60, b=50),
                font=dict(color=TEXT_DARK, size=13),
                xaxis=dict(title="样本权重（%）", gridcolor="#E5E7EB", ticksuffix="%"),
                yaxis=dict(gridcolor="#E5E7EB", categoryorder="total ascending"),
                showlegend=False,
            )
            st.plotly_chart(fig_resource, width="stretch", key="catl_resource_structure_v15")

        with chart_right:
            low_risk_df = country_df[country_df["risk_flag"] == "中低风险"].copy()
            high_risk_df = country_df[country_df["risk_flag"] == "较高风险"].copy()

            fig_country = go.Figure()

            fig_country.add_trace(
                go.Bar(
                    x=low_risk_df["exposure_score"],
                    y=low_risk_df["country"],
                    orientation="h",
                    name="中低风险",
                    marker=dict(color="#1677FF", line=dict(color="rgba(0,0,0,0)", width=0)),
                    text=low_risk_df["exposure_score"].astype(int).astype(str),
                    textposition="outside",
                    hovertemplate="国家：%{y}<br>风险与供应暴露评分：%{x}<extra></extra>",
                )
            )

            fig_country.add_trace(
                go.Bar(
                    x=high_risk_df["exposure_score"],
                    y=high_risk_df["country"],
                    orientation="h",
                    name="较高风险",
                    marker=dict(color="#FF6B35", line=dict(color="rgba(0,0,0,0)", width=0)),
                    text=high_risk_df["exposure_score"].astype(int).astype(str),
                    textposition="outside",
                    hovertemplate="国家：%{y}<br>风险与供应暴露评分：%{x}<extra></extra>",
                )
            )

            fig_country.update_layout(
                title=dict(text="资源国风险与供应暴露｜样本池", font=dict(color="#003A8C", size=20)),
                height=460,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                margin=dict(l=90, r=40, t=60, b=90),
                font=dict(color=TEXT_DARK, size=13),
                xaxis=dict(title="风险与供应暴露评分（越高越高）", gridcolor="#E5E7EB"),
                yaxis=dict(gridcolor="#E5E7EB", categoryorder="total ascending"),
                barmode="overlay",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.18,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12, color=TEXT_MUTED),
                ),
            )
            st.plotly_chart(fig_country, width="stretch", key="catl_country_exposure_v15")

        st.markdown("#### 优先跟踪样本 Top 10")
        top_projects_df = portfolio_df.sort_values(
            ["catl_lock_priority_score", "price_margin_wan", "annual_capacity"],
            ascending=[False, False, False],
        ).head(10).copy()
        top_projects_display = pd.DataFrame(
            {
                "样本项目": top_projects_df["project_name"],
                "国家": top_projects_df["country"],
                "资源类型": top_projects_df["portfolio_resource_type"],
                "样本优先级": top_projects_df["sample_priority_star"],
                "战略可获得成本（万元/吨 LCE）": top_projects_df["strategic_aisc_wan"].round(2),
                "价格安全垫（万元/吨）": top_projects_df["price_margin_wan"].round(2),
                "需复核风险": top_projects_df["risk_review_level"],
                "CATL动作建议": top_projects_df["catl_action_guidance"],
            }
        )
        st.dataframe(top_projects_display, width="stretch", hide_index=True)

        active_lock_df = portfolio_df[(portfolio_df["price_margin_wan"] > 0) & (portfolio_df["policy_risk_premium_wan"] <= 0.30)].copy()
        negotiation_df = portfolio_df[(portfolio_df["price_margin_wan"] > 0) & (portfolio_df["policy_risk_premium_wan"] > 0.30)].copy()
        wait_df = portfolio_df[(portfolio_df["price_margin_wan"] <= 0.80) & (portfolio_df["catl_lock_priority_score"] >= 45) & (portfolio_df["policy_risk_premium_wan"] <= 0.70)].copy()
        warning_df = portfolio_df[(portfolio_df["price_margin_wan"] <= 0) | (portfolio_df["policy_risk_premium_wan"] > 0.70)].copy()

        def zone_card(title, color, bg, border, bullets):
            bullet_html = "".join([f"<li style='margin-bottom:6px;'>{item}</li>" for item in bullets])
            return f"""
                <div style='background:{bg};border:1px solid {border};border-radius:14px;padding:14px 16px;height:100%;'>
                    <div style='font-size:20px;font-weight:900;color:{color};margin-bottom:8px;'>{title}</div>
                    <ul style='padding-left:18px;margin:0;color:#374151;font-size:13px;line-height:1.65;'>{bullet_html}</ul>
                </div>
            """

        st.markdown("#### CATL动作分区")
        z1, z2, z3, z4 = st.columns(4)
        with z1:
            st.markdown(
                zone_card(
                    "主动锁量区（绿色）",
                    "#15803D",
                    "#F0FDF4",
                    "#BBF7D0",
                    [
                        f"低战略AISC + 低政策风险 + 有产能贡献（{len(active_lock_df)} 个样本）",
                        "CATL动作：长协谈判 / 包销协议 / 战略合作 / 少数股权投资评估",
                    ],
                ),
                unsafe_allow_html=True,
            )
        with z2:
            st.markdown(
                zone_card(
                    "结构性谈判区（蓝色）",
                    CATL_BLUE,
                    "#EFF6FF",
                    "#BFDBFE",
                    [
                        f"低成本但政策风险较高，需要更强保护条款（{len(negotiation_df)} 个样本）",
                        "CATL动作：强化价格调整机制 / 本地加工安排 / 政府关系复核",
                    ],
                ),
                unsafe_allow_html=True,
            )
        with z3:
            st.markdown(
                zone_card(
                    "观察等待区（橙色）",
                    "#C2410C",
                    "#FFF7ED",
                    "#FDBA74",
                    [
                        f"资源质量较好，但成本或项目进度暂不具备优势（{len(wait_df)} 个样本）",
                        "CATL动作：保持信息跟踪，不急于进入排他谈判",
                    ],
                ),
                unsafe_allow_html=True,
            )
        with z4:
            st.markdown(
                zone_card(
                    "风险预警区（红色）",
                    "#DC2626",
                    "#FEF2F2",
                    "#FECACA",
                    [
                        f"高成本 + 高政策风险 + 价格安全垫不足（{len(warning_df)} 个样本）",
                        "CATL动作：不作为近期锁量重点，仅作为边际供应观察",
                    ],
                ),
                unsafe_allow_html=True,
            )

        top_country = country_df.sort_values("exposure_score", ascending=False).iloc[0]["country"] if not country_df.empty else "样本资源国"
        st.markdown(
            f"""
            <div class="insight-box">
            <b>管理层解读：</b>
            这个模块并不是在模拟宁德时代真实的矿山资产配置。这里的33个项目是全球锂资源观察样本，
            通过战略AISC、政策风险溢价、产能规模与价格安全垫标准化排序，转化为锁量、采购、尽调与风险监控优先级。
            对宁德时代而言，当前更值得优先关注的资源类型是 <b>{top_resource}</b>，国家层面需重点复核 <b>{top_country}</b> 等高暴露资源国，
            核心不是“买哪个矿”，而是判断哪些样本更适合进入长协、包销、参股、联合开发或持续观察清单。
            </div>
            """,
            unsafe_allow_html=True,
        )

        section_close()


    # =========================
    # 06 政策冲击与新闻风险
    # =========================

    def render_section_06_policy_risk():
        section_header("06", "政策与新闻风险｜资源可获得性约束")
        section_open()

        policy_risk_data = load_policy_news_risk_data()
        missing_policy_data = any(value is None for value in policy_risk_data.values())
        if missing_policy_data:
            st.info("相关政策或新闻风险数据尚未生成，请先运行对应数据生成脚本。")

        scored_policy_table = policy_risk_data.get("policy_scored_table")
        timeline_events_df = policy_risk_data.get("policy_timeline_events")
        decomposed_risk_df = policy_risk_data.get("lithium_policy_decomposed_risk")
        strategic_aisc_policy_df = policy_risk_data.get("project_strategic_aisc_v2")
        raw_disclosure_policy_df = policy_risk_data.get("raw_disclosure_events")

        policy_display_value_map = {
            "unknown": "未分类",
            "tax_royalty": "税费与权利金",
            "environment_policy": "环保与水资源政策",
            "investment_restriction": "投资准入限制",
            "export_control": "出口管制",
            "local_processing": "本地加工要求",
            "strategic_plan": "战略规划",
            "subsidy_support": "补贴与产业支持",
            "state_control": "国家控股与参与",
            "recycling": "回收与循环体系",
            "permitting": "许可审批",
            "general_policy": "一般政策",
            "financing": "融资支持",
            "investment_access": "投资准入",
            "refining": "冶炼精炼",
            "project_approval": "项目审批",
            "processing": "加工环节",
            "environmental_permitting": "环保许可",
            "concentrate_export": "精矿出口",
            "ore_export": "矿石出口",
            "restrictive": "约束性",
            "supportive": "支持性",
            "neutral": "中性",
            "resource_update": "资源量更新",
            "project_update": "项目进展",
            "production_guidance": "产量指引",
            "financial_report": "财务报告",
            "policy_or_legal": "政策或法律事项",
            "offtake_or_mna": "包销或并购",
            "other": "其他",
            "company_ir": "公司投资者关系",
            "exchange_disclosure": "交易所公告",
            "google_news_backup": "新闻备份",
            "sec_filing": "SEC披露",
            "lithium": "锂",
            "spodumene": "锂辉石",
            "brine": "盐湖卤水",
            "clay": "黏土锂",
            "zinnwaldite": "锡瓦尔德石",
            "lithium carbonate": "碳酸锂",
            "battery minerals": "电池金属",
            "True": "是",
            "False": "否",
            True: "是",
            False: "否",
        }
        country_display_map = {
            "Argentina": "阿根廷",
            "Australia": "澳大利亚",
            "Brazil": "巴西",
            "Canada": "加拿大",
            "Chile": "智利",
            "China": "中国",
            "Czech Republic": "捷克",
            "Ghana": "加纳",
            "Global": "全球",
            "Mali": "马里",
            "Portugal": "葡萄牙",
            "United States": "美国",
            "Zimbabwe": "津巴布韦",
        }

        def localize_policy_value(value):
            if pd.isna(value):
                return ""
            return policy_display_value_map.get(value, policy_display_value_map.get(str(value), value))

        def localize_country_value(value):
            if pd.isna(value):
                return ""
            return country_display_map.get(value, country_display_map.get(str(value), value))

        policy_constraint = 0.0
        policy_premium_project_count = 0
        if strategic_aisc_policy_df is not None and not strategic_aisc_policy_df.empty:
            if "policy_risk_premium_wan" in strategic_aisc_policy_df.columns:
                premium_series = pd.to_numeric(
                    strategic_aisc_policy_df["policy_risk_premium_wan"],
                    errors="coerce",
                ).fillna(0)
                policy_premium_project_count = int((premium_series > 0).sum())
                if len(strategic_aisc_policy_df) > 0:
                    policy_constraint = policy_premium_project_count / len(strategic_aisc_policy_df)

        lithium_policy_event_count = 0
        high_constraint_policy_count = 0
        if scored_policy_table is not None and not scored_policy_table.empty:
            policy_text = scored_policy_table.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
            lithium_terms = "lithium|spodumene|brine|battery minerals"
            lithium_policy_event_count = int(policy_text.str.contains(lithium_terms, regex=True).sum())

            hard_constraint_mask = pd.Series(False, index=scored_policy_table.index)
            if "hard_constraint" in scored_policy_table.columns:
                hard_constraint_mask = (
                    scored_policy_table["hard_constraint"]
                    .fillna(False)
                    .astype(str)
                    .str.lower()
                    .isin(["true", "1", "yes", "y", "hard_constraint"])
                )

            risk_score_mask = pd.Series(False, index=scored_policy_table.index)
            if "risk_score" in scored_policy_table.columns:
                risk_score_mask = (
                    pd.to_numeric(scored_policy_table["risk_score"], errors="coerce").fillna(0)
                    >= 0.7
                )

            high_constraint_policy_count = int((hard_constraint_mask | risk_score_mask).sum())

        subsection_title(
            "政策风险总览 KPI",
            "以全球锂资源样本为口径，观察政策约束、锂相关事件和战略AISC传导范围。",
        )

        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.metric("Policy Constraint", f"{policy_constraint:.1%}", "全球锂资源样本")
        with kpi_cols[1]:
            st.metric("锂相关政策事件数", f"{lithium_policy_event_count:,}", "全球锂资源样本")
        with kpi_cols[2]:
            st.metric("高约束政策数量", f"{high_constraint_policy_count:,}", "硬约束或风险评分≥0.7")
        with kpi_cols[3]:
            st.metric("已传导至AISC项目数", f"{policy_premium_project_count:,}", "政策风险溢价>0")

        subsection_title(
            "政策风险如何进入战略AISC",
            "说明政策、新闻事件与资源可获得成本之间的传导关系。",
        )
        st.markdown(
            """
            <div class="insight-box">
            <b>政策风险如何进入战略AISC</b><br>
            政策与新闻风险先影响资源可获得性：出口限制、本地加工要求、税费上调、审批延迟和公司公告扰动，会改变项目可兑现供给、运输与合规成本、资本开支节奏和交付确定性。
            在本页框架中，这些约束被映射为政策风险溢价，并传导至战略AISC，用于解释全球锂资源样本的可获得成本变化，而不是判断具体企业已投资或已锁定项目状态。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "政策风险矩阵｜政策类型 × 供应链环节",
            "按政策类型和受影响环节聚合风险评分，识别约束集中区域。",
        )
        if scored_policy_table is not None and not scored_policy_table.empty:
            policy_type_candidates = [
                "policy_type",
                "policy_category",
                "announcement_type",
            ]
            stage_candidates = [
                "affected_stage",
                "stage",
                "catl_impact_dimension",
            ]
            risk_candidates = [
                "risk_score",
                "impact_score",
                "policy_score",
            ]

            policy_type_col = next(
                (col for col in policy_type_candidates if col in scored_policy_table.columns),
                None,
            )
            stage_col = next(
                (col for col in stage_candidates if col in scored_policy_table.columns),
                None,
            )
            risk_col = next(
                (col for col in risk_candidates if col in scored_policy_table.columns),
                None,
            )

            if policy_type_col and stage_col and risk_col:
                matrix_df = scored_policy_table[[policy_type_col, stage_col, risk_col]].copy()
                matrix_df[risk_col] = pd.to_numeric(matrix_df[risk_col], errors="coerce")
                matrix_df = matrix_df.dropna(subset=[policy_type_col, stage_col, risk_col])
                matrix_df[policy_type_col] = matrix_df[policy_type_col].map(localize_policy_value)
                matrix_df[stage_col] = matrix_df[stage_col].map(localize_policy_value)

                if not matrix_df.empty:
                    heatmap_df = (
                        matrix_df
                        .pivot_table(
                            index=policy_type_col,
                            columns=stage_col,
                            values=risk_col,
                            aggfunc="mean",
                            fill_value=0,
                        )
                        .sort_index()
                    )
                    fig_policy_matrix = px.imshow(
                        heatmap_df,
                        aspect="auto",
                        color_continuous_scale=[
                            [0.0, CATL_BLUE_PALE],
                            [0.55, "#FDE68A"],
                            [1.0, CORAL],
                        ],
                        labels=dict(x="供应链环节", y="政策类型", color="平均风险评分"),
                    )
                    plotly_enterprise_layout(
                        fig_policy_matrix,
                        title=None,
                        height=max(360, min(620, 120 + len(heatmap_df) * 34)),
                    )
                    fig_policy_matrix.update_layout(
                        coloraxis_colorbar=dict(title="风险评分"),
                        margin=dict(l=20, r=20, t=30, b=80),
                    )
                    fig_policy_matrix.update_xaxes(tickangle=-30)
                    st.plotly_chart(fig_policy_matrix, width="stretch")
                else:
                    st.info("政策风险矩阵数据不足，暂无法聚合展示。")
            else:
                st.info("政策风险矩阵字段不足，需包含政策类型、影响环节和风险评分字段。")
        else:
            st.info("相关政策或新闻风险数据尚未生成，请先运行对应数据生成脚本。")

        subsection_title(
            "重大政策与新闻事件 Top 10",
            "优先展示政策评分表，其次展示公司公告事件，最多10条。",
        )
        top_events_df = pd.DataFrame()
        if scored_policy_table is not None and not scored_policy_table.empty:
            policy_events_df = scored_policy_table.copy()
            policy_event_score_col = next(
                (col for col in ["risk_score", "impact_score", "policy_score"] if col in policy_events_df.columns),
                None,
            )
            if policy_event_score_col:
                policy_events_df["_event_sort_score"] = pd.to_numeric(
                    policy_events_df[policy_event_score_col],
                    errors="coerce",
                ).fillna(0)
                policy_events_df = policy_events_df.sort_values("_event_sort_score", ascending=False).head(10)
            else:
                policy_events_df = policy_events_df.head(10)

            top_events_df = pd.DataFrame(
                {
                    "日期": policy_events_df.get("time_start", policy_events_df.get("policy_year", "")),
                    "国家/公司": policy_events_df.get("country", "").map(localize_country_value),
                    "事件类型": policy_events_df.get("policy_type", policy_events_df.get("announcement_type", "")).map(localize_policy_value),
                    "标题": policy_events_df.get("policy_name", policy_events_df.get("title", "")),
                    "影响方向": policy_events_df.get("risk_direction", policy_events_df.get("impact_direction", "")).map(localize_policy_value),
                    "影响环节": policy_events_df.get("affected_stage", policy_events_df.get("stage", policy_events_df.get("catl_impact_dimension", ""))).map(localize_policy_value),
                    "风险等级": policy_events_df.get("risk_level", ""),
                    "资源策略含义": policy_events_df.get("summary_cn", policy_events_df.get("summary", policy_events_df.get("policy_name", ""))),
                }
            )
        elif raw_disclosure_policy_df is not None and not raw_disclosure_policy_df.empty:
            raw_events_df = raw_disclosure_policy_df.copy().head(10)
            top_events_df = pd.DataFrame(
                {
                    "日期": raw_events_df.get("published_at", ""),
                    "国家/公司": raw_events_df.get("company", raw_events_df.get("country", "")).map(localize_country_value),
                    "事件类型": raw_events_df.get("announcement_type", raw_events_df.get("filing_type", "")).map(localize_policy_value),
                    "标题": raw_events_df.get("title", ""),
                    "影响方向": raw_events_df.get("source_type", "").map(localize_policy_value),
                    "影响环节": raw_events_df.get("resource_type", "").map(localize_policy_value),
                    "风险等级": raw_events_df.get("is_price_sensitive", "").map(localize_policy_value),
                    "资源策略含义": raw_events_df.get("summary", ""),
                }
            )

        if not top_events_df.empty:
            st.dataframe(top_events_df.head(10), width="stretch", hide_index=True)
        else:
            st.info("重大政策与新闻事件数据不足，暂无法展示 Top 10。")

        subsection_title(
            "政策风险溢价 Top 10｜战略AISC传导",
            "按政策风险溢价从高到低展示已传导至战略AISC的全球锂资源样本。",
        )
        if strategic_aisc_policy_df is not None and not strategic_aisc_policy_df.empty:
            if "policy_risk_premium_wan" in strategic_aisc_policy_df.columns:
                premium_top_df = strategic_aisc_policy_df.copy()
                premium_top_df["policy_risk_premium_wan"] = pd.to_numeric(
                    premium_top_df["policy_risk_premium_wan"],
                    errors="coerce",
                ).fillna(0)
                premium_top_df = premium_top_df[premium_top_df["policy_risk_premium_wan"] > 0].copy()
                if not premium_top_df.empty:
                    premium_top_df = premium_top_df.sort_values(
                        "policy_risk_premium_wan",
                        ascending=False,
                    ).head(10)
                    premium_display_df = pd.DataFrame(
                        {
                            "项目": premium_top_df.get("project_name", premium_top_df.get("project", premium_top_df.get("name", ""))),
                            "国家": premium_top_df.get("country", "").map(localize_country_value),
                            "战略AISC": pd.to_numeric(
                                premium_top_df.get("strategic_aisc_wan", pd.Series(0, index=premium_top_df.index)),
                                errors="coerce",
                            ).round(2),
                            "政策风险溢价": premium_top_df["policy_risk_premium_wan"].round(2),
                            "政策溢价占比": pd.to_numeric(
                                premium_top_df.get("policy_risk_premium_pct", pd.Series(0, index=premium_top_df.index)),
                                errors="coerce",
                            ).map(lambda value: f"{value:.1%}"),
                            "风险说明": premium_top_df.get("adjustment_reason", premium_top_df.get("latest_event_title", "")),
                        }
                    )
                    st.dataframe(premium_display_df, width="stretch", hide_index=True)
                else:
                    st.info("暂无政策风险溢价大于0的全球锂资源样本。")
            else:
                st.info("project_strategic_aisc_v2.csv 缺少 policy_risk_premium_wan 字段。")
        else:
            st.info("相关政策或新闻风险数据尚未生成，请先运行对应数据生成脚本。")

        subsection_title(
            "数据说明",
            "解释页面口径、数据来源和边界。",
        )
        st.caption(
            "本页面用于解释政策约束如何影响资源可获得成本与战略AISC，不代表具体企业已投资或已锁定项目状态。"
        )
        available_files = {
            "policy_scored_table.csv": scored_policy_table,
            "policy_timeline_events.csv": timeline_events_df,
            "lithium_policy_decomposed_risk.csv": decomposed_risk_df,
            "project_strategic_aisc_v2.csv": strategic_aisc_policy_df,
            "raw_disclosure_events.csv": raw_disclosure_policy_df,
        }
        data_status_df = pd.DataFrame(
            [
                {
                    "数据文件": file_name,
                    "读取状态": "已读取" if data_frame is not None else "未生成",
                    "记录数": 0 if data_frame is None else len(data_frame),
                }
                for file_name, data_frame in available_files.items()
            ]
        )
        st.dataframe(data_status_df, width="stretch", hide_index=True)

        section_close()
        return
        
        if not policy_price_df.empty:
            row = policy_price_df.iloc[0]
            pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    
            with pc1:
                st.metric("供给损失比例", f"{safe_num(row.get('supply_loss_ratio', 0)):.2%}")
    
            with pc2:
                st.metric("AISC上移", format_wan(row.get("aisc_uplift", 0)))
    
            with pc3:
                st.metric("供给溢价", format_wan(row.get("supply_premium", 0)))
    
            with pc4:
                st.metric("成本溢价", format_wan(row.get("aisc_premium", 0)))
    
            with pc5:
                st.metric("政策后价格影响", format_wan(row.get("expected_lce_price", 0)))
        else:
            st.info("暂无 policy_price_impact.csv。请先运行 python main.py。")

        st.markdown("#### IEA关键矿产政策底库")
        if not critical_policy_df.empty:
            policy_display_cols = [
                "policy_id",
                "country",
                "region",
                "mineral",
                "policy_name",
                "policy_type",
                "policy_year",
                "effective_date",
                "status",
                "jurisdiction",
                "risk_level",
                "risk_direction",
                "affected_stage",
                "catl_impact_dimension",
                "summary_cn",
                "source",
                "source_url",
                "last_updated",
            ]
            policy_display_cols = [
                col for col in policy_display_cols
                if col in critical_policy_df.columns
            ]
            policy_display_df = critical_policy_df[policy_display_cols].copy()
            policy_display_df = policy_display_df.rename(
                columns={
                    "policy_id": "政策ID",
                    "country": "国家",
                    "region": "区域",
                    "mineral": "矿种",
                    "policy_name": "政策名称",
                    "policy_type": "政策类型",
                    "policy_year": "政策年份",
                    "effective_date": "生效日期",
                    "status": "状态",
                    "jurisdiction": "管辖层级",
                    "risk_level": "风险等级",
                    "risk_direction": "风险方向",
                    "affected_stage": "影响环节",
                    "catl_impact_dimension": "CATL影响维度",
                    "summary_cn": "中文摘要",
                    "source": "来源",
                    "source_url": "来源链接",
                    "last_updated": "更新时间",
                }
            )
            st.dataframe(
                policy_display_df,
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "政策样例来源：IEA Critical Minerals Policy Tracker；来源链接字段保留原始 source_url，便于后续核验。"
            )
        else:
            st.info("暂无 critical_minerals_policy_tracker.csv。")
    
        risk_left, risk_right = st.columns([1.2, 1])
    
        with risk_left:
            st.markdown("#### 国家新闻事件风险")
    
            if not event_risk_df.empty:
                if "country" in event_risk_df.columns and "event_risk_score" in event_risk_df.columns:
                    event_chart_df = event_risk_df.sort_values(
                        "event_risk_score",
                        ascending=False,
                    ).copy()
                    event_scores = pd.to_numeric(
                        event_chart_df["event_risk_score"],
                        errors="coerce",
                    )
                    event_colors = [
                        NEUTRAL_LIGHT if pd.isna(score)
                        else TEAL_LIGHT if score < 0.40
                        else CORAL_LIGHT if score < 0.70
                        else CORAL_DARK
                        for score in event_scores
                    ]
                    fig_event = px.bar(
                        event_chart_df,
                        x="country",
                        y="event_risk_score",
                        labels={"country": "国家", "event_risk_score": "事件风险评分"},
                    )
                    fig_event.update_traces(
                        marker=dict(
                            color=event_colors,
                            line=dict(color="#FFFFFF", width=1),
                        )
                    )
    
                    plotly_enterprise_layout(
                        fig_event,
                        title=None,
                        height=360,
                    )
    
                    st.plotly_chart(fig_event, width="stretch")
                else:
                    st.info("事件风险字段不足。")
            else:
                st.info("暂无国家新闻事件风险数据。")
    
        with risk_right:
            st.markdown("#### 风险明细")
    
            if not event_risk_df.empty:
                display_cols = [
                    col for col in [
                        "country",
                        "event_risk_score",
                        "event_count",
                        "negative_event_count",
                        "latest_event_title",
                    ]
                    if col in event_risk_df.columns
                ]
    
                if display_cols:
                    if "event_risk_score" in event_risk_df.columns:
                        display_df = event_risk_df[display_cols].sort_values(
                            "event_risk_score",
                            ascending=False,
                        )
                    else:
                        display_df = event_risk_df[display_cols]
    
                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=True,
                    )
                else:
                    st.info("暂无可展示风险字段。")
            else:
                st.info("暂无风险明细。")
    
        # =========================
        # 最新锂资源新闻事件表
        # 注意：这一段必须和 with risk_right 同级
        # =========================
    
        st.markdown("#### 最新锂资源新闻事件")
    
        if news_event_summary_df.empty:
            st.info("暂无 news_event_summary.csv。请先运行 python news_pipeline.py。")
        else:
            news_df = news_event_summary_df.copy()
    
            display_cols = [
                "published_at",
                "country",
                "event_type",
                "impact_direction",
                "risk_score",
                "supply_shock",
                "price_shock",
                "title_cn",
                "title",
                "source",
                "url",
            ]
    
            display_cols = [
                col for col in display_cols
                if col in news_df.columns
            ]
    
            news_display_df = news_df[display_cols].copy()
    
            # =========================
            # 去重：防止同一新闻反复出现
            # =========================
    
            if "title_cn" in news_display_df.columns:
                news_display_df = news_display_df.drop_duplicates(
                    subset=["title_cn"],
                    keep="first",
                )
            elif "title" in news_display_df.columns:
                news_display_df = news_display_df.drop_duplicates(
                    subset=["title"],
                    keep="first",
                )
    
            # =========================
            # 字段名中文化
            # =========================
    
            rename_map = {
                "published_at": "发布时间",
                "country": "国家",
                "event_type": "事件类型",
                "impact_direction": "影响方向",
                "risk_score": "风险评分",
                "supply_shock": "供给冲击",
                "price_shock": "价格冲击",
                "title_cn": "中文标题",
                "title": "英文标题",
                "source": "媒体来源",
                "url": "来源链接",
            }
    
            news_display_df = news_display_df.rename(columns=rename_map)
    
            # =========================
            # 内容中文化：国家
            # =========================
    
            if "国家" in news_display_df.columns:
                country_map = {
                    "China": "中国",
                    "Chile": "智利",
                    "Argentina": "阿根廷",
                    "Australia": "澳大利亚",
                    "Zimbabwe": "津巴布韦",
                    "Mali": "马里",
                    "Ghana": "加纳",
                    "Canada": "加拿大",
                    "United States": "美国",
                    "Brazil": "巴西",
                    "Portugal": "葡萄牙",
                    "Czech Republic": "捷克",
                    "Global": "全球/未识别",
                }
    
                news_display_df["国家"] = news_display_df["国家"].replace(country_map)
    
            # =========================
            # 内容中文化：事件类型
            # =========================
    
            if "事件类型" in news_display_df.columns:
                event_type_map = {
                    "export_ban_or_restriction": "出口禁令/出口限制",
                    "tax_or_royalty_increase": "税费/矿权费上升",
                    "permit_or_environmental_delay": "审批/环保延迟",
                    "production_disruption": "生产扰动",
                    "project_delay": "项目延期",
                    "price_pressure": "价格压力",
                    "project_approval_or_rampup": "审批通过/投产爬坡",
                    "investment_or_offtake": "投资/包销合作",
                    "general_lithium_resource_news": "一般锂资源新闻",
                }
    
                news_display_df["事件类型"] = news_display_df["事件类型"].replace(
                    event_type_map
                )
    
            # =========================
            # 内容中文化：影响方向
            # =========================
    
            if "影响方向" in news_display_df.columns:
                direction_map = {
                    "negative": "负面",
                    "positive": "正面",
                    "neutral": "中性",
                }
    
                news_display_df["影响方向"] = news_display_df["影响方向"].replace(
                    direction_map
                )
    
            # =========================
            # 时间与数字格式
            # =========================
    
            if "发布时间" in news_display_df.columns:
                news_display_df["发布时间"] = pd.to_datetime(
                    news_display_df["发布时间"],
                    errors="coerce",
                ).dt.strftime("%Y-%m-%d %H:%M")
    
            for col in ["风险评分", "供给冲击", "价格冲击"]:
                if col in news_display_df.columns:
                    news_display_df[col] = pd.to_numeric(
                        news_display_df[col],
                        errors="coerce",
                    ).round(4)
    
            # =========================
            # 中文标题优先
            # =========================
    
            if "中文标题" in news_display_df.columns and "英文标题" in news_display_df.columns:
                news_display_df["新闻标题"] = news_display_df["中文标题"].fillna(
                    news_display_df["英文标题"]
                )
            elif "中文标题" in news_display_df.columns:
                news_display_df["新闻标题"] = news_display_df["中文标题"]
            elif "英文标题" in news_display_df.columns:
                news_display_df["新闻标题"] = news_display_df["英文标题"]
    
            # =========================
            # 最终列顺序
            # =========================
    
            final_cols = [
                "发布时间",
                "国家",
                "事件类型",
                "影响方向",
                "风险评分",
                "供给冲击",
                "价格冲击",
                "新闻标题",
                "媒体来源",
                "来源链接",
            ]
    
            final_cols = [
                col for col in final_cols
                if col in news_display_df.columns
            ]
    
            news_display_df = news_display_df[final_cols]
    
            # =========================
            # 风险颜色区间
            # =========================
    
            def risk_row_style(row):
                score = row.get("风险评分", 0)
    
                try:
                    score = float(score)
                except Exception:
                    score = 0
    
                if score >= 0.80:
                    bg = "#FEE2E2"
                    fg = "#7F1D1D"
                elif score >= 0.65:
                    bg = "#FFEDD5"
                    fg = "#7C2D12"
                elif score >= 0.45:
                    bg = "#FEF3C7"
                    fg = "#78350F"
                elif score >= 0.30:
                    bg = "#EFF6FF"
                    fg = "#1E3A8A"
                else:
                    bg = "#DCFCE7"
                    fg = "#14532D"
    
                return [
                    f"background-color: {bg}; color: {fg};"
                    for _ in row
                ]
    
            styled_news_df = news_display_df.head(30).style.apply(
                risk_row_style,
                axis=1,
            )
    
            st.dataframe(
                styled_news_df,
                width="stretch",
                hide_index=True,
                height=520,
                column_config={
                    "来源链接": st.column_config.LinkColumn(
                        "来源链接",
                        help="点击打开新闻原文",
                        display_text="打开新闻",
                    ),
                    "新闻标题": st.column_config.TextColumn(
                        "新闻标题",
                        width="large",
                    ),
                    "媒体来源": st.column_config.TextColumn(
                        "媒体来源",
                        width="medium",
                    ),
                    "风险评分": st.column_config.NumberColumn(
                        "风险评分",
                        format="%.2f",
                    ),
                    "供给冲击": st.column_config.NumberColumn(
                        "供给冲击",
                        format="%.4f",
                    ),
                    "价格冲击": st.column_config.NumberColumn(
                        "价格冲击",
                        format="%.4f",
                    ),
                },
            )
    
        section_close()


    # =========================
    # 07 投资优先级清单
    # =========================

    def render_section_07_investment_priority():
        section_header("07", "投资优先级")
        section_open()
    
        ranking_cols = [
            "name",
            "country",
            "resource_type",
            "adjusted_aisc",
            "delivered_cost",
            "risk_score",
            "investment_score",
            "recommended_action",
        ]
    
        ranking_cols = [col for col in ranking_cols if col in filtered_invest_df.columns]
    
        if ranking_cols:
            table_df = filtered_invest_df.copy()
    
            if "investment_score" in table_df.columns:
                table_df["investment_score"] = pd.to_numeric(table_df["investment_score"], errors="coerce")
                table_df = table_df.sort_values("investment_score", ascending=False)
    
            st.dataframe(table_df[ranking_cols].head(30), width="stretch")
        else:
            st.info("暂无可展示的投资优先级字段。")
    
        section_close()


    # =========================
    # 08 单项目AI策略建议
    # =========================

    def render_section_08_ai_strategy():
        section_header("08", "AI策略建议")
        section_open()
    
        st.markdown(
            """
            <div class="insight-box">
            为保证看板加载速度，AI策略建议不在页面打开时批量生成。请选择具体项目后，点击按钮单独生成。
            </div>
            """,
            unsafe_allow_html=True,
        )
    
        if "name" not in filtered_invest_df.columns:
            st.warning("investment_recommendations.csv 中没有 name 字段。")
        else:
            if "investment_score" in filtered_invest_df.columns:
                strategy_projects = (
                    filtered_invest_df
                    .sort_values("investment_score", ascending=False)
                    ["name"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            else:
                strategy_projects = filtered_invest_df["name"].dropna().unique().tolist()
    
            if not strategy_projects:
                st.warning("当前筛选条件下没有可用项目。")
            else:
                selected_project = st.selectbox(
                    "选择项目查看 / 生成AI投资建议",
                    strategy_projects,
                )
    
                project_rows = filtered_invest_df[filtered_invest_df["name"] == selected_project].copy()
    
                if "investment_score" in project_rows.columns:
                    project_rows["investment_score"] = pd.to_numeric(project_rows["investment_score"], errors="coerce")
                    project_row = project_rows.sort_values("investment_score", ascending=False).iloc[0]
                else:
                    project_row = project_rows.iloc[0]
    
                ai_c1, ai_c2, ai_c3, ai_c4 = st.columns(4)
    
                with ai_c1:
                    st.metric("国家", project_row.get("country", "N/A"))
    
                with ai_c2:
                    st.metric("资源类型", project_row.get("resource_type", "N/A"))
    
                with ai_c3:
                    st.metric("投资评分", project_row.get("investment_score", "N/A"))
    
                with ai_c4:
                    st.metric("综合风险", project_row.get("risk_score", "N/A"))
    
                st.markdown("#### 系统建议动作")
                st.info(project_row.get("recommended_action", "暂无建议动作"))
    
                cache_key = f"ai_strategy_{selected_project}"
    
                if st.button("生成该项目AI投资策略建议", type="primary"):
                    with st.spinner("AI正在生成该项目投资建议，请稍候..."):
                        try:
                            from ai_strategy import generate_ai_strategy
    
                            price_center = expected_price
                            if price_center <= 0:
                                price_center = project_row.get("delivered_cost", 0)
    
                            strategy = generate_ai_strategy(
                                row=project_row,
                                predicted_price_center=price_center,
                                rule_action=project_row.get("recommended_action", ""),
                            )
    
                            st.session_state[cache_key] = strategy
    
                        except Exception as exc:
                            st.error(f"AI策略生成失败：{exc}")
    
                if cache_key in st.session_state:
                    st.markdown("#### AI Strategy Detail")
                    st.success(st.session_state[cache_key])
                else:
                    st.caption("尚未生成AI策略。点击上方按钮后，只会为当前项目调用一次AI。")
    
        section_close()


    # =========================
    # 09数据与模型说明
    # =========================

    def render_section_09_data_model():
        section_header("09", "数据与模型说明｜方法论与口径定义")
        section_open()

        subsection_title(
            "1. 系统方法论总览",
            "将价格、成本、政策约束与投资优先级统一到资源可获得性框架下。",
        )
        st.markdown(
            """
            <div class="insight-box">
            本系统将市场价格、三情景价格中枢、战略AISC、政策约束与项目投资优先级统一到“资源可获得性”框架下，用于辅助判断全球锂资源市场压力、供给兑现风险与资源配置优先级。
            <br><br>
            <b>逻辑链：</b>
            市场价格 → 三情景价格中枢 → 战略AISC成本锚 → Policy Constraint → RPI资源压力指数 → Investment Tier
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "2. 数据源说明",
            "说明主要输入数据、用途与更新节奏。",
        )
        data_source_df = pd.DataFrame(
            [
                {
                    "数据类型": "市场价格",
                    "主要来源": "GFEX、现货、SC6、期现价差",
                    "用途": "Market Monitor与价格验证",
                    "更新频率": "周度/可扩展为日度",
                },
                {
                    "数据类型": "价格情景",
                    "主要来源": "STEPS / APS / NZE 研究假设",
                    "用途": "2026–2035 LCE走势预测",
                    "更新频率": "模型更新",
                },
                {
                    "数据类型": "项目成本",
                    "主要来源": "全球锂资源样本库",
                    "用途": "AISC与投资优先级",
                    "更新频率": "模型更新",
                },
                {
                    "数据类型": "政策风险",
                    "主要来源": "IEA政策追踪、政策评分表",
                    "用途": "Policy Constraint与战略AISC溢价",
                    "更新频率": "周度/事件驱动",
                },
                {
                    "数据类型": "公司公告与新闻",
                    "主要来源": "IR、交易所公告、新闻事件",
                    "用途": "事件验证与风险预警",
                    "更新频率": "周度/事件驱动",
                },
            ]
        )
        st.dataframe(data_source_df, width="stretch", hide_index=True)
        st.caption(
            "全球锂资源样本用于行业比较和模型验证，不代表宁德时代已投资、已锁定或正在推进的项目组合。"
        )

        subsection_title(
            "3. AISC口径定义",
            "区分物理成本、现实调整成本与资源可获得成本。",
        )
        st.markdown(
            """
            <div class="insight-box">
            <b>原始AISC：</b>项目物理成本基础，反映矿山或盐湖项目的基础成本水平。<br>
            <b>调整后AISC：</b>在原始AISC基础上加入运营、运输、能源、汇率、爬坡等现实调整。<br>
            <b>战略AISC：</b>在调整后AISC基础上加入政策/战略风险溢价，用于衡量资源可获得成本。<br><br>
            <b>公式：</b>战略AISC = max(原始AISC, 调整后AISC) + 政策风险溢价<br><br>
            战略AISC不是传统矿山成本，而是资源可获得成本口径。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "4. 价格中枢 × 战略AISC关系",
            "用于判断未来价格是否足以支撑边际资源释放。",
        )
        st.markdown(
            """
            <div class="insight-box">
            三情景价格中枢用于刻画2026–2035年未来价格路径；战略AISC用于刻画全球锂资源样本的资源可获得成本边界。二者结合用于判断未来价格是否足以支撑边际资源释放。
            <br><br>
            <b>价格 &gt; AISC90 + 3：</b>覆盖充分<br>
            <b>AISC90 ≤ 价格 ≤ AISC90 + 3：</b>边际覆盖<br>
            <b>价格 &lt; AISC90：</b>价格倒挂<br><br>
            该判断用于识别供给兑现风险，不等同于价格预测承诺。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "5. Policy Constraint定义",
            "解释政策约束如何进入战略AISC。",
        )
        st.markdown(
            """
            <div class="insight-box">
            Policy Constraint 衡量政策对资源可获得性的压缩程度。它来自出口限制、本地加工要求、国家参与、税费/权利金、环保/盐湖保护、审批许可等因素。
            <br><br>
            <b>传导链：</b>政策事件 → 政策类型 → 供应链环节 → 政策风险溢价 → 战略AISC
            <br><br>
            Policy Constraint用于解释政策如何进入战略AISC，而不是单纯统计新闻数量。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "6. RPI资源压力指数定义",
            "核心驾驶舱使用的市场/样本整体压力指标。",
        )
        st.markdown(
            """
            <div class="insight-box">
            <b>RPI = 0.40 × Cost Pressure + 0.35 × Policy Constraint + 0.25 × Supply Tightness</b>
            <br><br>
            <b>Cost Pressure：</b>样本90%战略AISC / 当前LCE价格<br>
            <b>Supply Strength：</b>当前价格下战略AISC低于LCE价格的样本比例<br>
            <b>Supply Tightness：</b>1 - Supply Strength<br><br>
            RPI是市场/样本整体层面的压力指标，用于核心驾驶舱，不用于替代单个项目投资判断。
            </div>
            """,
            unsafe_allow_html=True,
        )
        rpi_tier_df = pd.DataFrame(
            [
                {"RPI区间": "0–30", "资源压力状态": "资源压力宽松", "策略含义": "扩张窗口"},
                {"RPI区间": "30–60", "资源压力状态": "资源压力中性", "策略含义": "精选投资"},
                {"RPI区间": "60–80", "资源压力状态": "资源压力上升", "策略含义": "谨慎布局"},
                {"RPI区间": "80–100", "资源压力状态": "资源压力高位", "策略含义": "收缩防御"},
            ]
        )
        st.dataframe(rpi_tier_df, width="stretch", hide_index=True)

        subsection_title(
            "7. Tier投资优先级定义",
            "项目层面的投资优先级判断。",
        )
        st.markdown(
            """
            <div class="insight-box">
            <b>战略投资评分 = 35% 成本优势 + 30% 价格安全垫 + 20% 产能贡献 + 15% 政策风险</b>
            <br><br>
            <b>成本优势：</b>战略AISC越低，成本优势越强。<br>
            <b>价格安全垫：</b>当前LCE价格相对战略AISC的覆盖能力。<br>
            <b>产能贡献：</b>项目产能对资源配置的潜在贡献。<br>
            <b>政策风险：</b>资源国政策、审批、环保、税费等对项目可获得性的约束。<br><br>
            RPI看市场压力，Tier看项目优先级。
            </div>
            """,
            unsafe_allow_html=True,
        )
        investment_tier_df = pd.DataFrame(
            [
                {"Tier": "Tier 1", "投资优先级": "优先锁定"},
                {"Tier": "Tier 2", "投资优先级": "重点跟踪"},
                {"Tier": "Tier 3", "投资优先级": "观察储备"},
                {"Tier": "Tier 4", "投资优先级": "暂缓推进"},
            ]
        )
        st.dataframe(investment_tier_df, width="stretch", hide_index=True)

        subsection_title(
            "8. 模型边界与免责声明",
            "说明系统用途、边界与不可替代事项。",
        )
        st.markdown(
            """
            <div class="insight-box">
            本系统为投研决策支持模型，不代表投资建议或已执行决策。<br>
            全球锂资源样本用于行业比较，不代表宁德时代已投资、已锁定或正在推进的项目。<br>
            政策风险评分为结构化研究指标，不替代法律、合规或尽职调查结论。<br>
            价格情景为研究假设，不构成价格预测承诺。
            </div>
            """,
            unsafe_allow_html=True,
        )

        section_close()


    def render_with_gap(render_func):
        render_func()
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    if top_nav == "CATL资源事业部周报":
        render_section_00_weekly_report()
    elif top_nav == "核心驾驶舱":
        render_with_gap(render_section_01_command_center)
    elif top_nav == "Market Monitor 市场监测中心":
        render_with_gap(render_section_02_market_monitor)
    elif top_nav == "LCE走势预测":
        st.markdown(
            """
            <div class="insight-box">
            <b>LCE走势预测专题</b><br>
            本页按照“短期价格判断—中期供需平衡—长期情景预测”的逻辑组织。
            短期重点观察碳酸锂价格区间、库存变化、SC6成本传导与期货预期；
            中期重点观察年度需求、可兑现供应与供需缺口；
            长期重点观察2026–2035年三种情景下的需求扩张、供给兑现率、结构性短缺和价格中枢。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "第一层：短期价格判断",
            "关注未来半年价格区间、库存变化、SC6成本传导、GFEX期货预期与价格驱动因子。"
        )
        render_section_02_price_forecast()

        subsection_title(
            "第二层：中期供需平衡",
            "关注年度需求、可兑现供应、供给折损与LCE缺口变化。"
        )
        render_section_03_supply_demand()

        subsection_title(
            "第三层：长期情景预测",
            "关注2026–2035年不同政策与需求情景下的长期供需缺口和价格中枢。"
        )
        render_section_04_long_term_scenario()
    elif top_nav == "全球资源地图与AISC成本":
        st.markdown(
            """
            <div class="insight-box">
            <b>全球资源配置结论：</b>
            优先锁定低成本盐湖与头部锂辉石项目；非洲资源保留机会型跟踪；
            高成本边际项目更多作为价格弹性观察指标。
            </div>
            """,
            unsafe_allow_html=True,
        )

        subsection_title(
            "第一层：全球资源地图",
            "识别资源分布、资源类型、国家风险和战略资源池。",
        )
        render_section_04_resource_map()

        subsection_title(
            "第二层：AISC成本曲线",
            "识别低成本核心资产、边际成本资产和价格支撑区间。",
        )
        render_section_05_aisc_curve()

        render_section_06_resource_portfolio_allocation()
    elif top_nav == "政策与新闻风险":
        topic_intro(
            "政策与新闻风险｜资源可获得性约束",
            "追踪全球锂资源政策、公司公告与新闻事件，解释其如何影响战略AISC、供给兑现和投资优先级。",
        )
        render_with_gap(render_section_06_policy_risk)
    elif top_nav == "数据与模型说明":
        topic_intro(
            "数据与模型说明｜方法论与口径定义",
            "解释本系统中价格、AISC、政策风险、RPI与投资Tier的计算逻辑和使用边界。",
        )
        render_with_gap(render_section_09_data_model)

    st.markdown(
        f"""
        <div class="small-muted">
        数据更新时间：{forecast.get("updated_at", "N/A") if forecast else "N/A"} ｜
        本看板用于内部研究与决策支持，不构成投资承诺或交易建议。
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
