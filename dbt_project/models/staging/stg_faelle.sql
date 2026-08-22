with src as (
    select * from {{ source('raw', 'faelle') }}
)

select
    fall_id,
    einrichtung_id,
    patient_pseudonym,
    cast(berichtsjahr as integer)                       as berichtsjahr,
    cast(quartal as integer)                            as quartal,
    -- Rohdaten liefern deutsches Datumsformat TT.MM.JJJJ
    strptime(aufnahme_datum, '%d.%m.%Y')::date          as aufnahme_datum,
    strptime(op_datum, '%d.%m.%Y')::date                as op_datum,
    strptime(entlass_datum, '%d.%m.%Y')::date           as entlass_datum,
    cast("alter" as integer)                            as alter_jahre,
    -- Geschlecht wird mal gross, mal klein geliefert -> normalisieren
    case lower(geschlecht)
        when 'm' then 'm'
        when 'w' then 'w'
        when 'd' then 'd'
        else null
    end                                                 as geschlecht,
    cast(asa_klasse as integer)                         as asa_klasse,
    eingriff_art,
    diagnose_icd,
    prothesen_typ,
    -- OP-Dauer kommt teils mit Dezimalkomma ("107,0") -> in Zahl wandeln
    round(replace(op_dauer_minuten, ',', '.')::double)::integer as op_dauer_minuten,
    cast(verweildauer_tage as integer)                  as verweildauer_tage,
    cast(wundinfektion as integer)                      as wundinfektion,
    cast(luxation as integer)                           as luxation,
    cast(reoperation as integer)                        as reoperation,
    cast(letalitaet as integer)                         as letalitaet,
    cast(beweglichkeit_aufnahme as integer)             as beweglichkeit_aufnahme,
    cast(beweglichkeit_entlassung as integer)           as beweglichkeit_entlassung
from src
