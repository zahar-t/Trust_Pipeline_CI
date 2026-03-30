"""Consent Impact Simulator.

Re-weights historical per-consent-level metrics according to hypothetical
consent distributions to project aggregate KPIs under different scenarios.
"""

from __future__ import annotations

import pandas as pd

from .scenarios import CONSENT_LEVELS, ConsentDistribution, validate_distribution

# Metrics that scale linearly with the number of users in each consent tier.
VOLUME_METRICS: list[str] = [
    "n_orders",
    "gross_revenue_eur",
    "net_revenue_eur",
    "unique_customers",
    "total_sessions",
    "sessions_with_pageview",
    "sessions_with_cart",
    "sessions_with_checkout",
    "sessions_with_purchase",
]

# Rate metrics that should be recomputed from weighted volumes.
RATE_METRICS: list[str] = [
    "session_conversion_rate",
    "cart_to_purchase_rate",
    "avg_order_value_eur",
]

FULL_VISIBILITY: ConsentDistribution = {"full": 1.0, "analytics_only": 0.0, "minimal": 0.0}


class ConsentImpactSimulator:
    """Simulate aggregate metrics under different consent distributions.

    The simulator stores per-consent-level, per-month *rate profiles*
    derived from the historical ``fct_consent_impact`` data.  Given a
    new consent distribution it re-weights the per-level volumes
    proportionally and re-derives rate metrics.

    Args:
        impact_df: Historical data from ``fct_consent_impact``.
    """

    def __init__(self, impact_df: pd.DataFrame) -> None:
        """Initialize the simulator with historical consent impact data."""
        self._raw = impact_df.copy()
        self._months: list[str] = sorted(self._raw["report_month"].unique())

        # Pre-compute per-level totals across all months so we know each
        # level's historical share of volume.
        self._level_totals: dict[str, pd.Series] = {}
        for level in CONSENT_LEVELS:
            level_df = self._raw[self._raw["consent_level"] == level]
            self._level_totals[level] = level_df[VOLUME_METRICS].sum()

        # Per-level, per-month data pivoted for quick access.
        self._monthly: dict[str, pd.DataFrame] = {}
        for level in CONSENT_LEVELS:
            ldf = self._raw[self._raw["consent_level"] == level].copy()
            ldf = ldf.set_index("report_month").sort_index()
            self._monthly[level] = ldf

    @property
    def months(self) -> list[str]:
        """Sorted list of report months available in the historical data."""
        return list(self._months)

    def _actual_distribution(self) -> ConsentDistribution:
        """Compute the actual consent distribution from historical session volumes."""
        total_sessions_by_level = {level: self._level_totals[level]["total_sessions"] for level in CONSENT_LEVELS}
        grand_total = sum(total_sessions_by_level.values())
        if grand_total == 0:
            return {level: 1.0 / len(CONSENT_LEVELS) for level in CONSENT_LEVELS}
        return {level: total_sessions_by_level[level] / grand_total for level in CONSENT_LEVELS}

    def _aggregate_month(
        self,
        month: str,
        scenario: ConsentDistribution,
        actual_dist: ConsentDistribution,
    ) -> dict[str, float]:
        """Aggregate volume metrics for a single month under *scenario*."""
        agg: dict[str, float] = {m: 0.0 for m in VOLUME_METRICS}
        for level in CONSENT_LEVELS:
            if month not in self._monthly[level].index:
                continue
            hist_share = actual_dist.get(level, 0.0)
            if hist_share == 0:
                continue
            level_row = self._monthly[level].loc[month]
            scale = scenario[level] / hist_share
            for metric in VOLUME_METRICS:
                val = level_row[metric]
                agg[metric] += float(val) * scale if pd.notna(val) else 0.0
        return agg

    @staticmethod
    def _derive_rate_metrics(agg: dict[str, float]) -> dict[str, float]:
        """Compute rate metrics from aggregated volumes."""
        return {
            "session_conversion_rate": (
                agg["sessions_with_purchase"] / agg["total_sessions"] if agg["total_sessions"] > 0 else 0.0
            ),
            "cart_to_purchase_rate": (
                agg["sessions_with_purchase"] / agg["sessions_with_cart"] if agg["sessions_with_cart"] > 0 else 0.0
            ),
            "avg_order_value_eur": (agg["gross_revenue_eur"] / agg["n_orders"] if agg["n_orders"] > 0 else 0.0),
        }

    def simulate(
        self,
        scenario: ConsentDistribution,
        months: list[str] | None = None,
    ) -> pd.DataFrame:
        """Project aggregate metrics under *scenario*.

        For each month the simulator takes per-level volume metrics,
        scales them by the ratio ``scenario_proportion / historical_proportion``,
        sums across levels, and re-derives rate metrics.

        Args:
            scenario: Target consent distribution.
            months: Subset of months to simulate. ``None`` means all.

        Returns:
            DataFrame with one row per month and columns for every
            projected metric.
        """
        validate_distribution(scenario)
        actual_dist = self._actual_distribution()
        target_months = months if months is not None else self._months

        rows: list[dict[str, object]] = []
        for month in target_months:
            agg = self._aggregate_month(month, scenario, actual_dist)
            row: dict[str, object] = {"report_month": month, **agg, **self._derive_rate_metrics(agg)}
            rows.append(row)

        return pd.DataFrame(rows)

    def measurement_gap(self, scenario: ConsentDistribution) -> pd.DataFrame:
        """Compare *scenario* against a full-visibility baseline.

        The measurement gap quantifies how much signal is lost when not
        all users grant full consent.

        Args:
            scenario: Target consent distribution.

        Returns:
            DataFrame with columns metric_name, scenario_value,
            baseline_value, gap_pct for each volume and rate metric.
        """
        baseline = self.simulate(FULL_VISIBILITY)
        projected = self.simulate(scenario)

        metrics_to_compare = VOLUME_METRICS + RATE_METRICS
        rows: list[dict[str, object]] = []
        for metric in metrics_to_compare:
            b_val = float(baseline[metric].sum()) if metric in VOLUME_METRICS else float(baseline[metric].mean())
            s_val = float(projected[metric].sum()) if metric in VOLUME_METRICS else float(projected[metric].mean())
            gap_pct = ((b_val - s_val) / b_val * 100.0) if b_val != 0 else 0.0
            rows.append(
                {
                    "metric_name": metric,
                    "scenario_value": round(s_val, 4),
                    "baseline_value": round(b_val, 4),
                    "measurement_gap_pct": round(gap_pct, 2),
                }
            )
        return pd.DataFrame(rows)
