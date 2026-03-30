# Metric Trust Pipeline — Dashboard

Interactive Streamlit dashboard for exploring pipeline outputs.

## Running

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard launches at `http://localhost:8501` by default.

## Pages

| Page | Description |
|------|-------------|
| **Revenue Overview** | Top-line revenue KPIs, time-series trends, and country-level breakdowns |
| **Consent Impact** | Measurement gap analysis showing how metrics shift across full, analytics-only, and minimal consent regimes |
| **Metric Health** | Semantic CI drift detection results and data test status across the pipeline |
| **FX Impact** | Currency effects on revenue after EUR normalization using ingested FX rates |
| **Consent Forecast** | Projected revenue under simulated consent scenarios from the `ds_models` forecast |

## Dependencies

See `requirements.txt`. Key packages:

- `streamlit` — application framework
- `duckdb` — database driver
- `pandas` — data manipulation
- `plotly` or `altair` — charting (depending on requirements.txt)

## DuckDB Connection

The dashboard connects to the dbt project's DuckDB database in **read-only mode** to avoid write-lock conflicts. The default path is `../dbt_project/target/dev.duckdb`.

Because DuckDB enforces a single-writer constraint, read-only mode allows the dashboard to run concurrently with `dbt run`, `dbt test`, or any other process that writes to the database. Multiple dashboard sessions can also read at the same time without issues.
