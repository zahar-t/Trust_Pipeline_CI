"""CLI for semantic-ci.

Commands:
    snapshot   Capture current metric values from a dbt project
    diff       Compare current metrics against a baseline snapshot
    list       Show recent snapshot runs
    gate       Run full CI gate (snapshot + diff + report + exit code)
"""

import subprocess  # nosec B404
import sys
from pathlib import Path

import click
import duckdb

from .diff import DiffConfig, diff_snapshots, summarize_diffs
from .gate import CIGate
from .snapshot import MetricRow, SnapshotStore


def _get_git_info() -> tuple[str | None, str | None]:
    """Return the current git short SHA and branch name, or (None, None)."""
    try:
        sha = (
            subprocess.check_output(  # nosec B603 B607
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        branch = (
            subprocess.check_output(  # nosec B603 B607
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        return sha, branch
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None


def _load_metrics_from_dbt(project_dir: str, target: str = "dev") -> list[MetricRow]:
    """Load metrics from a dbt project's metric_definitions model.

    Assumes the model has been run and results are queryable via DuckDB.

    Raises:
        click.ClickException: If the DuckDB target file is missing or
            the query fails.
    """
    project_path = Path(project_dir)

    # Try DuckDB target first
    duckdb_path = project_path / "target" / "dev.duckdb"
    if not duckdb_path.exists():
        raise click.ClickException(f"Could not find dbt target database at {duckdb_path}. Run 'dbt run' first.")

    try:
        conn = duckdb.connect(str(duckdb_path), read_only=True)
    except duckdb.Error as exc:
        raise click.ClickException(f"Failed to connect to DuckDB at {duckdb_path}: {exc}") from exc

    try:
        rows = conn.execute(
            """
            SELECT metric_name, period, grain,
                   dimension_name, dimension_value, metric_value
            FROM metric_definitions
            ORDER BY metric_name, period
            """
        ).fetchall()
    except duckdb.Error as exc:
        raise click.ClickException(
            f"Failed to query metric_definitions: {exc}. Ensure 'dbt run' completed successfully."
        ) from exc
    finally:
        conn.close()

    return [
        MetricRow(
            metric_name=r[0],
            period=str(r[1]),
            grain=r[2],
            dimension_name=r[3],
            dimension_value=r[4],
            metric_value=float(r[5]),
        )
        for r in rows
    ]


@click.group()
@click.version_option()
def cli() -> None:
    """semantic-ci: Metric regression testing for dbt projects."""


@cli.command()
@click.option("--project-dir", required=True, help="Path to dbt project")
@click.option(
    "--label",
    default=None,
    help="Label for this snapshot (e.g., 'baseline', 'pr-123')",
)
@click.option(
    "--store",
    default=".semantic_ci/snapshots.duckdb",
    help="Path to snapshot store",
)
def snapshot(project_dir: str, label: str | None, store: str) -> None:
    """Capture current metric values as a snapshot."""
    git_sha, git_branch = _get_git_info()
    metrics = _load_metrics_from_dbt(project_dir)

    if not metrics:
        raise click.ClickException("No metrics found. Did you run 'dbt run'?")

    ss = SnapshotStore(store)
    try:
        run = ss.save_snapshot(
            metrics=metrics,
            git_sha=git_sha,
            git_branch=git_branch,
            label=label,
        )
        click.echo(f"Snapshot {run.run_id}: {run.n_metrics} metrics captured")
    finally:
        ss.close()


@cli.command("diff")
@click.option("--project-dir", required=True, help="Path to dbt project")
@click.option(
    "--baseline",
    default="latest",
    help="Baseline run ID or 'latest'",
)
@click.option(
    "--threshold",
    default=0.05,
    type=float,
    help="Warning threshold (pct)",
)
@click.option(
    "--store",
    default=".semantic_ci/snapshots.duckdb",
    help="Path to snapshot store",
)
def diff_cmd(project_dir: str, baseline: str, threshold: float, store: str) -> None:
    """Compare current metrics against a baseline snapshot."""
    ss = SnapshotStore(store)
    try:
        # Load current
        current = _load_metrics_from_dbt(project_dir)

        # Find baseline
        baseline_id = ss.get_latest_run() if baseline == "latest" else baseline

        if not baseline_id:
            raise click.ClickException("No baseline found. Run 'semantic-ci snapshot --label baseline' first.")

        baseline_metrics = ss.get_metrics_for_run(baseline_id)

        config = DiffConfig(warning_pct=threshold, critical_pct=threshold * 2)
        diffs = diff_snapshots(baseline_metrics, current, config)
        summary = summarize_diffs(diffs)

        # Print results
        for d in diffs:
            if d.severity.value != "none":
                click.echo(d.explanation)

        click.echo(
            f"\nSummary: {summary['critical']} critical, "
            f"{summary['warning']} warnings, "
            f"{summary['info']} info, "
            f"{summary['unchanged']} unchanged"
        )
    finally:
        ss.close()


@cli.command("list")
@click.option(
    "--store",
    default=".semantic_ci/snapshots.duckdb",
    help="Path to snapshot store",
)
@click.option("--limit", default=10, type=int)
def list_runs(store: str, limit: int) -> None:
    """Show recent snapshot runs."""
    ss = SnapshotStore(store)
    try:
        runs = ss.list_runs(limit=limit)
    finally:
        ss.close()

    if not runs:
        click.echo("No snapshots found.")
        return

    for r in runs:
        click.echo(
            f"  {r['run_id']}  {r['created_at'][:19]}  "
            f"branch={r['git_branch'] or '-'}  "
            f"label={r['label'] or '-'}  "
            f"metrics={r['n_metrics']}"
        )


@cli.command()
@click.option("--project-dir", required=True, help="Path to dbt project")
@click.option(
    "--baseline-label",
    default="baseline",
    help="Label of baseline snapshot",
)
@click.option(
    "--current-label",
    default=None,
    help="Label for current snapshot",
)
@click.option(
    "--threshold",
    default=0.05,
    type=float,
    help="Warning threshold (pct)",
)
@click.option(
    "--output-dir",
    default=".semantic_ci/reports",
    help="Directory for report artifacts",
)
@click.option(
    "--store",
    default=".semantic_ci/snapshots.duckdb",
    help="Path to snapshot store",
)
def gate(
    project_dir: str,
    baseline_label: str,
    current_label: str | None,
    threshold: float,
    output_dir: str,
    store: str,
) -> None:
    """Run full CI gate: snapshot, diff, report, exit code."""
    git_sha, git_branch = _get_git_info()
    metrics = _load_metrics_from_dbt(project_dir)

    if not metrics:
        raise click.ClickException("No metrics found. Did you run 'dbt run'?")

    ss = SnapshotStore(store)
    try:
        config = DiffConfig(warning_pct=threshold, critical_pct=threshold * 2)
        ci_gate = CIGate(store=ss, config=config)
        exit_code = ci_gate.run(
            current_metrics=metrics,
            baseline_label=baseline_label,
            current_label=current_label or f"pr-{git_sha or 'local'}",
            git_sha=git_sha,
            git_branch=git_branch,
            output_dir=output_dir,
        )
    finally:
        ss.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
