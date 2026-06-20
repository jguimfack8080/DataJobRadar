{# Ueberschreibt das Standardverhalten von dbt-duckdb, das Schemas
   mit dem Standardpraefix `main_` versieht. Wir wollen die Schemas
   direkt als `silver` und `gold` ansprechen, damit das Backend ohne
   Praefix abfragen kann. #}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
