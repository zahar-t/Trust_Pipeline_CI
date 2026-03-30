-- metric_definitions_forecast.sql
-- Unpivoted forecast metrics from the consent impact simulation model.
-- Each row = one predicted metric value under a specific consent scenario.
-- Same schema as metric_definitions for semantic-ci compatibility.

{{ config(materialized='table') }}

with predictions as (
    select * from {{ ref('consent_forecast_predictions') }}
)

select
    case
        when period = 'all_months' then cast('2025-01-01' as timestamp)
        else cast(period as timestamp)
    end as period,
    metric_name,
    cast(predicted_value as double) as metric_value,
    case
        when period = 'all_months' then 'aggregate'
        else 'monthly'
    end as grain,
    'scenario' as dimension_name,
    scenario_name as dimension_value
from predictions
