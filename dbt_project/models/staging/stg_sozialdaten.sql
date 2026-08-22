with src as (
    select * from {{ source('raw', 'sozialdaten') }}
)

select
    patient_pseudonym,
    nullif(folge_op_datum, '')::date        as folge_op_datum,
    nullif(folge_op_grund, '')              as folge_op_grund,
    cast(verstorben_365 as integer)         as verstorben_365
from src
