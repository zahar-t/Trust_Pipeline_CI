"""Metric Trust Pipeline design helpers — bone / ink / copper palette."""

from __future__ import annotations

from html import escape

import streamlit as st

# ---------------------------------------------------------------------------
# Colour tokens (mirrors colors_and_type.css)
# ---------------------------------------------------------------------------

COLORS = {
    # Bone — warm off-white surfaces
    "surface":                 "#FBF9F4",   # bone-0 — page background
    "surface_container_low":   "#F3EFE6",   # bone-1 — cards / raised
    "surface_container":       "#E8E2D2",   # bone-2 — dividers / wells
    "surface_container_high":  "#D4CDB9",   # bone-3 — borders
    "surface_container_lowest": "#FFFFFF",  # white — highest contrast cards
    # Ink — deep warm brown text
    "on_surface":         "#2A241C",  # ink-700 — primary text
    "on_surface_variant": "#5A5044",  # ink-500 — secondary / captions
    "outline_variant":    "#D4CDB9",  # bone-3
    # Copper — primary brand accent
    "primary":            "#B5722F",  # copper-500
    "primary_container":  "#8A4E1A",  # copper-700
    "primary_tint":       "#F3DDC3",  # copper-100
    # Ink dark — sidebar / hero backgrounds
    "inverse_surface":    "#14110C",  # ink-900
    # Signal
    "signal_ok":          "#2E6B5A",
    "signal_ok_bg":       "#D6E4DF",
    "signal_warn":        "#E8B931",
    "signal_warn_bg":     "#FAEBB5",
    "signal_bad":         "#B2382F",
    "signal_bad_bg":      "#F4D5D3",
    "error":              "#B2382F",
}

# Per-page semantic accents — one hue per section, no rainbow gradients.
# Hero banner uses a consistent warm-ink background; the accent drives section
# headers, metric card borders, and active tab indicators only.
ACCENTS = {
    "home":          {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#B5722F"},
    "revenue":       {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#B5722F"},
    "consent":       {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#7D3C7B"},
    "metric_health": {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#2E6B5A"},
    "fx":            {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#3A6EA5"},
    "forecast":      {"gradient_start": "#14110C", "gradient_end": "#2A241C", "accent": "#C7433A"},
}


def apply_global_styles() -> None:
    """Inject global CSS shared by all pages."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Code+Pro:wght@400;600&display=swap');

        .stApp { background:#FBF9F4 !important; }
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

        /* Sidebar — warm ink, not cold slate */
        [data-testid="stSidebar"] { background: linear-gradient(165deg, #14110C 0%, #2A241C 100%) !important; }
        [data-testid="stSidebar"] * { color:#B3A994 !important; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top:0 !important; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            border-radius:8px; padding:6px 12px; margin:2px 0;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background:rgba(181,114,47,0.12) !important; color:#F3DDC3 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background:rgba(181,114,47,0.18) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] * {
            color:#F3DDC3 !important; font-weight:600 !important;
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stDateInput label {
            font-size:10px !important;
            font-weight:700 !important;
            text-transform:uppercase !important;
            letter-spacing:0.1em !important;
            color:#8A7F6D !important;
        }

        /* Charts */
        [data-testid="stPlotlyChart"] {
            background:#FFFFFF !important;
            border-radius:10px;
            padding:10px;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
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
            border-radius:10px;
            overflow:hidden;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
        }
        [data-testid="stMetric"] { display:none !important; }
        header[data-testid="stHeader"] { display:none !important; }
        [data-testid="stToolbar"] { display:none !important; }
        [data-testid="stDecoration"] { display:none !important; }
        #MainMenu { visibility:hidden !important; }

        /* Tabs — copper active state */
        .stTabs [data-baseweb="tab-list"] {
            gap:0;
            background:#FFFFFF;
            border-bottom:1px solid rgba(212,205,185,0.4);
            padding:0 18px;
            border-radius:10px 10px 0 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding:14px 18px;
            font-size:13px;
            font-weight:600;
            color:#8A7F6D;
            border-bottom:2px solid transparent;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color:#B5722F !important;
            border-bottom-color:#B5722F !important;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background:#FFFFFF;
            border-radius:0 0 10px 10px;
            padding:20px 18px;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
            overflow:visible;
        }
        [data-testid="stPageLink"] a {
            background:#FFFFFF !important;
            border:1px solid rgba(212,205,185,0.3) !important;
            border-radius:10px !important;
            min-height:108px !important;
            padding:16px 16px !important;
            align-items:flex-start !important;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
            font-weight:700 !important;
        }
        [data-testid="stPageLink"] a:hover {
            border-color:#D49A5C !important;
            background:#FAF0E6 !important;
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
    """Render a full-width hero banner with warm ink background."""
    accent = ACCENTS.get(page, ACCENTS["home"])
    right_html = ""
    if right_label and right_value:
        right_html = f"""
        <div style=\"text-align:right;padding-bottom:4px;\">
            <div style=\"font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;opacity:0.6;margin-bottom:4px;\">{right_label}</div>
            <div style=\"font-size:18px;font-family:'Inter',monospace;font-weight:600;\">{right_value}</div>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {accent['gradient_start']} 0%, {accent['gradient_end']} 100%);
            color: #FBF9F4;
            padding: 40px 42px;
            margin: -1rem -1rem 0 -1rem;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            border-radius: 0 0 14px 14px;
        ">
            <div>
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(181,114,47,0.20);
                    border: 1px solid rgba(181,114,47,0.35);
                    border-radius: 6px;
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
                <h2 style="font-size:38px;font-weight:800;letter-spacing:-0.022em;margin:0 0 6px 0;color:#FBF9F4;line-height:1.1;">{title}</h2>
                <p style="font-size:14px;font-weight:500;opacity:0.75;margin:0;max-width:560px;line-height:1.55;">{subtitle}</p>
            </div>
            {right_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(label: str, accent_color: str = "#B5722F") -> None:
    """Render a small uppercase section label with accent bar."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:28px 0 14px 0;">
            <span style="width:4px;height:14px;background:{accent_color};border-radius:4px;display:inline-block;"></span>
            <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{COLORS['on_surface_variant']};">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    delta: str = "",
    delta_positive: bool = True,
    accent_color: str = "#B5722F",
    description: str = "",
) -> None:
    """Render a KPI card with left accent border."""
    label_safe = escape(label)
    value_safe = escape(value)
    description_safe = escape(description)

    delta_html = ""
    if delta:
        delta_color = COLORS["signal_ok"] if delta_positive else COLORS["error"]
        arrow = "&#x2197;" if delta_positive else "&#x2198;"
        delta_safe = escape(delta)
        delta_html = f'<span style="font-size:12px;font-weight:700;color:{delta_color};margin-left:8px;">{arrow} {delta_safe}</span>'

    desc_html = ""
    if description:
        desc_html = f'<div style="font-size:10px;color:{COLORS["on_surface_variant"]};margin-top:6px;font-weight:500;">{description_safe}</div>'

    html = (
        f'<div style="background:{COLORS["surface_container_lowest"]};border-left:4px solid {accent_color};'
        'border-radius:10px;padding:22px;'
        'box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);height:100%;">'
        f'<p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:{COLORS["on_surface_variant"]};margin:0 0 8px 0;">{label_safe}</p>'
        '<div style="display:flex;align-items:baseline;">'
        f'<span style="font-size:32px;font-weight:800;color:{COLORS["on_surface"]};letter-spacing:-0.022em;line-height:1;">{value_safe}</span>'
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
            border-radius:10px;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
            border:1px solid rgba(212,205,185,0.25);
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
        bg = COLORS["signal_ok_bg"] if available else COLORS["signal_bad_bg"]
        color = COLORS["signal_ok"] if available else COLORS["signal_bad"]
        icon = "&#x2713;" if available else "&#x2717;"
        ring = "#B8D4CC" if available else "#E8B5B1"

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
        <div style="background:{COLORS['surface_container_low']};padding:28px;border-radius:10px;border:1px solid rgba(212,205,185,0.2);">
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
        "success":   {"bg": "#D6E4DF", "color": "#2E6B5A"},
        "warning":   {"bg": "#FAEBB5", "color": "#5C4410"},
        "error":     {"bg": "#F4D5D3", "color": "#B2382F"},
        "neutral":   {"bg": "#E8E2D2", "color": "#5A5044"},
        "favorable": {"bg": "#D6E4DF", "color": "#2E6B5A"},
        "adverse":   {"bg": "#F4D5D3", "color": "#B2382F"},
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
            font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;
            color:{COLORS['on_surface_variant']};text-align:{a};background:{COLORS['surface_container_low']};
        ">{h}</th>
        """

    body_rows = ""
    for idx, row in enumerate(rows):
        bg = "background:rgba(232,226,210,0.25);" if idx % 2 == 1 else ""
        cells = ""
        for val, a in zip(row, align):
            cells += f'<td style="padding:14px 22px;font-size:13px;text-align:{a};{bg}">{val}</td>'
        body_rows += f"<tr>{cells}</tr>"

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_lowest']};
            border-radius:10px;overflow:hidden;
            box-shadow:0 1px 0 rgba(20,17,12,0.04), 0 1px 2px rgba(20,17,12,0.06);
            border:1px solid rgba(212,205,185,0.2);
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
        dot_color  = COLORS["signal_ok"]  if is_positive else COLORS["signal_bad"]
        text_color = COLORS["signal_ok"]  if is_positive else COLORS["signal_bad"]
        border_color = "#B8D4CC" if is_positive else "#E8B5B1"
        badges_html += f"""
        <div style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:white;border-radius:6px;border:1px solid {border_color};">
            <span style="width:6px;height:6px;border-radius:50%;background:{dot_color};display:inline-block;"></span>
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;color:{text_color};">{label}</span>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_low']};
            padding:16px 24px;
            border-radius:0 0 10px 10px;
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
        <div style="background:{COLORS['surface_container_low']};padding:28px;border-radius:10px;overflow:hidden;">
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
    """Render branded sidebar header."""
    st.sidebar.markdown(
        """
        <div style="padding:8px 8px 12px 8px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                <div style="width:28px;height:28px;background:#B5722F;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#FBF9F4;font-weight:800;font-size:12px;">M</div>
                <div>
                    <div style="font-size:22px;font-weight:800;color:#FBF9F4;line-height:1;">Metric Trust</div>
                    <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#8A7F6D;font-weight:700;">Pipeline</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="position:fixed;bottom:20px;left:16px;width:220px;padding-top:12px;border-top:1px solid rgba(181,114,47,0.2);">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(181,114,47,0.18);display:flex;align-items:center;justify-content:center;color:#D49A5C;font-weight:700;">A</div>
                <div>
                    <div style="font-size:12px;font-weight:700;color:#FBF9F4;line-height:1.1;">Administrator</div>
                    <div style="font-size:10px;color:#8A7F6D;">admin@metrictrust.com</div>
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
            background:rgba(251,249,244,0.88);
            backdrop-filter:blur(8px);
            border-bottom:1px solid rgba(212,205,185,0.35);
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:0 24px;
            position:sticky;
            top:0;
            z-index:9;
        ">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:13px;color:#8A7F6D;font-weight:600;">Pipeline /</span>
                <span style="font-size:13px;color:#B5722F;font-weight:700;">{current_page}</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="
                    min-width:240px;
                    background:#F3EFE6;
                    border-radius:8px;
                    padding:6px 12px;
                    font-size:12px;
                    color:#8A7F6D;
                ">{search_placeholder}</div>
                <span style="font-size:15px;color:#8A7F6D;">🔔</span>
                <span style="font-size:15px;color:#8A7F6D;">⚙️</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
