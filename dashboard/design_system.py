"""Financial Architect design helpers for the Streamlit dashboard."""

from __future__ import annotations

from html import escape

import streamlit as st

COLORS = {
    "surface": "#f9f9ff",
    "surface_container_low": "#f1f3ff",
    "surface_container": "#e9edff",
    "surface_container_high": "#e0e8ff",
    "surface_container_lowest": "#ffffff",
    "on_surface": "#0d1b34",
    "on_surface_variant": "#444651",
    "outline_variant": "#c5c5d3",
    "primary": "#00236f",
    "primary_container": "#1e3a8a",
    "inverse_surface": "#23304a",
    "error": "#ba1a1a",
}

ACCENTS = {
    "home": {"gradient_start": "#1e3a8a", "gradient_end": "#3b82f6", "accent": "#3b82f6"},
    "revenue": {"gradient_start": "#1e3a8a", "gradient_end": "#3b82f6", "accent": "#3b82f6"},
    "consent": {"gradient_start": "#9a3412", "gradient_end": "#f97316", "accent": "#f97316"},
    "metric_health": {"gradient_start": "#5b21b6", "gradient_end": "#8b5cf6", "accent": "#8b5cf6"},
    "fx": {"gradient_start": "#064e3b", "gradient_end": "#10b981", "accent": "#10b981"},
    "forecast": {"gradient_start": "#991b1b", "gradient_end": "#ef4444", "accent": "#ef4444"},
}


def apply_global_styles() -> None:
    """Inject global CSS shared by all pages."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        .stApp { background:#f9f9ff !important; }
        .stApp *:not(.material-symbols-rounded):not(.material-symbols-outlined):not(.material-icons) {
            font-family:'Inter', -apple-system, sans-serif !important;
        }
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            font-style: normal !important;
            font-weight: normal !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            white-space: nowrap !important;
            direction: ltr !important;
        }
        [data-testid="stSidebarCollapseButton"] * {
            text-transform: none !important;
        }
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            overflow-x: hidden !important;
        }

        [data-testid="stSidebar"] { background: linear-gradient(165deg, #0f172a 0%, #23304a 100%) !important; }
        [data-testid="stSidebar"] * { color:#94a3b8 !important; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top:0 !important; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            border-radius:8px; padding:6px 12px; margin:2px 0;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background:rgba(255,255,255,0.06) !important; color:#e2e8f0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background:rgba(255,255,255,0.10) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] * {
            color:white !important; font-weight:600 !important;
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stDateInput label {
            font-size:10px !important;
            font-weight:700 !important;
            text-transform:uppercase !important;
            letter-spacing:0.1em !important;
            color:#64748b !important;
        }

        [data-testid="stPlotlyChart"] {
            background:#ffffff !important;
            border-radius:12px;
            padding:10px;
            box-shadow:0 1px 4px rgba(13,27,52,0.04);
            overflow:hidden !important;
            max-width:100% !important;
        }
        [data-testid="stPlotlyChart"] > div,
        [data-testid="stPlotlyChart"] .js-plotly-plot,
        [data-testid="stPlotlyChart"] .plot-container,
        [data-testid="stPlotlyChart"] .svg-container {
            width:100% !important;
            max-width:100% !important;
        }
        [data-testid="stPlotlyChart"] .modebar {
            right:8px !important;
            top:8px !important;
        }
        [data-testid="stPlotlyChart"] .plotly .main-svg,
        [data-testid="stPlotlyChart"] .plotly .svg-container {
            overflow: hidden !important;
        }
        [data-testid="stFileUploader"] button {
            display:inline-flex !important;
            align-items:center !important;
            gap:8px !important;
            line-height:1 !important;
            font-size:14px !important;
        }
        [data-testid="stFileUploader"] button [class*="material"],
        [data-testid="stFileUploader"] button [data-testid="stIconMaterial"] {
            display:none !important;
        }
        [data-testid="stDataFrame"] {
            border-radius:12px;
            overflow:hidden;
            box-shadow:0 1px 4px rgba(13,27,52,0.04);
        }
        [data-testid="stMetric"] { display:none !important; }
        header[data-testid="stHeader"] { display:none !important; }
        [data-testid="stToolbar"] { display:none !important; }
        [data-testid="stDecoration"] { display:none !important; }
        #MainMenu { visibility:hidden !important; }

        .stTabs [data-baseweb="tab-list"] {
            gap:0;
            background:#ffffff;
            border-bottom:1px solid rgba(197,197,211,0.2);
            padding:0 18px;
            border-radius:12px 12px 0 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding:14px 18px;
            font-size:13px;
            font-weight:600;
            color:#556070;
            border-bottom:2px solid transparent;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color:#1e3a8a !important;
            border-bottom-color:#1e3a8a !important;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background:#ffffff;
            border-radius:0 0 12px 12px;
            padding:20px 18px;
            box-shadow:0 1px 4px rgba(13,27,52,0.04);
            overflow:visible;
        }
        [data-testid="stPageLink"] a {
            background:#ffffff !important;
            border:1px solid rgba(197,197,211,0.18) !important;
            border-radius:12px !important;
            min-height:108px !important;
            padding:16px 16px !important;
            align-items:flex-start !important;
            box-shadow:0 1px 3px rgba(13,27,52,0.04);
            font-weight:700 !important;
        }
        [data-testid="stPageLink"] a:hover {
            border-color:#93c5fd !important;
            background:#f8fbff !important;
        }

        section.main > div { padding-top:0.25rem; }
        hr { border:none; height:0; margin:8px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero_banner(
    title: str,
    subtitle: str,
    badge_text: str,
    page: str = "home",
    right_label: str = "",
    right_value: str = "",
) -> None:
    """Render a full-width hero banner."""
    accent = ACCENTS.get(page, ACCENTS["home"])
    right_html = ""
    if right_label and right_value:
        right_html = f"""
        <div style=\"text-align:right;padding-bottom:4px;\">
            <div style=\"font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;opacity:0.75;margin-bottom:4px;\">{right_label}</div>
            <div style=\"font-size:18px;font-family:'Inter',monospace;font-weight:600;\">{right_value}</div>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {accent['gradient_start']} 0%, {accent['gradient_end']} 100%);
            color: white;
            padding: 40px 42px;
            margin: -1rem -1rem 0 -1rem;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            border-radius: 0 0 12px 12px;
        ">
            <div>
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(255,255,255,0.12);
                    border-radius: 8px;
                    padding: 4px 12px;
                    margin-bottom: 14px;
                    font-size: 10px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                ">
                    <span style="width:8px;height:8px;border-radius:50%;background:#4ade80;display:inline-block;"></span>
                    {badge_text}
                </div>
                <h2 style="font-size:38px;font-weight:800;letter-spacing:-0.02em;margin:0 0 6px 0;color:white;line-height:1.1;">{title}</h2>
                <p style="font-size:14px;font-weight:500;opacity:0.9;margin:0;max-width:560px;line-height:1.5;">{subtitle}</p>
            </div>
            {right_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(label: str, accent_color: str = "#3b82f6") -> None:
    """Render a small uppercase section label with accent bar."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:28px 0 14px 0;">
            <span style="width:4px;height:14px;background:{accent_color};border-radius:4px;display:inline-block;"></span>
            <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{COLORS['on_surface_variant']};">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    delta: str = "",
    delta_positive: bool = True,
    accent_color: str = "#3b82f6",
    description: str = "",
) -> None:
    """Render a premium KPI card."""
    label_safe = escape(label)
    value_safe = escape(value)
    description_safe = escape(description)

    delta_html = ""
    if delta:
        delta_color = "#10b981" if delta_positive else COLORS["error"]
        arrow = "&#x2197;" if delta_positive else "&#x2198;"
        delta_safe = escape(delta)
        delta_html = f'<span style="font-size:12px;font-weight:700;color:{delta_color};margin-left:8px;">{arrow} {delta_safe}</span>'

    desc_html = ""
    if description:
        desc_html = f'<div style="font-size:10px;color:{COLORS["on_surface_variant"]};margin-top:6px;font-weight:500;">{description_safe}</div>'

    html = (
        f'<div style="background:{COLORS["surface_container_lowest"]};border-left:4px solid {accent_color};'
        'border-radius:12px;padding:22px;box-shadow:0 1px 4px rgba(13,27,52,0.04);height:100%;">'
        f'<p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{COLORS["on_surface_variant"]};margin:0 0 8px 0;">{label_safe}</p>'
        '<div style="display:flex;align-items:baseline;">'
        f'<span style="font-size:32px;font-weight:800;color:{COLORS["on_surface"]};letter-spacing:-0.02em;line-height:1;">{value_safe}</span>'
        f"{delta_html}</div>{desc_html}</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def nav_card(icon: str, title: str, description: str) -> None:
    """Render a navigation card."""
    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_lowest']};
            padding:18px;
            border-radius:12px;
            box-shadow:0 1px 3px rgba(13,27,52,0.04);
            border:1px solid rgba(197,197,211,0.15);
            height:100%;
        ">
            <div style="font-size:22px;margin-bottom:10px;">{icon}</div>
            <h4 style="font-size:13px;font-weight:700;color:{COLORS['on_surface']};margin:0 0 4px 0;">{title}</h4>
            <p style="font-size:10px;color:{COLORS['on_surface_variant']};margin:0;line-height:1.4;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pipeline_health(tables: list[tuple[str, bool]]) -> None:
    """Render pipeline availability indicators."""
    items_html = ""
    for name, available in tables:
        name_safe = escape(name)
        bg = "#ECFDF5" if available else "#FEF2F2"
        color = "#10b981" if available else COLORS["error"]
        icon = "&#x2713;" if available else "&#x2717;"
        ring = "#D1FAE5" if available else "#FECACA"

        items_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;min-width:78px;">
            <div style="
                width:38px;height:38px;border-radius:50%;
                background:{bg};display:flex;align-items:center;justify-content:center;
                color:{color};font-weight:700;font-size:16px;
                border:2px solid white;box-shadow:0 0 0 4px {ring}, 0 1px 3px rgba(0,0,0,0.05);
                margin-bottom:8px;
            ">{icon}</div>
            <span style="
                font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.02em;
                color:{COLORS['on_surface_variant']};text-align:center;max-width:86px;word-break:break-word;
            ">{name_safe}</span>
        </div>
        """

    st.markdown(
        f"""
        <div style="background:{COLORS['surface_container_low']};padding:28px;border-radius:12px;border:1px solid rgba(197,197,211,0.1);">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;max-width:960px;margin:0 auto;flex-wrap:wrap;">
                {items_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(label: str, variant: str = "success") -> str:
    """Return inline status badge HTML."""
    configs = {
        "success": {"bg": "#ECFDF5", "color": "#047857"},
        "warning": {"bg": "#FEF3C7", "color": "#92400E"},
        "error": {"bg": "#FEF2F2", "color": "#991B1B"},
        "neutral": {"bg": "#F1F5F9", "color": "#475569"},
        "favorable": {"bg": "#ECFDF5", "color": "#047857"},
        "adverse": {"bg": "#FEF2F2", "color": "#991B1B"},
    }
    c = configs.get(variant, configs["neutral"])
    label_safe = escape(label)
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:4px;background:{c["bg"]};'
        f'color:{c["color"]};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">{label_safe}</span>'
    )


def editorial_table(headers: list[str], rows: list[list[str]], align: list[str] | None = None) -> None:
    """Render editorial style table with tonal rows and no hard lines."""
    if align is None:
        align = ["left"] * len(headers)

    header_cells = ""
    for h, a in zip(headers, align):
        header_cells += f"""
        <th style="
            padding:16px 22px;
            font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
            color:{COLORS['on_surface_variant']};text-align:{a};background:{COLORS['surface_container_low']};
        ">{h}</th>
        """

    body_rows = ""
    for idx, row in enumerate(rows):
        bg = "background:rgba(241,243,255,0.3);" if idx % 2 == 1 else ""
        cells = ""
        for val, a in zip(row, align):
            cells += f'<td style="padding:14px 22px;font-size:13px;text-align:{a};{bg}">{val}</td>'
        body_rows += f"<tr>{cells}</tr>"

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_lowest']};
            border-radius:12px;overflow:hidden;
            box-shadow:0 1px 4px rgba(13,27,52,0.04);
            border:1px solid rgba(197,197,211,0.1);
        ">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr>{header_cells}</tr></thead>
                <tbody>{body_rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def signal_badges(items: list[tuple[str, str]]) -> None:
    """Render a row of signal badges."""
    badges_html = ""
    for label, variant in items:
        is_positive = variant == "positive"
        dot_color = "#10b981" if is_positive else COLORS["error"]
        text_color = "#047857" if is_positive else "#991B1B"
        border_color = "#D1FAE5" if is_positive else "#FECACA"
        badges_html += f"""
        <div style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:white;border-radius:8px;border:1px solid {border_color};">
            <span style="width:6px;height:6px;border-radius:50%;background:{dot_color};display:inline-block;"></span>
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;color:{text_color};">{label}</span>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_low']};
            padding:16px 24px;
            border-radius:0 0 12px 12px;
            display:flex;
            flex-wrap:wrap;
            gap:8px;
            align-items:center;
        ">
            <span style="font-size:11px;font-weight:700;color:{COLORS['on_surface_variant']};margin-right:8px;">Signal Summary:</span>
            {badges_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(icon: str, title: str, description: str) -> None:
    """Render contextual insight card."""
    st.markdown(
        f"""
        <div style="background:{COLORS['surface_container_low']};padding:28px;border-radius:12px;overflow:hidden;">
            <div style="font-size:28px;margin-bottom:14px;">{icon}</div>
            <h4 style="font-size:16px;font-weight:700;color:{COLORS['on_surface']};margin:0 0 8px 0;">{title}</h4>
            <p style="font-size:13px;color:{COLORS['on_surface_variant']};line-height:1.6;margin:0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def spacer(height: int = 24) -> None:
    """Render vertical spacer."""
    st.markdown(f'<div style="height:{height}px;"></div>', unsafe_allow_html=True)


def sidebar_brand() -> None:
    """Render branded sidebar header and user footer."""
    st.sidebar.markdown(
        """
        <div style="padding:8px 8px 12px 8px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                <div style="width:28px;height:28px;background:#2563eb;border-radius:6px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:12px;">M</div>
                <div>
                    <div style="font-size:22px;font-weight:800;color:#ffffff;line-height:1;">Metric Trust</div>
                    <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#94a3b8;font-weight:700;">Financial Architect</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="position:fixed;bottom:20px;left:16px;width:220px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.08);">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;color:#dbeafe;font-weight:700;">A</div>
                <div>
                    <div style="font-size:12px;font-weight:700;color:#ffffff;line-height:1.1;">Administrator</div>
                    <div style="font-size:10px;color:#94a3b8;">admin@metrictrust.com</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def top_nav(current_page: str, search_placeholder: str = "Search metrics...") -> None:
    """Render concept-style top nav bar."""
    st.markdown(
        f"""
        <div style="
            margin:-1rem -1rem 0 -1rem;
            height:58px;
            background:rgba(249,249,255,0.85);
            backdrop-filter:blur(8px);
            border-bottom:1px solid rgba(197,197,211,0.2);
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:0 24px;
            position:sticky;
            top:0;
            z-index:9;
        ">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:13px;color:#64748b;font-weight:600;">Pipeline /</span>
                <span style="font-size:13px;color:#1e3a8a;font-weight:700;">{current_page}</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="
                    min-width:240px;
                    background:#f1f3ff;
                    border-radius:10px;
                    padding:6px 12px;
                    font-size:12px;
                    color:#94a3b8;
                ">{search_placeholder}</div>
                <span style="font-size:15px;color:#64748b;">🔔</span>
                <span style="font-size:15px;color:#64748b;">⚙️</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
