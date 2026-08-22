-- Hub: fachlicher Schluessel der Einrichtung, Insert-Only.
{{ config(materialized='incremental', unique_key='hk_einrichtung') }}

with src as (
    select distinct einrichtung_id
    from {{ ref('stg_einrichtungen') }}
)

select
    {{ hashkey(['einrichtung_id']) }}   as hk_einrichtung,
    einrichtung_id,
    current_timestamp                   as load_ts,
    'qvig.einrichtungen'                as record_source
from src

{% if is_incremental() %}
where {{ hashkey(['einrichtung_id']) }} not in (select hk_einrichtung from {{ this }})
{% endif %}
