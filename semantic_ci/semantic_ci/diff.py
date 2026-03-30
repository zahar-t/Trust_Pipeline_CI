"""Diff engine: compare two metric snapshots and detect meaningful drift.

Supports absolute and percentage thresholds, and classifies drifts
as expected (within tolerance) or unexpected (potential regression).
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .snapshot import MetricRow


class DriftSeverity(StrEnum):
    """Classification levels for metric drift."""

    NONE = "none"
    INFO = "info"  # Change detected but within tolerance
    WARNING = "warning"  # Exceeds soft threshold
    CRITICAL = "critical"  # Exceeds hard threshold
    NEW = "new"  # Metric exists in current but not baseline
    REMOVED = "removed"  # Metric exists in baseline but not current


@dataclass
class MetricDiff:
    """The result of comparing a single metric across two snapshots."""

    metric_name: str
    period: str
    dimension_name: str | None
    dimension_value: str | None
    baseline_value: float | None
    current_value: float | None
    absolute_change: float | None
    pct_change: float | None
    severity: DriftSeverity
    explanation: str


@dataclass
class DiffConfig:
    """Thresholds for drift detection."""

    # Default percentage thresholds
    warning_pct: float = 0.05  # 5% change -> warning
    critical_pct: float = 0.10  # 10% change -> critical

    # Absolute thresholds (override pct for small values)
    min_absolute_change: float = 1.0  # Ignore changes smaller than this

    # Per-metric overrides: metric_name -> {warning_pct, critical_pct}
    metric_overrides: dict[str, dict[str, float]] = field(default_factory=dict)


def _metric_key(row: MetricRow) -> str:
    """Build a composite key for matching metrics across snapshots."""
    # Normalize period to date-only (first 10 chars) so that
    # "2025-01-01" and "2025-01-01 00:00:00" match correctly.
    period = row.period[:10] if row.period else row.period
    return f"{row.metric_name}|{period}|{row.dimension_name}|{row.dimension_value}"


def _compute_severity(
    pct_change: float | None,
    abs_change: float,
    config: DiffConfig,
    metric_name: str,
) -> DriftSeverity:
    """Classify drift severity based on thresholds."""
    # Check for per-metric overrides
    overrides = config.metric_overrides.get(metric_name, {})

    min_abs = overrides.get("min_absolute_change", config.min_absolute_change)
    if abs_change < min_abs:
        return DriftSeverity.NONE
    warn_pct = overrides.get("warning_pct", config.warning_pct)
    crit_pct = overrides.get("critical_pct", config.critical_pct)

    if pct_change is None:
        return DriftSeverity.INFO

    abs_pct = abs(pct_change)
    if abs_pct >= crit_pct:
        return DriftSeverity.CRITICAL
    elif abs_pct >= warn_pct:
        return DriftSeverity.WARNING
    else:
        return DriftSeverity.INFO


def _explain_drift(diff: MetricDiff) -> str:
    """Generate a human-readable explanation of a metric drift."""
    if diff.severity == DriftSeverity.NEW:
        return f"New metric: {diff.metric_name} = {diff.current_value}"
    if diff.severity == DriftSeverity.REMOVED:
        return f"Metric removed: {diff.metric_name} (was {diff.baseline_value})"
    if diff.severity == DriftSeverity.NONE:
        return "No meaningful change"

    direction = "increased" if (diff.absolute_change or 0) > 0 else "decreased"
    pct_str = f"{abs(diff.pct_change) * 100:.1f}%" if diff.pct_change is not None else "N/A"
    return f"{diff.metric_name} {direction} by {pct_str} ({diff.baseline_value:.2f} -> {diff.current_value:.2f})"


def _diff_single_key(
    b: MetricRow | None,
    c: MetricRow | None,
    config: DiffConfig,
) -> MetricDiff:
    """Compute the diff for a single metric key pair."""
    if b is None and c is not None:
        diff = MetricDiff(
            metric_name=c.metric_name,
            period=c.period,
            dimension_name=c.dimension_name,
            dimension_value=c.dimension_value,
            baseline_value=None,
            current_value=c.metric_value,
            absolute_change=None,
            pct_change=None,
            severity=DriftSeverity.NEW,
            explanation="",
        )
        diff.explanation = _explain_drift(diff)
        return diff

    if b is not None and c is None:
        diff = MetricDiff(
            metric_name=b.metric_name,
            period=b.period,
            dimension_name=b.dimension_name,
            dimension_value=b.dimension_value,
            baseline_value=b.metric_value,
            current_value=None,
            absolute_change=None,
            pct_change=None,
            severity=DriftSeverity.REMOVED,
            explanation="",
        )
        diff.explanation = _explain_drift(diff)
        return diff

    # Both exist -- compute change
    assert b is not None and c is not None
    abs_change = c.metric_value - b.metric_value
    pct_change: float | None = abs_change / abs(b.metric_value) if b.metric_value != 0 else None
    severity = _compute_severity(pct_change, abs(abs_change), config, b.metric_name)

    diff = MetricDiff(
        metric_name=b.metric_name,
        period=b.period,
        dimension_name=b.dimension_name,
        dimension_value=b.dimension_value,
        baseline_value=b.metric_value,
        current_value=c.metric_value,
        absolute_change=abs_change,
        pct_change=pct_change,
        severity=severity,
        explanation="",
    )
    diff.explanation = _explain_drift(diff)
    return diff


_SEVERITY_ORDER: dict[DriftSeverity, int] = {
    DriftSeverity.CRITICAL: 0,
    DriftSeverity.REMOVED: 1,
    DriftSeverity.WARNING: 2,
    DriftSeverity.NEW: 3,
    DriftSeverity.INFO: 4,
    DriftSeverity.NONE: 5,
}


def diff_snapshots(
    baseline: list[MetricRow],
    current: list[MetricRow],
    config: DiffConfig | None = None,
) -> list[MetricDiff]:
    """Compare two metric snapshots and return a list of diffs.

    Args:
        baseline: Metric values from the baseline snapshot (e.g., main branch).
        current: Metric values from the current snapshot (e.g., PR branch).
        config: Threshold configuration for drift detection.

    Returns:
        List of MetricDiff objects, sorted by severity (critical first).
    """
    if config is None:
        config = DiffConfig()

    baseline_map: dict[str, MetricRow] = {_metric_key(m): m for m in baseline}
    current_map: dict[str, MetricRow] = {_metric_key(m): m for m in current}

    all_keys = set(baseline_map.keys()) | set(current_map.keys())
    diffs = [_diff_single_key(baseline_map.get(key), current_map.get(key), config) for key in all_keys]

    diffs.sort(key=lambda d: _SEVERITY_ORDER.get(d.severity, 99))
    return diffs


def summarize_diffs(
    diffs: list[MetricDiff],
) -> dict[str, Any]:
    """Aggregate diff results into a summary dict."""
    by_severity: dict[str, list[MetricDiff]] = {}
    for d in diffs:
        by_severity.setdefault(d.severity.value, []).append(d)

    return {
        "total_metrics": len(diffs),
        "critical": len(by_severity.get("critical", [])),
        "warning": len(by_severity.get("warning", [])),
        "info": len(by_severity.get("info", [])),
        "new": len(by_severity.get("new", [])),
        "removed": len(by_severity.get("removed", [])),
        "unchanged": len(by_severity.get("none", [])),
        "pass": len(by_severity.get("critical", [])) == 0,
    }
