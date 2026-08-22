-- Faktentabelle (Grain: ein QS-Fall). Zentrum des Star-Schemas.
with angereichert as (
    select * from {{ ref('int_faelle_angereichert') }}
)

select
    {{ hashkey(['fall_id']) }}          as fall_sk,
    {{ hashkey(['einrichtung_id']) }}   as einrichtung_sk,

    -- degenerierte Dimensionen (direkt am Fakt)
    fall_id,
    patient_pseudonym,
    berichtsjahr,
    quartal,
    op_datum,
    eingriff_art,
    diagnose_icd,
    prothesen_typ,
    geschlecht,
    asa_klasse,
    alter_jahre,
    ist_hochbetagt,
    ist_hohes_risiko,

    -- Kennzahlen (Measures)
    op_dauer_minuten,
    verweildauer_tage,
    beweglichkeitsgewinn,
    wundinfektion,
    luxation,
    reoperation,
    letalitaet,
    verstorben_365,
    zufriedenheit_gesamt
from angereichert
