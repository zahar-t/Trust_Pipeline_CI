"""Reusable Plotly chart builders with a consistent colour palette."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

if TYPE_CHECKING:
    import pandas as pd

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

CONSENT_COLORS: dict[str, str] = {
    "full": "#2E6B5A",          # pine / signal-ok
    "analytics_only": "#E8B931", # signal-warn
    "minimal": "#B2382F",        # signal-bad
}

REVENUE_PRIMARY = "#B5722F"    # copper-500
REVENUE_SECONDARY = "#D49A5C"  # copper-300

# Plotly template defaults
_LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    font=dict(size=12),
)


# ---------------------------------------------------------------------------
# KPI card
# ---------------------------------------------------------------------------


def kpi_card(label: str, value: str, delta: str | None = None, delta_color: str = "normal") -> None:
    """Render an ``st.metric`` KPI card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Line chart
# ---------------------------------------------------------------------------


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """Return a Plotly line chart."""
    fig = px.line(df, x=x, y=y, color=color, title=title, color_discrete_map=color_map)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


# ---------------------------------------------------------------------------
# Stacked area chart
# ---------------------------------------------------------------------------


def stacked_area(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """Return a Plotly stacked area chart."""
    fig = px.area(df, x=x, y=y, color=color, title=title, color_discrete_map=color_map)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


# ---------------------------------------------------------------------------
# Bar chart
# ---------------------------------------------------------------------------


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """Return a Plotly stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, color_discrete_map=color_map)
    fig.update_layout(**_LAYOUT_DEFAULTS, barmode="stack")
    return fig


# ---------------------------------------------------------------------------
# Grouped bar chart
# ---------------------------------------------------------------------------


def grouped_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """Return a Plotly grouped bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode="group", color_discrete_map=color_map)
    fig.update_layout(**_LAYOUT_DEFAULTS, barmode="group")
    return fig
