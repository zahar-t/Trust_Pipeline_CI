"""Generate forecast predictions for all predefined scenarios and write to CSV.

The output CSV is suitable for loading back into dbt as a seed table.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from .scenarios import SCENARIOS

if TYPE_CHECKING:
    from .model import ConsentImpactSimulator


def generate_all_predictions(sim: ConsentImpactSimulator) -> pd.DataFrame:
    """Run every predefined scenario and collect results.

    Args:
        sim: A fitted ConsentImpactSimulator instance.

    Returns:
        Long-format DataFrame with columns scenario_name, period,
        metric_name, predicted_value, baseline_value, measurement_gap_pct.
    """
    all_rows: list[dict[str, object]] = []

    for scenario_name, dist in SCENARIOS.items():
        gap_df = sim.measurement_gap(dist)
        projected = sim.simulate(dist)

        for _, gap_row in gap_df.iterrows():
            metric = str(gap_row["metric_name"])
            all_rows.append(
                {
                    "scenario_name": scenario_name,
                    "period": "all_months",
                    "metric_name": metric,
                    "predicted_value": gap_row["scenario_value"],
                    "baseline_value": gap_row["baseline_value"],
                    "measurement_gap_pct": gap_row["measurement_gap_pct"],
                }
            )

        # Per-month detail for key metrics.
        key_metrics = ["gross_revenue_eur", "session_conversion_rate", "n_orders"]
        for _, row in projected.iterrows():
            month = str(row["report_month"])
            for metric in key_metrics:
                all_rows.append(
                    {
                        "scenario_name": scenario_name,
                        "period": month,
                        "metric_name": metric,
                        "predicted_value": round(float(row[metric]), 4),
                        "baseline_value": None,
                        "measurement_gap_pct": None,
                    }
                )

    return pd.DataFrame(all_rows)


def write_predictions(sim: ConsentImpactSimulator, output_path: str | Path) -> Path:
    """Generate predictions and write them to a CSV file.

    Args:
        sim: A fitted ConsentImpactSimulator instance.
        output_path: Destination path for the CSV.

    Returns:
        Resolved path to the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_all_predictions(sim)
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} rows to {output_path}")
    return output_path
