# Metric Definitions

> **Owner**: Data/Analytics Engineering  
> **Last updated**: 2025-09-01  
> **Source of truth**: `dbt_project/models/metrics/metric_definitions.sql`

This document defines the business metrics used across dashboards, reports, and automated monitoring. All metrics are computed from the same source models and are subject to automated regression testing via Semantic CI.

---

## Revenue Metrics

### Gross Revenue (EUR)
- **Definition**: Sum of `total_amount_eur` for all orders with status = `completed`
- **Currency**: All values normalized to EUR using daily FX rates
- **Grain**: Monthly
- **Excludes**: Cancelled orders, refunded orders, orders flagged with data quality issues (negative amounts, future dates)
- **Consent impact**: Revenue is recorded regardless of consent level (transaction data is "strictly necessary"). However, attribution of revenue to marketing channels is consent-dependent.

### Net Revenue (EUR)
- **Definition**: Gross Revenue minus Refund Amount
- **Calculation**: `completed_revenue - refunded_revenue`
- **Note**: A negative net revenue for a period is possible if refunds from prior-period orders exceed current-period sales. This is expected behavior, not a data quality issue.

### Average Order Value (EUR)
- **Definition**: Net Revenue / Count of Distinct Orders (excluding cancelled)
- **Note**: AOV is sensitive to high-value outliers. For reporting to non-technical stakeholders, median order value may be more appropriate, but is not currently included in the standard metric set.

### Refund Rate
- **Definition**: Total Refund Amount / Gross Revenue
- **Expected range**: 0.05 – 0.15 (5–15%)
- **Alert threshold**: > 0.20 triggers investigation

---

## Customer Metrics

### New Customers
- **Definition**: Count of distinct customers whose first completed order falls within the reporting period
- **Note**: "First order" is determined by `customer_order_sequence = 1` in `fct_orders`, which uses chronological ordering. If an order is backdated due to a data pipeline delay, the first-order assignment may shift.

### Unique Buyers
- **Definition**: Count of distinct customers with at least one non-cancelled order in the period
- **Differs from "Active Users"**: This metric counts only purchasing customers, not all visitors or registered accounts.

### Customer Segments
| Segment | Definition |
|---------|-----------|
| Never Purchased | Registered but no completed orders |
| One-Time | Exactly 1 completed order lifetime |
| Repeat | 2–4 completed orders lifetime |
| Loyal | 5+ completed orders lifetime |

---

## Consent & Privacy Metrics

### Full Consent Rate
- **Definition**: Count of customers with `consent_level = 'full'` / Total customers registered in period
- **Why it matters**: Determines the proportion of customer behavior that is fully observable. In EU markets, this typically ranges 40–60%.

### Consent Impact on Revenue Visibility
Metrics in `fct_consent_impact` show the same revenue and funnel metrics broken down by consent tier:

| Consent Level | What's Tracked | What's Missing |
|--------------|---------------|----------------|
| **Full** | All events, all attribution, full funnel | Nothing |
| **Analytics Only** | Purchases, checkout events | Page views, marketing attribution |
| **Minimal** | Transactions only (essential) | Most funnel events, all behavioral data |

This breakdown quantifies the "measurement gap" — the difference between what you'd measure with full consent vs. what you actually observe under EU consent norms.

---

## Funnel Metrics

### Session Conversion Rate
- **Definition**: Sessions with a purchase event / Total sessions
- **Consent dependency**: Under `minimal` consent, many sessions lack page_view events, meaning session counts are underreported. This artificially inflates the conversion rate for minimal-consent users.

### Cart-to-Purchase Rate
- **Definition**: Sessions with a purchase / Sessions with an add_to_cart event
- **More reliable**: Less affected by consent suppression than session conversion rate, because add_to_cart events are tracked under both `full` and `analytics_only` consent.

---

## How Metrics Are Monitored

All metrics defined above are automatically:

1. **Computed** on every `dbt run` via the `metric_definitions` model
2. **Snapshotted** by Semantic CI and stored in the snapshot database
3. **Diffed** against baseline values on every pull request
4. **Gated** in CI — PRs that cause >5% drift generate warnings; >10% drift blocks the merge

See [Postmortem #001](../postmortems/001-revenue-metric-drift.md) for a worked example of how this monitoring caught a real metric regression.
