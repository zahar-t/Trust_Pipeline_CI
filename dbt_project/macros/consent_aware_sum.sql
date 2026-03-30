{% macro consent_aware_sum(column, consent_column='consent_level_at_order') %}
{#
    Macro: consent_aware_sum
    
    Computes a sum with consent-regime breakdowns.
    Returns the total AND the consent-segmented values so downstream
    consumers can see exactly how much signal comes from each tier.
    
    Usage:
        {{ consent_aware_sum('net_revenue_eur') }}
    
    Produces columns:
        - {column}_total
        - {column}_full_consent
        - {column}_analytics_only
        - {column}_minimal_consent
        - {column}_consent_coverage (% from full consent)
#}
    sum({{ column }}) as {{ column }}_total,
    sum(case when {{ consent_column }} = 'full' then {{ column }} else 0 end) as {{ column }}_full_consent,
    sum(case when {{ consent_column }} = 'analytics_only' then {{ column }} else 0 end) as {{ column }}_analytics_only,
    sum(case when {{ consent_column }} = 'minimal' then {{ column }} else 0 end) as {{ column }}_minimal_consent,
    case 
        when sum({{ column }}) != 0 
        then round(
            cast(sum(case when {{ consent_column }} = 'full' then {{ column }} else 0 end) as numeric) 
            / cast(sum({{ column }}) as numeric), 
            4
        )
        else null 
    end as {{ column }}_consent_coverage
{% endmacro %}
