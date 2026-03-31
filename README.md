# Metric Trust Pipeline

**Numbers stay stable unless intended changes occur.**

An end-to-end analytics engineering project that demonstrates how to build trusted, governed metrics — with automated regression testing that catches unintended changes before they reach production.

This project exists because the #1 pain point in analytics engineering isn't building dashboards — it's maintaining trust in the numbers those dashboards show. When metric logic is scattered across BI tools, ad-hoc SQL, and undocumented transformations, teams lose confidence in their data. This pipeline treats metrics as production artifacts: versioned, tested, documented, and enforced in CI.

## What This Project Demonstrates

| Skill | How It's Shown |
|-------|---------------|
| **Dimensional modeling** | Fact/dimension schema with SCD Type 2, incremental loads, consent-aware design |
| **dbt best practices** | Staging → intermediate → marts layering, custom macros, schema tests, documentation |
| **Data quality engineering** | Data contracts, freshness checks, anomaly detection, incident response workflow |
| **Metric governance** | Centralized metric definitions with semantic CI — automated regression testing on every PR |
| **EU/GDPR awareness** | Consent flag dimension showing how metrics shift under different consent regimes |
| **FX rate integration** | Daily EUR exchange rates from frankfurter.app, loaded as dbt seeds for currency-aware metrics |
| **Consent impact forecasting** | Simulation-based model projecting revenue under different GDPR consent scenarios |
| **Interactive analytics** | 5-page Streamlit dashboard for exploring metrics, consent impact, FX effects, and forecasts |
| **Production operations** | CI/CD pipeline, monitoring hooks, incident postmortem documentation |
| **Stakeholder communication** | Business-facing metric definition docs, impact analysis reports |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Data Generator  │────▶│   DuckDB / BQ     │────▶│    dbt Project       │
│  (Python)        │     │   (Raw Layer)     │     │   staging/int/marts  │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                            │
┌─────────────────┐                   ┌─────────────────────┤
│  FX Ingestion    │──── seeds ──────▶│                     │
│  (frankfurter)   │                  │          ┌──────────▼───────────┐
└─────────────────┘     ┌─────────────┤          │  Metric Definitions   │
                        │             │          │  (dbt metrics +      │
┌─────────────────┐     │             │          │   business docs)     │
│ Consent Forecast │◀───┘             │          └──────────────────────┘
│ (ds_models)      │── seeds ──▶ dbt  │
└─────────────────┘                   │          ┌─────────────────────────┐
                                      └─────────▶│   Semantic CI Module    │
┌─────────────────┐                              │   - Snapshot store      │
│  Streamlit       │◀── read-only DuckDB ───────▶│   - Metric diff engine  │
│  Dashboard       │                              │   - PR report generator │
└─────────────────┘                              │   - CI gate             │
                                                  └─────────────────────────┘
```

## Quick Start

### Local development (DuckDB — no warehouse account needed)

```bash
# Clone and setup
git clone https://github.com/zahar-t/metric-trust-pipeline.git
cd metric-trust-pipeline

# Generate synthetic data (small config for fast setup, ~12K rows)
pip install -r data_generator/requirements.txt
python data_generator/generate.py --config data_generator/config_small.yaml --target duckdb --output dbt_project/seeds/
# For full dataset (~160K rows): omit --config flag

# Fetch daily FX rates (EUR base) and write to seeds
pip install -r fx_ingestion/requirements.txt
python fx_ingestion/fetch_rates.py
# Falls back to bundled CSV if frankfurter.app is unreachable

# Run dbt
cd dbt_project
pip install dbt-duckdb
dbt deps
dbt seed
dbt run
dbt test

# Run consent impact forecast (writes predictions back as a seed)
cd ..
pip install -r ds_models/requirements.txt
python -m ds_models.consent_forecast --db dbt_project/target/dev.duckdb --output dbt_project/seeds/consent_forecast_predictions.csv

# Rebuild dbt with forecast seed included
cd dbt_project
dbt seed
dbt run

# Run Semantic CI
cd ../semantic_ci
pip install -e .
semantic-ci snapshot --project-dir ../dbt_project
semantic-ci diff --baseline latest

# Launch the dashboard
cd ../dashboard
pip install -r requirements.txt
streamlit run app.py
```

### BigQuery (production-like)

```bash
# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Generate and load data
python data_generator/generate.py --target bigquery --project your-gcp-project --dataset raw_ecommerce

# Run dbt
cd dbt_project
dbt run --target bq
dbt test --target bq
```

## Project Structure

```
metric-trust-pipeline/
├── README.md
├── data_generator/           # Synthetic EU e-commerce data with consent flags
│   ├── generate.py
│   ├── config.yaml           # Data generation parameters
│   └── requirements.txt
├── fx_ingestion/             # Daily EUR exchange rate fetcher
│   ├── fetch_rates.py        # Pulls rates from frankfurter.app → CSV seed
│   └── requirements.txt
├── ds_models/                # Data science models
│   ├── consent_forecast/     # Consent impact revenue simulation
│   │   ├── __main__.py       # CLI entry point
│   │   ├── model.py          # Stratified simulation engine
│   │   ├── scenarios.py      # Consent scenario definitions
│   │   ├── features.py       # Feature extraction from DuckDB
│   │   ├── evaluate.py       # Model evaluation
│   │   └── output.py         # CSV seed writer
│   └── requirements.txt
├── dashboard/                # Streamlit interactive analytics
│   ├── app.py                # Main entry point
│   ├── pages/
│   │   ├── 1_Revenue_Overview.py
│   │   ├── 2_Consent_Impact.py
│   │   ├── 3_Metric_Health.py
│   │   ├── 4_FX_Impact.py
│   │   └── 5_Consent_Forecast.py
│   ├── components/           # Shared UI components
│   └── requirements.txt
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/          # 1:1 source cleaning
│   │   ├── intermediate/     # Business logic joins
│   │   ├── marts/            # Consumption-ready tables
│   │   └── metrics/          # Metric definitions
│   ├── seeds/                # Reference data (countries, consent mappings, FX rates, forecasts)
│   ├── macros/               # Reusable transformations
│   ├── tests/                # Custom data tests
│   └── snapshots/            # SCD Type 2 tracking
├── semantic_ci/              # Standalone Python package (pip-installable)
│   ├── pyproject.toml
│   ├── semantic_ci/
│   │   ├── snapshot.py       # Capture metric values at a point in time
│   │   ├── diff.py           # Compare snapshots, detect drift
│   │   ├── report.py         # Generate markdown PR comments
│   │   └── gate.py           # CI pass/fail logic
│   └── tests/
├── docs/
│   ├── architecture/         # System design decisions
│   ├── metric_definitions/   # Business-facing metric docs
│   └── postmortems/          # Incident examples (traced metric breaks)
├── scripts/                  # Utility scripts
└── .github/workflows/        # CI/CD pipeline
```

## FX Rate Ingestion

The `fx_ingestion/fetch_rates.py` script pulls daily EUR exchange rates from the [frankfurter.app](https://www.frankfurter.app/) API and writes them to `dbt_project/seeds/fx_rates.csv`.

```bash
python fx_ingestion/fetch_rates.py
```

The rates are loaded into dbt as a seed table, keeping the pipeline simple and reproducible. If the API is unreachable (e.g., in CI with no network or during an outage), the step falls back to the previously committed CSV so builds are never blocked. FX-aware metrics in the marts layer join against this seed to normalize revenue to EUR.

## Consent Impact Forecasting

The `ds_models/consent_forecast/` module simulates revenue under different GDPR consent scenarios using stratified reweighting. Rather than training a regression model (which would overfit on only 3 consent levels and 12 months of data), it reweights observed revenue by consent-level mix to project outcomes.

```bash
python -m ds_models.consent_forecast \
  --db dbt_project/target/dev.duckdb \
  --output dbt_project/seeds/consent_forecast_predictions.csv
```

The output CSV is loaded as a dbt seed so forecast data flows through the same governance pipeline as actuals. After running the forecast, re-run `dbt seed` and `dbt run` to incorporate predictions into the marts.

## Dashboard

The `dashboard/` directory contains a 5-page Streamlit application for interactive exploration of pipeline outputs. It connects to the DuckDB database in read-only mode.

```bash
cd dashboard
streamlit run app.py
```

Pages:

| Page | Description |
|------|-------------|
| **Revenue Overview** | Top-line revenue KPIs, trends, and country breakdowns |
| **Consent Impact** | Measurement gap analysis across consent regimes |
| **Metric Health** | Semantic CI results — drift detection and test status |
| **FX Impact** | Currency effect on revenue after EUR normalization |
| **Consent Forecast** | Projected revenue under simulated consent scenarios |

See [dashboard/README.md](dashboard/README.md) for more details.

## The EU Angle: Consent-Aware Metrics

This project treats GDPR consent as a first-class analytical dimension, not an afterthought. Every metric can be computed under three consent regimes:

- **Full consent**: All tracking active — baseline measurement
- **Analytics-only**: Marketing tracking suppressed — shows measurement gap from consent loss
- **Minimal consent**: Only essential cookies — worst-case measurement scenario

This mirrors real EU measurement challenges where consent rates typically run 40-60%, meaning 40-60% of user behavior is invisible to analytics. The pipeline explicitly quantifies this gap rather than ignoring it.

## Incident Postmortem Example

See [docs/postmortems/001-revenue-metric-drift.md](docs/postmortems/001-revenue-metric-drift.md) for a worked example of how Semantic CI caught an unintended 12% revenue metric drift caused by a currency conversion change, including root cause analysis and the PR that fixed it.

## Semantic CI Module

The `semantic_ci/` package is designed to be usable independently of this project. Install it in any dbt project:

```bash
pip install semantic-ci
semantic-ci snapshot --project-dir /path/to/dbt/project
semantic-ci diff --baseline latest --threshold 0.05
```

See [semantic_ci/README.md](semantic_ci/README.md) for full documentation.

## Built With

- **dbt Core** — transformation and testing
- **DuckDB** — local development (zero infrastructure)
- **BigQuery** — production target
- **Python 3.11+** — data generation, FX ingestion, consent forecasting, and Semantic CI
- **Streamlit** — interactive analytics dashboard
- **GitHub Actions** — CI/CD

## Troubleshooting

### DuckDB seed loading errors

**CRLF line endings in CSV seed files**: If `dbt seed` fails with parse errors or
unexpected column counts, the seed CSV files may contain Windows-style line endings
(`\r\n`). Convert them to Unix line endings:

```bash
# On macOS/Linux
sed -i '' 's/\r$//' dbt_project/seeds/*.csv
# Or use dos2unix if available
dos2unix dbt_project/seeds/*.csv
```

**Schema mismatch after regenerating data**: If you regenerate seed data with
`generate.py` and then `dbt seed` fails with column type or name mismatches, run
a full refresh to drop and recreate the seed tables:

```bash
cd dbt_project
dbt seed --full-refresh
```

This forces dbt to re-infer the schema from the CSV headers rather than trying to
load into the previously created table structure.

### DuckDB lock errors

DuckDB does not support concurrent writers. If you see a "database is locked" error,
ensure no other process (e.g., a DBeaver session or a previous `dbt run`) is holding
the database file open. The Streamlit dashboard connects in read-only mode to avoid
this issue.

## License

MIT
