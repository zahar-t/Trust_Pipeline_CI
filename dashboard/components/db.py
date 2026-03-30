"""DuckDB read-only connection singleton for the Metric Trust Pipeline dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Main pipeline database
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "dbt_project" / "target" / "dev.duckdb")


@st.cache_resource
def _get_connection() -> duckdb.DuckDBPyConnection:
    """Return a read-only DuckDB connection (cached as a Streamlit resource)."""
    db_path = os.environ.get("DUCKDB_PATH", _DEFAULT_DB_PATH)
    return duckdb.connect(db_path, read_only=True)


@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    """Execute *sql* against the pipeline DuckDB and return a DataFrame."""
    con = _get_connection()
    try:
        return con.execute(sql).fetchdf()
    except Exception as exc:
        st.error(f"Query failed: {exc}")
        return pd.DataFrame()


def table_exists(table_name: str) -> bool:
    """Check whether *table_name* exists in the pipeline database."""
    df = query(f"SELECT count(*) AS n FROM information_schema.tables WHERE table_name = '{table_name}'")  # nosec B608
    return bool(len(df) and df["n"].iloc[0] > 0)


# ---------------------------------------------------------------------------
# Semantic-CI snapshot store (separate DuckDB file, may not exist)
# ---------------------------------------------------------------------------

_SNAPSHOT_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / ".semantic_ci" / "snapshots.duckdb")


@st.cache_resource
def _get_snapshot_connection() -> duckdb.DuckDBPyConnection | None:
    """Return a read-only connection to the semantic-ci snapshot store, or None."""
    path = os.environ.get("SNAPSHOT_DUCKDB_PATH", _SNAPSHOT_DB_PATH)
    if not Path(path).exists():
        return None
    return duckdb.connect(path, read_only=True)


@st.cache_data(ttl=300)
def snapshot_query(sql: str) -> pd.DataFrame | None:
    """Query the semantic-ci snapshot store. Returns None when the store is missing."""
    con = _get_snapshot_connection()
    if con is None:
        return None
    try:
        return con.execute(sql).fetchdf()
    except Exception as exc:
        st.error(f"Snapshot query failed: {exc}")
        return None


def snapshot_store_available() -> bool:
    """Return True when the semantic-ci snapshot DuckDB exists."""
    return _get_snapshot_connection() is not None
