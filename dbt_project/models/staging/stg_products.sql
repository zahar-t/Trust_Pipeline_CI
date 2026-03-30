-- stg_products.sql

with source as (
    select * from {{ source('raw_ecommerce', 'raw_products') }}
),

cleaned as (
    select
        product_id,
        trim(name) as product_name,
        trim(category) as category,
        cast(base_price_eur as numeric) as base_price_eur,
        cast(created_at as timestamp) as created_at
    from source
)

select * from cleaned
