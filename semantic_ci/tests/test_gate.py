"""Tests for the CIGate."""

from collections.abc import Generator
from pathlib import Path

import pytest

from semantic_ci.diff import DiffConfig
from semantic_ci.gate import CIGate
from semantic_ci.snapshot import MetricRow, SnapshotStore


def _row(name: str, value: float, period: str = "2025-01-01") -> MetricRow:
    return MetricRow(
        metric_name=name,
        period=period,
        grain="monthly",
        dimension_name=None,
        dimension_value=None,
        metric_value=value,
    )


@pytest.fixture()
def store(tmp_path: Path) -> Generator[SnapshotStore, None, None]:
    db = tmp_path / "gate_test.duckdb"
    ss = SnapshotStore(str(db))
    yield ss
    ss.close()


class TestCIGate:
    def test_pass_when_no_drift(self, store: SnapshotStore, tmp_path: Path) -> None:
        """Exit code 0 when current matches baseline."""
        baseline = [_row("revenue", 1000), _row("aov", 50)]
        store.save_snapshot(baseline, label="baseline")

        gate = CIGate(store=store)
        code = gate.run(
            current_metrics=baseline,  # identical
            baseline_label="baseline",
            output_dir=str(tmp_path / "reports"),
        )
        assert code == 0

    def test_fail_on_critical_drift(self, store: SnapshotStore, tmp_path: Path) -> None:
        """Exit code 1 when critical drift is detected."""
        baseline = [_row("revenue", 1000)]
        store.save_snapshot(baseline, label="baseline")

        drifted = [_row("revenue", 1200)]  # 20% change
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        gate = CIGate(store=store, config=config)
        code = gate.run(
            current_metrics=drifted,
            baseline_label="baseline",
            output_dir=str(tmp_path / "reports"),
        )
        assert code == 1

    def test_warn_on_warning_drift(self, store: SnapshotStore, tmp_path: Path) -> None:
        """Exit code 2 when only warnings (no criticals) are detected."""
        baseline = [_row("revenue", 1000)]
        store.save_snapshot(baseline, label="baseline")

        warned = [_row("revenue", 1060)]  # 6% change
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        gate = CIGate(store=store, config=config)
        code = gate.run(
            current_metrics=warned,
            baseline_label="baseline",
            output_dir=str(tmp_path / "reports"),
        )
        assert code == 2

    def test_pass_when_no_baseline_exists(self, store: SnapshotStore) -> None:
        """Exit code 0 when no baseline exists (first run)."""
        metrics = [_row("revenue", 1000)]
        gate = CIGate(store=store)
        code = gate.run(current_metrics=metrics, baseline_label="baseline")
        assert code == 0

    def test_reports_written_to_output_dir(self, store: SnapshotStore, tmp_path: Path) -> None:
        """Gate writes pr_comment.md and full_report.md."""
        baseline = [_row("revenue", 1000)]
        store.save_snapshot(baseline, label="baseline")

        out = tmp_path / "reports"
        gate = CIGate(store=store)
        gate.run(
            current_metrics=baseline,
            baseline_label="baseline",
            output_dir=str(out),
        )
        assert (out / "pr_comment.md").exists()
        assert (out / "full_report.md").exists()

    def test_report_content_matches_drift(self, store: SnapshotStore, tmp_path: Path) -> None:
        """PR comment contains 'Failed' when critical drift occurs."""
        baseline = [_row("revenue", 1000)]
        store.save_snapshot(baseline, label="baseline")

        drifted = [_row("revenue", 1500)]  # 50%
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        out = tmp_path / "reports"
        gate = CIGate(store=store, config=config)
        gate.run(
            current_metrics=drifted,
            baseline_label="baseline",
            output_dir=str(out),
        )
        content = (out / "pr_comment.md").read_text()
        assert "Failed" in content
        assert "`revenue`" in content
