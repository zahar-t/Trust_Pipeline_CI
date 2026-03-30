"""Feature extraction from the dbt DuckDB warehouse.

Reads ``fct_consent_impact`` and ``dim_customers`` to provide the
historical per-consent-level metrics consumed by the simulator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import duckdb
import pandas as pd  # noqa: TC002 -- used at runtime

if TYPE_CHECKING:
    from pathlib import Path


def connect(db_path: str | Path) -> duckdb.DuckDBPyConnection:
    """Open a read-only connection to the DuckDB warehouse.

    Args:
        db_path: Filesystem path to the DuckDB file.

    Returns:
        An open DuckDB connection.
    """
    return duckdb.connect(str(db_path), read_only=True)


def load_consent_impact(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Load the full ``fct_consent_impact`` table.

    Args:
        con: Active DuckDB connection.

    Returns:
        DataFrame with one row per (report_month, consent_level).
    """
    query = """
        SELECT
            report_month,
            consent_level,
            n_orders,
            gross_revenue_eur,
            net_revenue_eur,
            avg_order_value_eur,
            unique_customers,
            total_sessions,
            sessions_with_pageview,
            sessions_with_cart,
            sessions_with_checkout,
            sessions_with_purchase,
            session_conversion_rate,
            cart_to_purchase_rate
        FROM fct_consent_impact
        ORDER BY report_month, consent_level
    """
    return con.sql(query).fetchdf()


def load_consent_distribution(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    """Compute the actual consent distribution from ``dim_customers``.

    Args:
        con: Active DuckDB connection.

    Returns:
        Mapping of consent_level to its proportion of total customers.
    """
    query = """
        SELECT
            consent_level,
            COUNT(*) AS cnt
        FROM dim_customers
        GROUP BY consent_level
    """
    df = con.sql(query).fetchdf()
    total = df["cnt"].sum()
    return dict(zip(df["consent_level"], df["cnt"] / total, strict=False))


def load_features(db_path: str | Path) -> tuple[pd.DataFrame, dict[str, float]]:
    """High-level loader: returns impact metrics and consent distribution.

    Args:
        db_path: Path to the DuckDB warehouse file.

    Returns:
        A tuple of (impact_df, actual_consent_distribution).
    """
    con = connect(db_path)
    try:
        impact_df = load_consent_impact(con)
        dist = load_consent_distribution(con)
    finally:
        con.close()
    return impact_df, dist
