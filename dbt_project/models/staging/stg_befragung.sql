-- Die Rohquelle ist ein JSON-Dokument; die Antworten stecken verschachtelt
-- im Feld "antworten" (Struct). Hier flachen wir das Dokument auf.
with src as (
    select * from {{ source('raw', 'patientenbefragung') }}
)

select
    pseudonym                                       as patient_pseudonym,
    fall_id,
    cast(berichtsjahr as integer)                   as berichtsjahr,
    cast(antworten.zufriedenheit_gesamt as integer) as zufriedenheit_gesamt,
    cast(antworten.schmerz_vorher as integer)       as schmerz_vorher,
    cast(antworten.schmerz_nachher as integer)      as schmerz_nachher,
    cast(antworten.wuerde_empfehlen as boolean)     as wuerde_empfehlen,
    nullif(freitext, '')                            as freitext
from src
