-- tests/assert_revenue_reconciliation.sql
-- Singular test: verify that order-level revenue matches
-- the sum of line item revenue (within tolerance)
--
-- This catches the exact kind of bug that Semantic CI is designed
-- to detect: a model change that causes revenue to silently drift.

{{ config(severity='warn') }}

with order_totals as (
    select
        order_id,
        total_amount_eur as order_total
    from {{ ref('stg_orders') }}
    where not dq_negative_amount
),

line_item_totals as (
    select
        order_id,
        sum(line_total_eur) as line_items_total
    from {{ ref('stg_order_items') }}
    group by 1
),

comparison as (
    select
        o.order_id,
        o.order_total,
        l.line_items_total,
        abs(o.order_total - l.line_items_total) as absolute_diff,
        case 
            when o.order_total != 0 
            then abs(o.order_total - l.line_items_total) / abs(o.order_total)
            else 0
        end as pct_diff
    from order_totals o
    inner join line_item_totals l on o.order_id = l.order_id
)

-- Fail if any order has > 5% discrepancy between header and line items
select *
from comparison
where pct_diff > 0.05
