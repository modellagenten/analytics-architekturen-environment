-- Reporting-Mart (Information Mart): Qualitaetsindikatoren je Einrichtung.
-- Genau die Sicht, die eine Landesstelle bzw. das Portal auswertet.
with fakt as (
    select * from {{ ref('fct_faelle') }}
),
einrichtung as (
    select * from {{ ref('dim_einrichtung') }}
)

select
    e.einrichtung_id,
    e.einrichtung_name,
    e.bundesland,
    e.bundesland_name,
    e.region,
    e.traeger_typ,

    count(*)                                                as fallzahl,
    round(avg(f.alter_jahre), 1)                            as durchschnittsalter,
    round(avg(f.asa_klasse), 2)                             as asa_mittelwert,

    -- Indikatorraten in Prozent (klassische QS-Kennzahlen)
    round(100.0 * avg(f.wundinfektion), 2)                 as rate_wundinfektion_pct,
    round(100.0 * avg(f.luxation), 2)                      as rate_luxation_pct,
    round(100.0 * avg(f.reoperation), 2)                   as rate_reoperation_pct,
    round(100.0 * avg(f.letalitaet), 2)                    as rate_letalitaet_pct,
    round(100.0 * avg(f.verstorben_365), 2)                as rate_verstorben_365_pct,

    round(avg(f.verweildauer_tage), 1)                     as durchschnitt_verweildauer,
    round(avg(f.beweglichkeitsgewinn), 1)                  as durchschnitt_beweglichkeitsgewinn,
    round(avg(f.zufriedenheit_gesamt), 2)                  as durchschnitt_zufriedenheit
from fakt f
join einrichtung e using (einrichtung_sk)
group by 1, 2, 3, 4, 5, 6
