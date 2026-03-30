"""Tests for the SnapshotStore."""

from collections.abc import Generator
from pathlib import Path

import pytest

from semantic_ci.snapshot import MetricRow, SnapshotStore


def _sample_metrics() -> list[MetricRow]:
    return [
        MetricRow(
            metric_name="revenue",
            period="2025-01-01",
            grain="monthly",
            dimension_name=None,
            dimension_value=None,
            metric_value=1000.0,
        ),
        MetricRow(
            metric_name="revenue",
            period="2025-02-01",
            grain="monthly",
            dimension_name=None,
            dimension_value=None,
            metric_value=1200.0,
        ),
        MetricRow(
            metric_name="aov",
            period="2025-01-01",
            grain="monthly",
            dimension_name="country",
            dimension_value="DE",
            metric_value=55.0,
        ),
    ]


@pytest.fixture()
def store(tmp_path: Path) -> Generator[SnapshotStore, None, None]:
    db = tmp_path / "test_snapshots.duckdb"
    ss = SnapshotStore(str(db))
    yield ss
    ss.close()


class TestSnapshotStore:
    def test_create_store(self, store: SnapshotStore) -> None:
        """Store can be created and tables exist."""
        tables = store.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "metric_snapshots" in table_names
        assert "snapshot_runs" in table_names

    def test_save_and_retrieve_snapshot(self, store: SnapshotStore) -> None:
        """Metrics round-trip through save and retrieve."""
        metrics = _sample_metrics()
        run = store.save_snapshot(metrics, label="test-run")

        assert run.n_metrics == 3
        assert run.label == "test-run"

        retrieved = store.get_metrics_for_run(run.run_id)
        assert len(retrieved) == 3

        # Check values match
        by_name = {(m.metric_name, m.period): m for m in retrieved}
        assert by_name[("revenue", "2025-01-01 00:00:00")].metric_value == 1000.0
        assert by_name[("revenue", "2025-02-01 00:00:00")].metric_value == 1200.0
        assert by_name[("aov", "2025-01-01 00:00:00")].dimension_value == "DE"

    def test_list_runs(self, store: SnapshotStore) -> None:
        """list_runs returns saved runs in reverse chronological order."""
        metrics = _sample_metrics()
        store.save_snapshot(metrics, label="first")
        store.save_snapshot(metrics, label="second")

        runs = store.list_runs()
        assert len(runs) == 2
        # Most recent first
        assert runs[0]["label"] == "second"
        assert runs[1]["label"] == "first"
        assert runs[0]["n_metrics"] == 3

    def test_get_latest_run_by_label(self, store: SnapshotStore) -> None:
        """get_latest_run filters by label."""
        metrics = _sample_metrics()
        store.save_snapshot(metrics, label="baseline")
        store.save_snapshot(metrics, label="pr-123")

        latest_baseline = store.get_latest_run(label="baseline")
        assert latest_baseline is not None

        latest_pr = store.get_latest_run(label="pr-123")
        assert latest_pr is not None
        assert latest_baseline != latest_pr

    def test_get_latest_run_none_when_empty(self, store: SnapshotStore) -> None:
        """get_latest_run returns None for empty store."""
        assert store.get_latest_run() is None

    def test_empty_metrics_for_nonexistent_run(self, store: SnapshotStore) -> None:
        """get_metrics_for_run returns empty list for unknown run_id."""
        result = store.get_metrics_for_run("nonexistent")
        assert result == []

    def test_dimension_round_trip(self, store: SnapshotStore) -> None:
        """Dimension name/value survive the round trip."""
        metrics = [
            MetricRow(
                metric_name="conversion_rate",
                period="2025-03-01",
                grain="monthly",
                dimension_name="channel",
                dimension_value="organic",
                metric_value=0.032,
            ),
        ]
        run = store.save_snapshot(metrics, label="dim-test")
        retrieved = store.get_metrics_for_run(run.run_id)
        assert len(retrieved) == 1
        assert retrieved[0].dimension_name == "channel"
        assert retrieved[0].dimension_value == "organic"
        assert retrieved[0].metric_value == pytest.approx(0.032)
