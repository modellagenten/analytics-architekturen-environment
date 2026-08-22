-- Link: Beziehung Fall <-> Einrichtung, Insert-Only.
{{ config(materialized='incremental', unique_key='hk_fall_einrichtung') }}

with src as (
    select distinct fall_id, einrichtung_id
    from {{ ref('stg_faelle') }}
)

select
    {{ hashkey(['fall_id', 'einrichtung_id']) }}    as hk_fall_einrichtung,
    {{ hashkey(['fall_id']) }}                      as hk_fall,
    {{ hashkey(['einrichtung_id']) }}               as hk_einrichtung,
    current_timestamp                               as load_ts,
    'qvig.faelle'                                   as record_source
from src

{% if is_incremental() %}
where {{ hashkey(['fall_id', 'einrichtung_id']) }} not in (
    select hk_fall_einrichtung from {{ this }}
)
{% endif %}
