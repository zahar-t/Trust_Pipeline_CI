"""Shared sidebar filters used across dashboard pages."""

from __future__ import annotations

import datetime
from typing import Any

import streamlit as st

from components.db import query


def _safe_date(val: Any) -> datetime.date:
    """Coerce various date-like values to ``datetime.date``."""
    if hasattr(val, "date"):
        return val.date()  # type: ignore[no-any-return]
    if isinstance(val, datetime.date):
        return val
    return datetime.date.fromisoformat(str(val)[:10])


def render_sidebar_filters() -> dict[str, Any]:
    """Draw shared filters in the sidebar and return the current selections.

    Returns a dict with keys:
        - ``date_range``: tuple of (start_date, end_date) as ``datetime.date``
        - ``countries``: list of selected country codes (empty = all)
        - ``consent_levels``: list of selected consent levels (empty = all)
    """
    st.sidebar.header("Filters")

    # -- date range -----------------------------------------------------------
    date_bounds = query("SELECT min(order_date) AS mn, max(order_date) AS mx FROM fct_orders")
    if date_bounds.empty or date_bounds["mn"].iloc[0] is None:
        min_date = datetime.date(2024, 1, 1)
        max_date = datetime.date.today()
    else:
        min_date = _safe_date(date_bounds["mn"].iloc[0])
        max_date = _safe_date(date_bounds["mx"].iloc[0])

    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    # date_input may return a single date when the user has only picked one end
    if isinstance(date_range, list | tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    # -- countries ------------------------------------------------------------
    countries_df = query("SELECT DISTINCT country_code FROM fct_orders WHERE country_code IS NOT NULL ORDER BY 1")
    all_countries: list[str] = countries_df["country_code"].tolist() if not countries_df.empty else []
    selected_countries: list[str] = st.sidebar.multiselect("Country", options=all_countries)

    # -- consent level --------------------------------------------------------
    consent_df = query(
        "SELECT DISTINCT consent_level_at_order FROM fct_orders WHERE consent_level_at_order IS NOT NULL ORDER BY 1"
    )
    all_consent: list[str] = consent_df["consent_level_at_order"].tolist() if not consent_df.empty else []
    selected_consent: list[str] = st.sidebar.multiselect("Consent level", options=all_consent)

    return {
        "date_range": (start_date, end_date),
        "countries": selected_countries,
        "consent_levels": selected_consent,
    }


def build_where_clause(
    filters: dict[str, Any],
    date_col: str = "order_date",
    country_col: str = "country_code",
    consent_col: str = "consent_level_at_order",
) -> str:
    """Build a SQL WHERE clause string (including the WHERE keyword) from *filters*.

    Returns an empty string when no filters are active.
    """
    clauses: list[str] = []

    start, end = filters["date_range"]
    clauses.append(f"{date_col} BETWEEN '{start}' AND '{end}'")

    if filters["countries"]:
        quoted = ", ".join(f"'{c}'" for c in filters["countries"])
        clauses.append(f"{country_col} IN ({quoted})")

    if filters["consent_levels"]:
        quoted = ", ".join(f"'{c}'" for c in filters["consent_levels"])
        clauses.append(f"{consent_col} IN ({quoted})")

    return " WHERE " + " AND ".join(clauses) if clauses else ""
