-- stg_events.sql
-- Funnel events with consent-aware tracking context

with source as (
    select * from {{ source('raw_ecommerce', 'raw_events') }}
),

cleaned as (
    select
        event_id,
        customer_id,
        lower(trim(event_type)) as event_type,
        cast(event_timestamp as timestamp) as event_timestamp,
        session_id,
        lower(trim(consent_level)) as consent_level,

        -- Event classification
        case
            when lower(trim(event_type)) in ('page_view', 'add_to_cart') then 'top_funnel'
            when lower(trim(event_type)) in ('checkout_start') then 'mid_funnel'
            when lower(trim(event_type)) in ('purchase', 'refund') then 'bottom_funnel'
        end as funnel_stage,

        -- Is this event fully observable? (consent-dependent)
        case
            when lower(trim(consent_level)) = 'full' then true
            when lower(trim(consent_level)) = 'analytics_only'
                 and lower(trim(event_type)) not in ('page_view') then true
            else false
        end as is_fully_tracked

    from source
)

select * from cleaned
