{#
  SCD2-Demonstration: Aenderungen an Stammdaten der Einrichtung historisieren.
  Strategie 'check' vergleicht ausgewaehlte Spalten; bei Aenderung wird eine
  neue Version mit dbt_valid_from / dbt_valid_to angelegt.
  Ausfuehren mit:  dbt snapshot
#}
{% snapshot snap_einrichtung %}
{{
    config(
        target_schema='snapshots',
        unique_key='einrichtung_id',
        strategy='check',
        check_cols=['traeger_typ', 'betten', 'einrichtung_name']
    )
}}
select
    einrichtung_id,
    einrichtung_name,
    traeger_typ,
    bundesland,
    betten
from {{ ref('stg_einrichtungen') }}
{% endsnapshot %}
