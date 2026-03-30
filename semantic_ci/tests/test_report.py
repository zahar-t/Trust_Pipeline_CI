"""Tests for the report generator."""

from semantic_ci.diff import DiffConfig, diff_snapshots
from semantic_ci.report import generate_pr_comment
from semantic_ci.snapshot import MetricRow


def _row(name: str, value: float, period: str = "2025-01-01") -> MetricRow:
    return MetricRow(
        metric_name=name,
        period=period,
        grain="monthly",
        dimension_name=None,
        dimension_value=None,
        metric_value=value,
    )


class TestGeneratePrComment:
    def test_passing_report_contains_header(self) -> None:
        """A passing diff produces a 'Passed' header."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1000)]
        diffs = diff_snapshots(baseline, current)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "Metrics Check Passed" in md

    def test_failing_report_contains_header(self) -> None:
        """A failing diff produces a 'Failed' header."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1200)]  # 20% change
        config = DiffConfig(critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "Metrics Check Failed" in md

    def test_summary_table_present(self) -> None:
        """The report includes a summary table with status counts."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1060)]
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "### Summary" in md
        assert "| Critical |" in md
        assert "| Warning |" in md

    def test_significant_changes_section(self) -> None:
        """Critical/warning diffs appear under 'Significant Changes'."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1150)]  # 15% change
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "### Significant Changes" in md
        assert "`revenue`" in md
        assert "+15.0%" in md

    def test_no_significant_changes_section_when_clean(self) -> None:
        """No 'Significant Changes' section when all metrics are clean."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1000)]
        diffs = diff_snapshots(baseline, current)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "### Significant Changes" not in md

    def test_baseline_and_current_labels(self) -> None:
        """Labels appear in the report when provided."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1000)]
        diffs = diff_snapshots(baseline, current)
        md = generate_pr_comment(
            diffs,
            "run-aaa",
            "run-bbb",
            baseline_label="main",
            current_label="pr-42",
        )
        assert "`main`" in md
        assert "`pr-42`" in md

    def test_collapsible_details_section(self) -> None:
        """Full diff details are inside a collapsible section."""
        baseline = [_row("revenue", 1000)]
        current = [_row("revenue", 1060)]
        config = DiffConfig(warning_pct=0.05, critical_pct=0.10)
        diffs = diff_snapshots(baseline, current, config)
        md = generate_pr_comment(diffs, "run-aaa", "run-bbb")
        assert "<details>" in md
        assert "</details>" in md

    def test_footer_present(self) -> None:
        """The report ends with the semantic-ci attribution."""
        diffs = diff_snapshots([_row("x", 1)], [_row("x", 1)])
        md = generate_pr_comment(diffs, "a", "b")
        assert "semantic-ci" in md
