# semantic-ci

**Metric regression testing for dbt projects.**

Catch unintended metric drift before it reaches production. `semantic-ci` snapshots your dbt metric values, diffs them across runs, and gates your CI pipeline when metrics change beyond expected thresholds.

## The Problem

You refactor a dbt model. Tests pass. CI is green. But next Monday, the CFO asks why revenue dropped 12%. Turns out your currency conversion change propagated to a downstream metric you didn't check. **dbt tests validate data shape — they don't validate that your numbers still mean what they meant yesterday.**

`semantic-ci` fills this gap: it treats metric values as testable artifacts, just like code.

## How It Works

```
1. SNAPSHOT   →  Capture metric values from your dbt project
2. DIFF       →  Compare current values against a baseline
3. REPORT     →  Generate a markdown PR comment with drift analysis
4. GATE       →  Pass/fail your CI pipeline based on thresholds
```

## Quick Start

```bash
pip install semantic-ci

# After running `dbt run`, capture a baseline
semantic-ci snapshot --project-dir ./my_dbt_project --label baseline

# ... make changes to your dbt models ...
# Re-run dbt, then check for drift
semantic-ci gate \
  --project-dir ./my_dbt_project \
  --baseline-label baseline \
  --threshold 0.05 \
  --output-dir ./reports
```

## CLI Commands

### `semantic-ci snapshot`
Capture current metric values from your dbt project's `metric_definitions` model.

```bash
semantic-ci snapshot \
  --project-dir ./dbt_project \
  --label baseline \
  --store .semantic_ci/snapshots.duckdb
```

### `semantic-ci diff`
Compare current metrics against a baseline snapshot.

```bash
semantic-ci diff \
  --project-dir ./dbt_project \
  --baseline latest \
  --threshold 0.05
```

### `semantic-ci gate`
Full CI workflow: snapshot → diff → report → exit code.

Exit codes:
- `0` = pass (no critical drifts)
- `1` = fail (critical drifts detected)
- `2` = warn (warnings but no critical)

```bash
semantic-ci gate \
  --project-dir ./dbt_project \
  --baseline-label baseline \
  --threshold 0.05 \
  --output-dir .semantic_ci/reports
```

### `semantic-ci list`
Show recent snapshot runs.

```bash
semantic-ci list --limit 5
```

## GitHub Actions Integration

```yaml
- name: Run Semantic CI
  run: |
    dbt run
    semantic-ci gate \
      --project-dir . \
      --baseline-label baseline \
      --output-dir ./semantic-ci-reports

- name: Post PR Comment
  if: github.event_name == 'pull_request'
  uses: marocchino/sticky-pull-request-comment@v2
  with:
    path: ./semantic-ci-reports/pr_comment.md
```

## Configuration

### Thresholds

Default thresholds:
- **Warning**: 5% change
- **Critical**: 10% change
- **Min absolute change**: 1.0 (ignore tiny fluctuations)

### Per-Metric Overrides

Some metrics are more volatile than others. Configure per-metric thresholds:

```python
from semantic_ci.diff import DiffConfig

config = DiffConfig(
    warning_pct=0.05,
    critical_pct=0.10,
    metric_overrides={
        "refund_rate": {"warning_pct": 0.25, "critical_pct": 0.50},
        "session_conversion_rate": {"warning_pct": 0.10, "critical_pct": 0.20},
    }
)
```

## Requirements

Your dbt project needs a `metric_definitions` model (or equivalent) that outputs metrics in this format:

| Column | Type | Description |
|--------|------|-------------|
| `metric_name` | string | Name of the metric |
| `period` | timestamp | Time period for the metric value |
| `grain` | string | Temporal grain (daily, weekly, monthly) |
| `dimension_name` | string (nullable) | Optional dimension name |
| `dimension_value` | string (nullable) | Optional dimension value |
| `metric_value` | numeric | The metric value |

## License

MIT
