{% test metric_within_bounds(model, column_name, min_value=None, max_value=None) %}
{#
    Test: metric_within_bounds
    
    Asserts that a metric column stays within expected bounds.
    Useful for catching data quality issues like negative revenue
    or conversion rates > 1.0.
    
    Usage in schema.yml:
        columns:
          - name: refund_rate
            tests:
              - metric_within_bounds:
                  min_value: 0
                  max_value: 1.0
#}

select *
from {{ model }}
where {{ column_name }} is not null
  {% if min_value is not none %}
  and {{ column_name }} < {{ min_value }}
  {% endif %}
  {% if max_value is not none %}
  and {{ column_name }} > {{ max_value }}
  {% endif %}

{% endtest %}
