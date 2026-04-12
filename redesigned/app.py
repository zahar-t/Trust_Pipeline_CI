"""Metric Trust Pipeline - Redesigned entry point (Financial Architect theme)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dashboard"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

st.set_page_config(
    page_title="Metric Trust Pipeline",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — "The Financial Architect" design system
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== Root — Design Tokens ===== */
    :root {
        --surface: #f9f9ff;
        --surface-container-low: #f1f3ff;
        --surface-container: #e9edff;
        --surface-container-high: #e0e8ff;
        --surface-container-lowest: #ffffff;
        --on-surface: #0d1b34;
        --on-surface-variant: #444651;
        --outline-variant: #c5c5d3;
        --primary: #00236f;
        --primary-container: #1e3a8a;
        --inverse-surface: #23304a;
    }

    /* ===== Base ===== */
    .stApp {
        background: var(--surface) !important;
    }
    .stApp * {
        font-family: 'Inter', -apple-system, sans-serif !important;
    }

    /* ===== Sidebar — Dark Navy (The Anchor) ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #0f172a 0%, #23304a 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        border-radius: 8px;
        padding: 6px 12px;
        transition: all 0.2s ease;
        margin: 2px 0;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,0.06) !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
        background: rgba(255,255,255,0.10) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stDateInput label {
        font-size: 10px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: #64748b !important;
    }

    /* ===== Hide default Streamlit metric cards (we use custom HTML) ===== */
    [data-testid="stMetric"] {
        display: none !important;
    }

    /* ===== Headers ===== */
    h1 {
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
        color: var(--on-surface) !important;
    }
    h2 {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: var(--on-surface) !important;
    }
    h3 {
        font-size: 15px !important;
        font-weight: 700 !important;
        color: var(--on-surface) !important;
    }

    /* ===== Plotly charts — clean canvas ===== */
    [data-testid="stPlotlyChart"] {
        background: var(--surface-container-lowest) !important;
        border-radius: 12px;
        border: 1px solid rgba(197,197,211,0.1);
        padding: 12px;
        box-shadow: 0 1px 4px rgba(13,27,52,0.04);
    }

    /* ===== Dataframes ===== */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(197,197,211,0.1);
        box-shadow: 0 1px 4px rgba(13,27,52,0.04);
    }

    /* ===== Tabs — Stitch tab underline style ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--surface-container-lowest);
        border-bottom: 1px solid rgba(197,197,211,0.15);
        padding: 0 24px;
        border-radius: 12px 12px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 16px 24px;
        font-size: 13px;
        font-weight: 500;
        color: var(--on-surface-variant);
        border-radius: 0;
        border-bottom: 2px solid transparent;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        font-weight: 600;
        border-bottom-color: var(--primary-container) !important;
        color: var(--primary) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--surface-container-lowest);
        border-radius: 0 0 12px 12px;
        padding: 24px;
        box-shadow: 0 1px 4px rgba(13,27,52,0.04);
    }

    /* ===== Buttons ===== */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30,58,138,0.12);
    }

    /* ===== Alerts — rounded ===== */
    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* ===== Selectbox / inputs ===== */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        border-radius: 10px !important;
        background: var(--surface-container-low) !important;
    }

    /* ===== Dividers — The "No-Line" Rule ===== */
    hr {
        border: none;
        height: 0;
        margin: 8px 0;
    }

    /* ===== Hide colored_header and streamlit-extras styling ===== */
    /* We use our own design_system components instead */
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

pages = [
    st.Page("pages/1_Main.py", title="Home", icon="\U0001f3e0"),
    st.Page("pages/1_Revenue_Overview.py", title="Revenue Overview", icon="\U0001f4b0"),
    st.Page("pages/2_Consent_Impact.py", title="Consent Impact", icon="\U0001f6e1\ufe0f"),
    st.Page("pages/3_Metric_Health.py", title="Metric Health", icon="\U0001fa7a"),
    st.Page("pages/4_FX_Impact.py", title="FX Impact", icon="\U0001f4b1"),
    st.Page("pages/5_Consent_Forecast.py", title="Consent Forecast", icon="\U0001f52e"),
]

pg = st.navigation(pages)
pg.run()
