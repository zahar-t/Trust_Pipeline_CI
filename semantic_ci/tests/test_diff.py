"""Tests for the diff engine."""

from semantic_ci.diff import (
    DiffConfig,
    DriftSeverity,
    diff_snapshots,
    summarize_diffs,
)
from semantic_ci.snapshot import MetricRow


def _row(
    name: str, value: float, period: str = "2025-01-01", dim_name: str | None = None, dim_value: str | None = None
) -> MetricRow:
    return MetricRow(
        metric_name=name,
        period=period,
        grain="monthly",
        dimension_name=dim_name,
        dimension_value=dim_value,
        metric_value=value,
    )


class TestDiffSnapshots:
    def test_no_change(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1000)]
        diffs = diff_snapshots(baseline, current)
        assert len(diffs) == 1
        assert diffs[0].severity == DriftSeverity.NONE

    def test_small_change_below_threshold(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1010)]  # 1% change
        config = DiffConfig(warning_pct=0.05, min_absolute_change=1.0)
        diffs = diff_snapshots(baseline, current, config)
        assert diffs[0].severity == DriftSeverity.INFO

    def test_warning_threshold(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1060)]  # 6% change
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        assert diffs[0].severity == DriftSeverity.WARNING

    def test_critical_threshold(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1120)]  # 12% change
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        assert diffs[0].severity == DriftSeverity.CRITICAL

    def test_new_metric(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1000), _row("aov", 50)]
        diffs = diff_snapshots(baseline, current)
        new_diffs = [d for d in diffs if d.severity == DriftSeverity.NEW]
        assert len(new_diffs) == 1
        assert new_diffs[0].metric_name == "aov"

    def test_removed_metric(self) -> None:
        baseline = [_row("revenue", 1000), _row("aov", 50)]
        current = [_row("revenue", 1000)]
        diffs = diff_snapshots(baseline, current)
        removed = [d for d in diffs if d.severity == DriftSeverity.REMOVED]
        assert len(removed) == 1
        assert removed[0].metric_name == "aov"

    def test_dimension_aware_diff(self) -> None:
        baseline = [
            _row("revenue", 500, dim_name="country", dim_value="PT"),
            _row("revenue", 300, dim_name="country", dim_value="DE"),
        ]
        current = [
            _row("revenue", 500, dim_name="country", dim_value="PT"),
            _row("revenue", 350, dim_name="country", dim_value="DE"),  # +16.7%
        ]
        config = DiffConfig(warning_pct=0.05, critical_pct=0.15)
        diffs = diff_snapshots(baseline, current, config)
        de_diff = next(d for d in diffs if d.dimension_value == "DE")
        assert de_diff.severity == DriftSeverity.CRITICAL

    def test_per_metric_override(self) -> None:
        baseline = [_row("refund_rate", 0.05)]
        current = [_row("refund_rate", 0.06)]  # 20% change
        config = DiffConfig(
            warning_pct=0.05,
            critical_pct=0.10,
            metric_overrides={
                "refund_rate": {
                    "warning_pct": 0.25,
                    "critical_pct": 0.50,
                    "min_absolute_change": 0.001,
                }
            },
        )
        diffs = diff_snapshots(baseline, current, config)
        # 20% is below the override warning of 25%
        assert diffs[0].severity == DriftSeverity.INFO

    def test_negative_change(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 880)]  # -12%
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        assert diffs[0].severity == DriftSeverity.CRITICAL
        assert diffs[0].absolute_change is not None
        assert diffs[0].absolute_change < 0


class TestSummarizeDiffs:
    def test_pass_when_no_critical(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1040)]  # 4% — below warning
        diffs = diff_snapshots(baseline, current)
        summary = summarize_diffs(diffs)
        assert summary["pass"] is True

    def test_fail_when_critical(self) -> None:
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1200)]  # 20%
        config = DiffConfig(critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        summary = summarize_diffs(diffs)
        assert summary["pass"] is False
        assert summary["critical"] == 1
