# Architecture Decision Records

## ADR-001: DuckDB as local development target

**Context**: The project needs to be runnable by anyone reviewing the portfolio without requiring a cloud warehouse account.

**Decision**: Use dbt-duckdb as the default development target, with BigQuery as the production target.

**Consequences**:
- Reviewers can `git clone` → `pip install` → `dbt run` in under 5 minutes
- Some BigQuery-specific SQL features (e.g., `DATE_DIFF` vs `DATEDIFF`) require adapter-aware macros
- DuckDB's in-process nature means no server management for local development

## ADR-002: Synthetic data over public datasets

**Context**: Need a dataset that demonstrates EU-specific analytics challenges (consent flags, multi-currency, GDPR considerations).

**Decision**: Generate synthetic data with a Python script rather than using an existing public dataset.

**Consequences**:
- Full control over data characteristics (consent distribution, data quality issues, seasonal patterns)
- No licensing ambiguity for an open-source project
- Intentional data quality issues can be seeded for testing pipeline robustness
- Tradeoff: data isn't "real," but the pipeline logic and testing approach are production-grade

## ADR-003: Unpivoted metric store format

**Context**: Semantic CI needs a consistent format to snapshot and diff metrics across runs.

**Decision**: Store all metrics in an unpivoted format: `(period, metric_name, metric_value, dimension_name, dimension_value)`.

**Consequences**:
- Any new metric is automatically picked up by Semantic CI without code changes
- Dimensional breakdowns (by country, by consent level) are first-class citizens
- Slightly less intuitive to query directly than a wide table, but more extensible
- Aligns with how dbt's MetricFlow stores metric definitions

## ADR-004: Consent as a first-class analytical dimension

**Context**: EU analytics roles increasingly require understanding of how GDPR consent affects measurement. Most portfolio projects ignore this entirely.

**Decision**: Model consent level as a dimension on both `fct_orders` and event tables, and build a dedicated `fct_consent_impact` mart that quantifies the measurement gap.

**Consequences**:
- Every metric can be viewed through a consent lens
- The `consent_filter` project variable allows running the entire pipeline under different consent regimes
- Demonstrates regulatory awareness that's directly relevant to EU employers
- Adds complexity to the data model but reflects real-world EU measurement challenges

## ADR-005: Semantic CI as a standalone package

**Context**: The metric regression testing logic is useful beyond this specific project.

**Decision**: Build Semantic CI as a pip-installable Python package with its own `pyproject.toml`, CLI, and test suite.

**Consequences**:
- Can be installed in any dbt project: `pip install semantic-ci`
- Has its own README, versioning, and release cycle
- Demonstrates open-source packaging skills (relevant to analytics engineering roles)
- Adds maintenance surface area but maximizes portfolio value

## ADR-006: FX Rates as dbt Seed

**Context**: The pipeline needs daily EUR exchange rates to normalize multi-currency revenue. The data volume is small (one row per currency per day), and the pipeline must remain runnable offline for portfolio reviewers.

**Decision**: Fetch FX rates from frankfurter.app via a lightweight Python script and load them as a dbt seed CSV rather than configuring them as a dbt source or external table.

**Consequences**:
- Seed CSVs are committed to the repo, providing an offline fallback — the pipeline always works even without network access
- No additional infrastructure (no API keys, no external table configuration, no staging schema)
- The fetch step in CI uses `continue-on-error` so builds succeed even if the API is temporarily down
- Tradeoff: seed CSVs must be refreshed periodically to include recent rates, but for a portfolio project this is acceptable
- Keeps the FX data under the same governance and testing as all other seeds

## ADR-007: Stratified Simulation for Consent Forecasting

**Context**: Stakeholders want to understand how revenue would change under different GDPR consent scenarios (e.g., what if consent rates drop from 55% to 40%?). We need a forecasting approach that is transparent and defensible for a portfolio project.

**Decision**: Use stratified simulation with reweighting rather than ML regression to project revenue under different consent mixes.

**Consequences**:
- With only 3 consent levels and 12 months of historical data, a regression model would overfit and produce misleading confidence intervals
- Reweighting observed revenue by consent-level proportions is directly interpretable — reviewers can follow the logic without ML expertise
- The approach answers "what if the consent mix shifts?" without pretending to predict future revenue levels
- Output is written as a dbt seed so it flows through the same testing and governance pipeline as actuals
- Tradeoff: cannot capture non-linear interactions between consent level and purchasing behavior, but this is acceptable given the data volume and portfolio context

## ADR-008: Dashboard Reads DuckDB Read-Only

**Context**: The Streamlit dashboard needs to query the DuckDB database that dbt writes to. DuckDB enforces a single-writer constraint — only one process can hold a write lock at a time.

**Decision**: The Streamlit dashboard connects to DuckDB in read-only mode (`read_only=True`).

**Consequences**:
- Eliminates "database is locked" errors when running the dashboard alongside dbt or other write processes
- The dashboard cannot accidentally mutate pipeline data
- Multiple dashboard sessions can read concurrently without conflicts
- Tradeoff: the dashboard cannot write caches or user preferences to DuckDB, but this is not needed — Streamlit's own session state handles UI state
