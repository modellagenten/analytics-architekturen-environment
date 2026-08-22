-- Hub: fachlicher Schluessel des Falls, Insert-Only.
{{ config(materialized='incremental', unique_key='hk_fall') }}

with src as (
    select distinct fall_id
    from {{ ref('stg_faelle') }}
)

select
    {{ hashkey(['fall_id']) }}          as hk_fall,
    fall_id,
    current_timestamp                   as load_ts,
    'qvig.faelle'                       as record_source
from src

{% if is_incremental() %}
where {{ hashkey(['fall_id']) }} not in (select hk_fall from {{ this }})
{% endif %}
