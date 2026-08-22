with src as (
    select * from {{ source('raw', 'einrichtungen') }}
)

select
    einrichtung_id,
    name                                as einrichtung_name,
    traeger_typ,
    bundesland,
    bundesland_name,
    region,
    cast(betten as integer)             as betten,
    cast(lehrkrankenhaus as integer) = 1 as ist_lehrkrankenhaus,
    cast(aktiv as integer) = 1          as ist_aktiv,
    cast(gueltig_ab as date)            as gueltig_ab
from src
