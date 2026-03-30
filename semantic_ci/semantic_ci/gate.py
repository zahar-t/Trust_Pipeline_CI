"""CI gate: determine pass/fail for pipeline integration.

Returns exit codes:
  0 = pass (no critical drifts)
  1 = fail (critical drifts detected)
  2 = warn (warnings present but no critical)
"""

from pathlib import Path
from typing import Any

from .diff import DiffConfig, diff_snapshots, summarize_diffs
from .report import generate_full_report, generate_pr_comment
from .snapshot import MetricRow, SnapshotStore


class CIGate:
    """Orchestrate snapshot comparison and CI gating."""

    def __init__(
        self,
        store: SnapshotStore,
        config: DiffConfig | None = None,
    ) -> None:
        """Initialize the CI gate with a store and optional config."""
        self.store = store
        self.config = config or DiffConfig()

    def run(
        self,
        current_metrics: list[MetricRow],
        baseline_run_id: str | None = None,
        baseline_label: str | None = None,
        current_label: str | None = None,
        git_sha: str | None = None,
        git_branch: str | None = None,
        output_dir: str | None = None,
    ) -> int:
        """Execute the full CI gate workflow.

        Steps:
            1. Save current metrics as a new snapshot.
            2. Find baseline snapshot.
            3. Diff baseline vs current.
            4. Generate reports.
            5. Return exit code.

        Returns:
            0 for pass, 1 for fail, 2 for warn.
        """
        # Step 1: Save current snapshot
        current_run = self.store.save_snapshot(
            metrics=current_metrics,
            git_sha=git_sha,
            git_branch=git_branch,
            label=current_label or "current",
        )

        # Step 2: Find baseline
        if baseline_run_id is None:
            baseline_run_id = self.store.get_latest_run(label=baseline_label or "baseline")

        if baseline_run_id is None:
            print("WARNING: No baseline snapshot found. Saving current as baseline for next run.")
            # Re-save with baseline label for next run
            self.store.save_snapshot(
                metrics=current_metrics,
                git_sha=git_sha,
                git_branch=git_branch,
                label="baseline",
            )
            return 0

        baseline_metrics = self.store.get_metrics_for_run(baseline_run_id)
        if not baseline_metrics:
            print(f"WARNING: Baseline run {baseline_run_id} contains no metrics. Treating as pass.")
            return 0

        # Step 3: Diff
        diffs = diff_snapshots(baseline_metrics, current_metrics, self.config)
        summary: dict[str, Any] = summarize_diffs(diffs)

        # Step 4: Generate reports
        pr_comment = generate_pr_comment(
            diffs=diffs,
            baseline_run_id=baseline_run_id,
            current_run_id=current_run.run_id,
            baseline_label=baseline_label,
            current_label=current_label,
        )

        full_report = generate_full_report(
            diffs=diffs,
            baseline_run_id=baseline_run_id,
            current_run_id=current_run.run_id,
        )

        # Print PR comment to stdout
        print(pr_comment)

        # Save reports if output_dir specified
        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "pr_comment.md").write_text(pr_comment)
            (out / "full_report.md").write_text(full_report)
            print(f"\nReports saved to {output_dir}/")

        # Step 5: Determine exit code
        if summary["critical"] > 0:
            print(f"\nFAIL: {summary['critical']} critical metric drift(s) detected")
            return 1
        elif summary["warning"] > 0:
            print(f"\nWARN: {summary['warning']} metric warning(s)")
            return 2
        else:
            print("\nPASS: No significant metric drift")
            return 0
