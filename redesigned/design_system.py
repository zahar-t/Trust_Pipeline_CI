"""Design System: The Financial Architect — reusable HTML components for Streamlit.

Translates the Stitch/Tailwind mockups into st.markdown(unsafe_allow_html=True)
components that maintain the editorial, tonal-layering aesthetic.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Color Tokens (from DESIGN.md / Stitch config)
# ---------------------------------------------------------------------------

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
    "sidebar_start": "#0f172a",
    "sidebar_end": "#23304a",
}

# Page accent colors
ACCENTS = {
    "home": {"gradient_start": "#1e3a8a", "gradient_end": "#3b82f6", "accent": "#3b82f6", "light": "#EFF6FF"},
    "revenue": {"gradient_start": "#1e3a8a", "gradient_end": "#3b82f6", "accent": "#3b82f6", "light": "#EFF6FF"},
    "consent": {"gradient_start": "#9a3412", "gradient_end": "#f97316", "accent": "#f97316", "light": "#FFF7ED"},
    "metric_health": {"gradient_start": "#5b21b6", "gradient_end": "#8b5cf6", "accent": "#8b5cf6", "light": "#F5F3FF"},
    "fx": {"gradient_start": "#064e3b", "gradient_end": "#10b981", "accent": "#10b981", "light": "#ECFDF5"},
    "forecast": {"gradient_start": "#991b1b", "gradient_end": "#ef4444", "accent": "#ef4444", "light": "#FEF2F2"},
}


# ---------------------------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------------------------

def hero_banner(
    title: str,
    subtitle: str,
    badge_text: str,
    badge_icon: str = "analytics",
    page: str = "home",
    right_label: str = "",
    right_value: str = "",
) -> None:
    """Full-width gradient hero banner matching the Stitch mockup."""
    a = ACCENTS.get(page, ACCENTS["home"])
    right_html = ""
    if right_label and right_value:
        right_html = f"""
        <div style="text-align:right;padding-bottom:4px;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;opacity:0.7;margin-bottom:4px;">{right_label}</div>
            <div style="font-size:18px;font-family:'Inter',monospace;font-weight:600;">{right_value}</div>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {a['gradient_start']} 0%, {a['gradient_end']} 100%);
            color: white;
            padding: 40px 48px;
            margin: -1rem -1rem 0 -1rem;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
        ">
            <div>
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(255,255,255,0.12);
                    border-radius: 8px;
                    padding: 4px 12px;
                    margin-bottom: 16px;
                    font-size: 10px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                ">
                    <span style="width:8px;height:8px;border-radius:50%;background:#4ade80;display:inline-block;"></span>
                    {badge_text}
                </div>
                <h2 style="
                    font-size: 36px;
                    font-weight: 800;
                    letter-spacing: -0.025em;
                    margin: 0 0 6px 0;
                    color: white;
                    line-height: 1.1;
                ">{title}</h2>
                <p style="
                    font-size: 14px;
                    font-weight: 500;
                    opacity: 0.85;
                    margin: 0;
                    max-width: 520px;
                    line-height: 1.5;
                ">{subtitle}</p>
            </div>
            {right_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Section Header (small uppercase label with accent bar)
# ---------------------------------------------------------------------------

def section_header(label: str, accent_color: str = "#3b82f6") -> None:
    """Small uppercase section label with a colored pill on the left."""
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 32px 0 16px 0;
        ">
            <span style="
                width: 4px;
                height: 14px;
                background: {accent_color};
                border-radius: 4px;
                display: inline-block;
            "></span>
            <span style="
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: {COLORS['on_surface_variant']};
            ">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Metric Card (white card with left accent border)
# ---------------------------------------------------------------------------

def metric_card(
    label: str,
    value: str,
    delta: str = "",
    delta_positive: bool = True,
    accent_color: str = "#3b82f6",
    description: str = "",
) -> None:
    """Premium metric card matching the Stitch design — no outer border, left accent."""
    delta_html = ""
    if delta:
        delta_color = "#10b981" if delta_positive else COLORS["error"]
        arrow = "&#x2197;" if delta_positive else "&#x2198;"
        delta_html = f"""
        <span style="
            font-size: 12px;
            font-weight: 700;
            color: {delta_color};
            margin-left: 8px;
        ">{arrow} {delta}</span>
        """

    desc_html = ""
    if description:
        desc_html = f"""
        <div style="
            font-size: 10px;
            color: {COLORS['on_surface_variant']};
            margin-top: 6px;
            font-weight: 500;
        ">{description}</div>
        """

    st.markdown(
        f"""
        <div style="
            background: {COLORS['surface_container_lowest']};
            border-left: 4px solid {accent_color};
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 4px rgba(13,27,52,0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            height: 100%;
        " onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 24px rgba(13,27,52,0.08)'"
           onmouseout="this.style.transform='none';this.style.boxShadow='0 1px 4px rgba(13,27,52,0.04)'">
            <p style="
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: {COLORS['on_surface_variant']};
                margin: 0 0 8px 0;
            ">{label}</p>
            <div style="display: flex; align-items: baseline;">
                <span style="
                    font-size: 28px;
                    font-weight: 800;
                    color: {COLORS['on_surface']};
                    letter-spacing: -0.02em;
                    line-height: 1;
                ">{value}</span>
                {delta_html}
            </div>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Navigation Card
# ---------------------------------------------------------------------------

def nav_card(icon: str, title: str, description: str) -> None:
    """Quick navigation card matching the Stitch bento grid."""
    st.markdown(
        f"""
        <div style="
            background: {COLORS['surface_container_lowest']};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(13,27,52,0.04);
            border: 1px solid rgba(197,197,211,0.15);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            cursor: pointer;
            height: 100%;
        " onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 8px 24px rgba(13,27,52,0.08)'"
           onmouseout="this.style.transform='none';this.style.boxShadow='0 1px 3px rgba(13,27,52,0.04)'">
            <div style="font-size: 22px; margin-bottom: 10px;">{icon}</div>
            <h4 style="
                font-size: 13px;
                font-weight: 700;
                color: {COLORS['on_surface']};
                margin: 0 0 4px 0;
            ">{title}</h4>
            <p style="
                font-size: 10px;
                color: {COLORS['on_surface_variant']};
                margin: 0;
                line-height: 1.4;
            ">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pipeline Health Step
# ---------------------------------------------------------------------------

def pipeline_health(tables: list[tuple[str, bool]]) -> None:
    """Data pipeline health indicator with connected circles."""
    items_html = ""
    for i, (name, available) in enumerate(tables):
        bg = "#ECFDF5" if available else "#FEF2F2"
        color = "#10b981" if available else COLORS["error"]
        icon = "&#x2713;" if available else "&#x2717;"
        ring = "#D1FAE5" if available else "#FECACA"

        connector = ""
        if i < len(tables) - 1:
            line_color = "#A7F3D0" if available else "#FECACA"
            connector = f'<div style="flex:1;height:2px;background:{line_color};margin-top:-22px;display:none;"></div>'

        items_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;min-width:80px;">
            <div style="
                width:40px;height:40px;border-radius:50%;
                background:{bg};
                display:flex;align-items:center;justify-content:center;
                color:{color};font-weight:700;font-size:16px;
                border:2px solid white;
                box-shadow:0 0 0 4px {ring}, 0 1px 3px rgba(0,0,0,0.05);
                margin-bottom:8px;
                transition: transform 0.2s;
            " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">{icon}</div>
            <span style="
                font-size:9px;font-weight:700;
                text-transform:uppercase;letter-spacing:0.02em;
                color:{COLORS['on_surface_variant']};
                text-align:center;
                max-width:80px;
                word-break:break-all;
            ">{name}</span>
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_low']};
            padding:32px;
            border-radius:12px;
            border: 1px solid rgba(197,197,211,0.1);
        ">
            <div style="
                display:flex;
                align-items:flex-start;
                justify-content:space-between;
                gap:12px;
                max-width:900px;
                margin:0 auto;
                flex-wrap:wrap;
            ">
                {items_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Status Badge
# ---------------------------------------------------------------------------

def status_badge(label: str, variant: str = "success") -> str:
    """Return HTML for an inline status badge. Variants: success, warning, error, neutral."""
    configs = {
        "success": {"bg": "#ECFDF5", "color": "#047857", "border": ""},
        "warning": {"bg": "#FEF3C7", "color": "#92400E", "border": ""},
        "error": {"bg": "#FEF2F2", "color": "#991B1B", "border": ""},
        "neutral": {"bg": "#F1F5F9", "color": "#475569", "border": ""},
        "favorable": {"bg": "#ECFDF5", "color": "#047857", "border": ""},
        "adverse": {"bg": "#FEF2F2", "color": "#991B1B", "border": ""},
    }
    c = configs.get(variant, configs["neutral"])
    return (
        f'<span style="'
        f"display:inline-block;padding:2px 10px;border-radius:4px;"
        f"background:{c['bg']};color:{c['color']};"
        f"font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;"
        f'">{label}</span>'
    )


# ---------------------------------------------------------------------------
# Custom Table (editorial style — alternating tonal rows, no horizontal lines)
# ---------------------------------------------------------------------------

def editorial_table(headers: list[str], rows: list[list[str]], align: list[str] | None = None) -> None:
    """Render a table matching the Stitch editorial design. No borders, tonal rows."""
    if align is None:
        align = ["left"] * len(headers)

    header_cells = ""
    for h, a in zip(headers, align):
        header_cells += f"""
        <th style="
            padding:16px 24px;
            font-size:10px;font-weight:700;
            text-transform:uppercase;letter-spacing:0.1em;
            color:{COLORS['on_surface_variant']};
            text-align:{a};
            background:{COLORS['surface_container_low']};
        ">{h}</th>
        """

    body_rows = ""
    for i, row in enumerate(rows):
        bg = f"background:rgba(241,243,255,0.3);" if i % 2 == 1 else ""
        cells = ""
        for val, a in zip(row, align):
            cells += f"""
            <td style="
                padding:16px 24px;
                font-size:13px;
                text-align:{a};
                {bg}
            ">{val}</td>
            """
        body_rows += f'<tr style="transition:background 0.15s;" onmouseover="this.style.background=\'rgba(59,130,246,0.04)\'" onmouseout="this.style.background=\'\'">{cells}</tr>'

    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_lowest']};
            border-radius:12px;
            overflow:hidden;
            box-shadow:0 1px 4px rgba(13,27,52,0.04);
            border: 1px solid rgba(197,197,211,0.1);
        ">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr>{header_cells}</tr></thead>
                <tbody>{body_rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Signal Badge Row
# ---------------------------------------------------------------------------

def signal_badges(items: list[tuple[str, str]]) -> None:
    """Row of signal badges like the FX mockup. Each item is (label, variant)."""
    badges_html = ""
    for label, variant in items:
        dot_color = "#10b981" if variant == "positive" else COLORS["error"]
        text_color = "#047857" if variant == "positive" else "#991B1B"
        border_color = "#D1FAE5" if variant == "positive" else "#FECACA"
        badges_html += f"""
        <div style="
            display:inline-flex;align-items:center;gap:6px;
            padding:6px 12px;
            background:white;border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);
            border:1px solid {border_color};
        ">
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


# ---------------------------------------------------------------------------
# Insight Card (bottom of FX page)
# ---------------------------------------------------------------------------

def insight_card(icon: str, title: str, description: str, accent_color: str = "#10b981") -> None:
    """Contextual insight card matching bottom of FX Stitch mockup."""
    st.markdown(
        f"""
        <div style="
            background:{COLORS['surface_container_low']};
            padding:32px;
            border-radius:12px;
            position:relative;
            overflow:hidden;
        ">
            <div style="font-size:28px;margin-bottom:16px;">{icon}</div>
            <h4 style="
                font-size:16px;font-weight:700;
                color:{COLORS['on_surface']};
                margin:0 0 8px 0;
            ">{title}</h4>
            <p style="
                font-size:13px;
                color:{COLORS['on_surface_variant']};
                line-height:1.6;
                margin:0;
            ">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Spacer
# ---------------------------------------------------------------------------

def spacer(height: int = 24) -> None:
    """Vertical spacer using the design system's spacing scale."""
    st.markdown(f'<div style="height:{height}px;"></div>', unsafe_allow_html=True)
