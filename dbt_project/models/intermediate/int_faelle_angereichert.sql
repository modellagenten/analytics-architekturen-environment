-- Fachliche Anreicherung: Fall + Einrichtung + Kassen-Follow-up + Befragung.
-- Grain bleibt der Fall. Basis fuer Fakten- und Reporting-Marts.
with faelle as (
    select * from {{ ref('stg_faelle') }}
),
einrichtungen as (
    select * from {{ ref('stg_einrichtungen') }}
),
sozial as (
    select * from {{ ref('stg_sozialdaten') }}
),
befragung as (
    select * from {{ ref('stg_befragung') }}
)

select
    f.fall_id,
    f.einrichtung_id,
    f.patient_pseudonym,
    f.berichtsjahr,
    f.quartal,
    f.aufnahme_datum,
    f.op_datum,
    f.entlass_datum,
    f.alter_jahre,
    f.geschlecht,
    f.asa_klasse,
    f.eingriff_art,
    f.diagnose_icd,
    f.prothesen_typ,
    f.op_dauer_minuten,
    f.verweildauer_tage,

    -- Ergebnis-Indikatoren (0/1)
    f.wundinfektion,
    f.luxation,
    f.reoperation,
    f.letalitaet,
    f.beweglichkeit_entlassung - f.beweglichkeit_aufnahme as beweglichkeitsgewinn,

    -- Merkmale aus der Einrichtung (fuer Auswertung nach Land/Region/Traeger)
    e.einrichtung_name,
    e.bundesland,
    e.bundesland_name,
    e.region,
    e.traeger_typ,
    e.ist_lehrkrankenhaus,

    -- Follow-up der Kassen
    s.folge_op_datum,
    coalesce(s.verstorben_365, 0)                       as verstorben_365,

    -- Befragung (nicht fuer jeden Fall vorhanden)
    b.zufriedenheit_gesamt,

    -- abgeleitete Risikomerkmale (Grundlage einfache Risikoadjustierung)
    case when f.alter_jahre >= 80 then 1 else 0 end     as ist_hochbetagt,
    case when f.asa_klasse >= 3 then 1 else 0 end       as ist_hohes_risiko
from faelle f
left join einrichtungen e using (einrichtung_id)
left join sozial s using (patient_pseudonym)
left join befragung b on b.fall_id = f.fall_id
