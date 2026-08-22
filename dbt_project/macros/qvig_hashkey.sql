{#
  Bildet einen deterministischen Hash-Key/Hash-Diff (Data Vault 2.x).
  Business Keys werden getrimmt, gross geschrieben und mit '||' verkettet,
  damit der Hash stabil und quellenunabhaengig ist.
#}
{% macro hashkey(columns) %}
    md5(
        {%- if columns is string %}{% set columns = [columns] %}{% endif -%}
        concat_ws('||',
            {%- for col in columns %}
            coalesce(trim(upper(cast({{ col }} as varchar))), '^^') {%- if not loop.last %},{% endif %}
            {%- endfor %}
        )
    )
{% endmacro %}

{% macro hashdiff(columns) %}
    md5(
        concat_ws('||',
            {%- for col in columns %}
            coalesce(trim(cast({{ col }} as varchar)), '^^') {%- if not loop.last %},{% endif %}
            {%- endfor %}
        )
    )
{% endmacro %}
