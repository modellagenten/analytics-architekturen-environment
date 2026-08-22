-- Satellite: beschreibende Attribute zum Fall, Insert-Only mit Hash-Diff.
-- Neue Zeile nur, wenn sich die Attribute (hashdiff) geaendert haben.
{{ config(materialized='incremental') }}

with src as (
    select
        fall_id,
        op_datum,
        eingriff_art,
        diagnose_icd,
        prothesen_typ,
        asa_klasse,
        alter_jahre,
        geschlecht
    from {{ ref('stg_faelle') }}
),

hashed as (
    select
        {{ hashkey(['fall_id']) }}                                       as hk_fall,
        {{ hashdiff(['op_datum', 'eingriff_art', 'diagnose_icd',
                     'prothesen_typ', 'asa_klasse', 'alter_jahre',
                     'geschlecht']) }}                                   as hashdiff,
        current_timestamp                                               as load_ts,
        'qvig.faelle'                                                   as record_source,
        op_datum,
        eingriff_art,
        diagnose_icd,
        prothesen_typ,
        asa_klasse,
        alter_jahre,
        geschlecht
    from src
)

select * from hashed

{% if is_incremental() %}
-- Insert-Only: nur bisher unbekannte Zustaende (hashdiff) aufnehmen
where hashdiff not in (select hashdiff from {{ this }})
{% endif %}
