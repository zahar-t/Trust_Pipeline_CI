{% macro safe_divide(numerator, denominator, decimals=4) %}
{#
    Macro: safe_divide
    
    Division that returns null instead of erroring on zero denominator.
    
    Usage:
        {{ safe_divide('completed_orders', 'total_sessions') }}
#}
    case 
        when {{ denominator }} is null or {{ denominator }} = 0 then null
        else round(cast({{ numerator }} as numeric) / cast({{ denominator }} as numeric), {{ decimals }})
    end
{% endmacro %}
