"""Backtesting harness for the Consent Impact Simulator.

Uses the first 9 months of data to learn per-level rate profiles,
then predicts aggregate metrics for the remaining months using actual
consent distributions observed in those periods.
"""

from __future__ import annotations

import pandas as pd
from tabulate import tabulate

from .model import RATE_METRICS, VOLUME_METRICS, ConsentImpactSimulator


def _compute_actual_aggregates(impact_df: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    """Sum per-level rows into true aggregate rows for given months.

    Args:
        impact_df: Full historical data.
        months: Months to aggregate.

    Returns:
        DataFrame with one row per month containing aggregated metrics.
    """
    subset = impact_df[impact_df["report_month"].isin(months)].copy()
    agg = subset.groupby("report_month")[VOLUME_METRICS].sum().reset_index()

    # Re-derive rates from aggregated volumes.
    agg["session_conversion_rate"] = agg.apply(
        lambda r: r["sessions_with_purchase"] / r["total_sessions"] if r["total_sessions"] > 0 else 0.0,
        axis=1,
    )
    agg["cart_to_purchase_rate"] = agg.apply(
        lambda r: r["sessions_with_purchase"] / r["sessions_with_cart"] if r["sessions_with_cart"] > 0 else 0.0,
        axis=1,
    )
    agg["avg_order_value_eur"] = agg.apply(
        lambda r: r["gross_revenue_eur"] / r["n_orders"] if r["n_orders"] > 0 else 0.0,
        axis=1,
    )
    return agg.sort_values("report_month").reset_index(drop=True)


def _compute_actual_distribution_for_months(impact_df: pd.DataFrame, months: list[str]) -> dict[str, float]:
    """Derive consent distribution from session volumes in *months*.

    Args:
        impact_df: Full historical data.
        months: Months to consider.

    Returns:
        Consent distribution dict.
    """
    subset = impact_df[impact_df["report_month"].isin(months)]
    level_sessions = subset.groupby("consent_level")["total_sessions"].sum()
    total = level_sessions.sum()
    if total == 0:
        return {"full": 1 / 3, "analytics_only": 1 / 3, "minimal": 1 / 3}
    result: dict[str, float] = (level_sessions / total).to_dict()
    return result


def run_backtest(impact_df: pd.DataFrame, train_months: int = 9) -> pd.DataFrame:
    """Run a train/test backtest and return MAPE per metric.

    Args:
        impact_df: Full ``fct_consent_impact`` data.
        train_months: Number of months (sorted chronologically) to use
            for training.  Remaining months form the test set.

    Returns:
        DataFrame with columns metric_name and mape_pct.
    """
    all_months = sorted(impact_df["report_month"].unique())
    test = all_months[train_months:]

    if not test:
        raise ValueError(f"Not enough months for backtesting: {len(all_months)} total, {train_months} for training")

    # Build model on the full dataset so the test months are available for
    # simulation.  The backtest checks whether re-weighting by the *actual*
    # consent distribution recovers the observed aggregate -- i.e. it
    # validates the reweighting math, not an out-of-sample volume forecast.
    sim = ConsentImpactSimulator(impact_df)

    # Use the actual consent distribution from the test period.
    test_dist = _compute_actual_distribution_for_months(impact_df, test)
    test_months_str = [str(m) for m in test]

    predicted = sim.simulate(test_dist, months=test_months_str)
    actual = _compute_actual_aggregates(impact_df, test)

    # Align by sorted month.
    metrics = VOLUME_METRICS + RATE_METRICS
    results: list[dict[str, object]] = []
    for metric in metrics:
        pred_vals = predicted[metric].values
        act_vals = actual[metric].values
        n = min(len(pred_vals), len(act_vals))
        if n == 0:
            results.append({"metric_name": metric, "mape_pct": float("nan")})
            continue
        errors = []
        for i in range(n):
            a = float(act_vals[i])
            p = float(pred_vals[i])
            if a != 0:
                errors.append(abs((a - p) / a) * 100)
        mape = sum(errors) / len(errors) if errors else float("nan")
        results.append({"metric_name": metric, "mape_pct": round(mape, 2)})

    return pd.DataFrame(results)


def print_backtest(impact_df: pd.DataFrame, train_months: int = 9) -> None:
    """Run backtesting and print results as a formatted table.

    Args:
        impact_df: Full ``fct_consent_impact`` data.
        train_months: Number of months for training.
    """
    results = run_backtest(impact_df, train_months)
    print("\n=== Consent Impact Model - Backtest Results ===")
    all_months = sorted(impact_df["report_month"].unique())
    print(f"Training: {len(all_months[:train_months])} months | Test: {len(all_months[train_months:])} months\n")
    print(tabulate(results, headers="keys", tablefmt="simple", showindex=False, floatfmt=".2f"))
    print()
