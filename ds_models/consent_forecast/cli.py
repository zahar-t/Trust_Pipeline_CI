"""Click CLI entry-point for the Consent Impact Forecasting Model."""

from __future__ import annotations

from pathlib import Path

import click


@click.command("consent-forecast")
@click.option(
    "--db",
    type=click.Path(exists=True),
    default="dbt_project/target/dev.duckdb",
    show_default=True,
    help="Path to the DuckDB warehouse file.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(),
    default=None,
    help="Write scenario predictions CSV to this path.",
)
@click.option(
    "--evaluate",
    is_flag=True,
    default=False,
    help="Run backtesting and print MAPE results.",
)
def main(db: str, output_path: str | None, evaluate: bool) -> None:
    """Consent Impact Forecasting Model.

    Simulates the effect of different consent-distribution scenarios on
    revenue, conversion, and measurement visibility.
    """
    from .evaluate import print_backtest
    from .features import load_features
    from .model import ConsentImpactSimulator
    from .output import write_predictions

    db_resolved = str(Path(db).resolve())
    click.echo(f"Loading features from {db_resolved} ...")
    impact_df, actual_dist = load_features(db_resolved)
    click.echo(f"  {len(impact_df)} rows, {impact_df['report_month'].nunique()} months")
    click.echo(f"  Actual distribution: { {k: round(v, 3) for k, v in actual_dist.items()} }")

    sim = ConsentImpactSimulator(impact_df)

    if evaluate:
        print_backtest(impact_df)

    if output_path is not None:
        write_predictions(sim, output_path)

    if not evaluate and output_path is None:
        click.echo("No action specified. Use --output and/or --evaluate.")
