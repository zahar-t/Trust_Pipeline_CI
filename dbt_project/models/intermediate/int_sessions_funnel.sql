-- int_sessions_funnel.sql
-- Session-level funnel progression with consent-aware step tracking

with events as (
    select * from {{ ref('stg_events') }}
),

session_events as (
    select
        session_id,
        customer_id,
        consent_level,
        min(event_timestamp) as session_start,
        max(event_timestamp) as session_end,

        -- Funnel step flags
        max(case when event_type = 'page_view' then 1 else 0 end) as has_page_view,
        max(case when event_type = 'add_to_cart' then 1 else 0 end) as has_add_to_cart,
        max(case when event_type = 'checkout_start' then 1 else 0 end) as has_checkout_start,
        max(case when event_type = 'purchase' then 1 else 0 end) as has_purchase,

        -- Deepest funnel step reached
        case
            when max(case when event_type = 'purchase' then 1 else 0 end) = 1 then 'purchase'
            when max(case when event_type = 'checkout_start' then 1 else 0 end) = 1 then 'checkout_start'
            when max(case when event_type = 'add_to_cart' then 1 else 0 end) = 1 then 'add_to_cart'
            when max(case when event_type = 'page_view' then 1 else 0 end) = 1 then 'page_view'
            else 'unknown'
        end as deepest_funnel_step,

        count(*) as n_events

    from events
    group by session_id, customer_id, consent_level
)

select * from session_events
