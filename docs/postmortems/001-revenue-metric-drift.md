# Postmortem #001: Revenue Metric Drift — Currency Conversion Change

**Date**: 2025-09-15  
**Severity**: Critical (12.3% net revenue drift)  
**Detected by**: Semantic CI gate on PR #47  
**Time to detection**: 0 minutes (caught pre-merge)  
**Time to resolution**: 35 minutes  

## Summary

A well-intentioned refactor of the currency conversion logic in `stg_orders.sql` introduced a 12.3% drift in the `net_revenue_eur` metric. The change replaced hardcoded FX rates with a lookup from a new `dim_fx_rates` seed file, but the seed file contained inverted rates for GBP→EUR (using EUR→GBP rate instead). Because GBP transactions represent ~10% of total volume, the error was large enough to trigger Semantic CI's critical threshold but small enough to plausibly go unnoticed in a dashboard review.

## Timeline

| Time | Event |
|------|-------|
| 09:15 | Developer opens PR #47: "Refactor: move FX rates to seed file for maintainability" |
| 09:16 | CI triggers: `dbt run` → `dbt test` → all pass |
| 09:17 | Semantic CI gate runs: **CRITICAL — net_revenue_eur drifted +12.3%** |
| 09:18 | Developer sees PR comment with drift report |
| 09:25 | Root cause identified: GBP rate inverted in seed file (0.85 instead of 1.17) |
| 09:35 | Seed file corrected, PR updated |
| 09:37 | Semantic CI re-runs: **PASS — all metrics within tolerance** |
| 09:40 | PR merged |

## Semantic CI Report (from the failing run)

```
## Semantic CI: Metrics Check Failed

**Baseline**: `baseline` -> **Current**: `pr-47`
**Run at**: 2025-09-15 09:17 UTC

### Summary
| Status | Count |
|--------|-------|
| Critical | 3 |
| Warning | 2 |
| Info | 0 |
| New | 0 |
| Removed | 0 |
| Unchanged | 47 |

### Significant Changes
| | Metric                              | Period     | Baseline   | Current    | Change |
|--|--------------------------------------|------------|------------|------------|--------|
| 🔴 | `net_revenue_eur`                  | 2025-08-01 | 245320.00  | 275502.00  | +12.3% |
| 🔴 | `net_revenue_eur` [country_code=GB] | 2025-08-01 | 24120.00  | 54302.00   | +125.1% |
| 🔴 | `avg_order_value_eur`              | 2025-08-01 | 67.40      | 75.72      | +12.3% |
| 🟡 | `net_revenue_eur` [consent_level=full] | 2025-08-01 | 103034.00 | 115711.00 | +12.3% |
| 🟡 | `net_revenue_eur` [consent_level=minimal] | 2025-08-01 | 73596.00 | 82651.00 | +12.3% |
```

## Root Cause

The new `seeds/fx_rates.csv` contained:

```csv
currency,rate_to_eur
EUR,1.0
GBP,0.85    ← WRONG: this is EUR→GBP, not GBP→EUR
SEK,0.088
PLN,0.23
```

The correct GBP→EUR rate is 1.17 (i.e., £1 = €1.17). The inverted rate (0.85) caused all GBP transactions to be underconverted, resulting in GBP revenue appearing ~37% higher in EUR terms than the baseline (which used the correct hardcoded rate).

Because the dimensional diff showed `[country=GB]` with +125% drift while all other countries showed 0% drift, the root cause was immediately localizable.

## Why Existing Tests Didn't Catch It

1. **Schema tests passed**: All columns had correct types, no nulls where unexpected, accepted values matched.
2. **Relationship tests passed**: All foreign keys were valid.
3. **`assert_revenue_reconciliation` passed**: Order header totals still matched line item totals (both were converted with the same wrong rate).

The fundamental issue: **dbt tests validate data structure, not data meaning.** The revenue number was a perfectly valid number — it was just the wrong number.

## What Semantic CI Caught That Tests Couldn't

Semantic CI compares the *output* of the metric (net_revenue_eur = 275,502) against the *expected* output (baseline = 245,320) and flags that the delta exceeds the configured threshold. It doesn't need to understand *why* the number changed — it just knows it changed more than expected.

The dimensional breakdown (`[country=GB]` showing +125% while others showed 0%) then pointed directly at the root cause without any additional investigation.

## Action Items

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Fix GBP rate in seed file | Developer | ✅ Done |
| 2 | Add singular test: `assert_fx_rates_are_gt_zero_and_reasonable` | Developer | ✅ Done |
| 3 | Add Semantic CI per-metric override: `net_revenue_eur` critical at 5% | Team | ✅ Done |
| 4 | Document FX rate update process in `docs/runbooks/` | Team | Pending |

## Lessons Learned

1. **Metric regression testing is not optional.** Standard dbt tests are necessary but insufficient for catching semantic errors — changes that produce valid-looking but incorrect numbers.

2. **Dimensional diffs are the fastest path to root cause.** Without the `[country=GB]` breakdown, the 12.3% aggregate drift could have taken hours to diagnose. With it, the cause was obvious in seconds.

3. **"Refactors" are the riskiest changes.** The PR didn't change business logic — it just moved constants to a config file. But the move introduced a data entry error that propagated through the entire pipeline. This is exactly the class of bug that thrives in analytics: quiet, plausible, and invisible without metric-level testing.
