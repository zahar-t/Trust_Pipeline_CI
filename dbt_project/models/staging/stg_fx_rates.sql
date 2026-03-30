-- stg_fx_rates.sql
-- Staging model for FX rates. Adds EUR→EUR identity rows and validates rates.

with raw_rates as (
    select * from {{ ref('fx_rates_daily') }}
    where rate > 0
),

-- Add EUR→EUR identity for all dates (so EUR orders can join without special-casing)
eur_dates as (
    select distinct rate_date from raw_rates
),

eur_identity as (
    select
        rate_date,
        'EUR' as base_currency,
        'EUR' as target_currency,
        1.0 as rate,
        1.0 as rate_inverse
    from eur_dates
)

select * from raw_rates
union all
select * from eur_identity
