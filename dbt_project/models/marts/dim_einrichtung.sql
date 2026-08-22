-- Dimension Einrichtung (Star-Schema). Surrogatschluessel per Hash.
select
    {{ hashkey(['einrichtung_id']) }}   as einrichtung_sk,
    einrichtung_id,
    einrichtung_name,
    traeger_typ,
    bundesland,
    bundesland_name,
    region,
    betten,
    ist_lehrkrankenhaus
from {{ ref('stg_einrichtungen') }}
