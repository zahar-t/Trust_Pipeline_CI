-- stg_customers.sql
-- Clean and type-cast raw customer data
-- Handles: null emails, standardizes country codes

with source as (
    select * from {{ source('raw_ecommerce', 'raw_customers') }}
),

cleaned as (
    select
        customer_id,
        nullif(trim(email), '') as email,
        upper(trim(country_code)) as country_code,
        upper(trim(currency)) as currency,
        lower(trim(consent_level)) as consent_level,
        cast(created_at as timestamp) as created_at,
        cast(is_active as boolean) as is_active,

        -- Derived: is email available for marketing?
        case
            when nullif(trim(email), '') is not null
                 and lower(trim(consent_level)) = 'full'
            then true
            else false
        end as is_marketable

    from source
)

select * from cleaned
