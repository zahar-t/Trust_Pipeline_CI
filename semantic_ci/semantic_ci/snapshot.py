"""Snapshot engine: capture metric values from a dbt project's metric_definitions table.

Stores snapshots in a local DuckDB file (or BigQuery table) so they can be
diffed across runs -- e.g., before/after a PR.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

SNAPSHOT_DB_DEFAULT: str = ".semantic_ci/snapshots.duckdb"

SNAPSHOT_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS metric_snapshots (
    snapshot_id     VARCHAR PRIMARY KEY,
    run_id          VARCHAR NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    git_sha         VARCHAR,
    git_branch      VARCHAR,
    label           VARCHAR,
    metric_name     VARCHAR NOT NULL,
    period          TIMESTAMP NOT NULL,
    grain           VARCHAR,
    dimension_name  VARCHAR,
    dimension_value VARCHAR,
    metric_value    DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshot_runs (
    run_id      VARCHAR PRIMARY KEY,
    created_at  TIMESTAMP NOT NULL,
    git_sha     VARCHAR,
    git_branch  VARCHAR,
    label       VARCHAR,
    n_metrics   INTEGER,
    metadata    VARCHAR
);
"""


@dataclass
class MetricRow:
    """A single metric data point with its dimension and period."""

    metric_name: str
    period: str
    grain: str
    dimension_name: str | None
    dimension_value: str | None
    metric_value: float


@dataclass
class SnapshotRun:
    """Metadata for a single snapshot run."""

    run_id: str
    created_at: datetime
    git_sha: str | None
    git_branch: str | None
    label: str | None
    n_metrics: int


def _generate_run_id(git_sha: str | None = None) -> str:
    """Generate a deterministic-ish run ID from timestamp and git sha."""
    now = datetime.now(UTC).isoformat()
    seed = f"{now}-{git_sha or 'local'}"
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


def _generate_snapshot_id(run_id: str, row: MetricRow) -> str:
    """Generate a unique ID for a metric row within a run."""
    key = f"{run_id}-{row.metric_name}-{row.period}-{row.dimension_name}-{row.dimension_value}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class SnapshotStore:
    """Local DuckDB-backed snapshot storage."""

    def __init__(self, db_path: str = SNAPSHOT_DB_DEFAULT) -> None:
        """Initialize the snapshot store, creating tables if needed."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.conn: duckdb.DuckDBPyConnection = duckdb.connect(str(self.db_path))
            self.conn.execute(SNAPSHOT_SCHEMA)
        except duckdb.Error as exc:
            raise RuntimeError(f"Failed to open snapshot store at {self.db_path}: {exc}") from exc

    def save_snapshot(
        self,
        metrics: list[MetricRow],
        git_sha: str | None = None,
        git_branch: str | None = None,
        label: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SnapshotRun:
        """Store a batch of metric values as a snapshot run."""
        run_id = _generate_run_id(git_sha)
        now = datetime.now(UTC)

        # Insert run record
        self.conn.execute(
            """
            INSERT INTO snapshot_runs
                (run_id, created_at, git_sha, git_branch,
                 label, n_metrics, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                now,
                git_sha,
                git_branch,
                label,
                len(metrics),
                json.dumps(metadata) if metadata else None,
            ],
        )

        # Insert metric rows
        for row in metrics:
            sid = _generate_snapshot_id(run_id, row)
            self.conn.execute(
                """
                INSERT INTO metric_snapshots
                    (snapshot_id, run_id, created_at, git_sha,
                     git_branch, label, metric_name, period,
                     grain, dimension_name, dimension_value,
                     metric_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    sid,
                    run_id,
                    now,
                    git_sha,
                    git_branch,
                    label,
                    row.metric_name,
                    row.period,
                    row.grain,
                    row.dimension_name,
                    row.dimension_value,
                    row.metric_value,
                ],
            )

        run = SnapshotRun(
            run_id=run_id,
            created_at=now,
            git_sha=git_sha,
            git_branch=git_branch,
            label=label,
            n_metrics=len(metrics),
        )
        print(f"Snapshot saved: {run_id} ({len(metrics)} metrics)")
        return run

    def get_latest_run(self, label: str | None = None) -> str | None:
        """Get the most recent run_id, optionally filtered by label."""
        query = "SELECT run_id FROM snapshot_runs"
        params: list[str] = []
        if label:
            query += " WHERE label = ?"
            params.append(label)
        query += " ORDER BY created_at DESC LIMIT 1"

        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else None

    def get_metrics_for_run(self, run_id: str) -> list[MetricRow]:
        """Retrieve all metric values for a given run."""
        rows = self.conn.execute(
            """
            SELECT metric_name, period, grain,
                   dimension_name, dimension_value, metric_value
            FROM metric_snapshots
            WHERE run_id = ?
            ORDER BY metric_name, period,
                     dimension_name, dimension_value
            """,
            [run_id],
        ).fetchall()

        return [
            MetricRow(
                metric_name=r[0],
                period=str(r[1]),
                grain=r[2],
                dimension_name=r[3],
                dimension_value=r[4],
                metric_value=r[5],
            )
            for r in rows
        ]

    def list_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent snapshot runs."""
        rows = self.conn.execute(
            """
            SELECT run_id, created_at, git_sha,
                   git_branch, label, n_metrics
            FROM snapshot_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()

        return [
            {
                "run_id": r[0],
                "created_at": str(r[1]),
                "git_sha": r[2],
                "git_branch": r[3],
                "label": r[4],
                "n_metrics": r[5],
            }
            for r in rows
        ]

    def close(self) -> None:
        """Close the underlying DuckDB connection."""
        self.conn.close()
