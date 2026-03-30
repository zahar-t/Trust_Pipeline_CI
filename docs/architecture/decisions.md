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
