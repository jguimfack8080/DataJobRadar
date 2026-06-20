{{ config(materialized='table') }}

with quelle as (
    select
        coalesce(nullif(unternehmen_normalisiert, ''), 'unbekannt') as schluessel,
        unternehmen
    from {{ ref('stg_stellenanzeigen') }}
    where unternehmen is not null
)
select
    md5(schluessel) as unternehmens_id,
    any_value(unternehmen) as unternehmen,
    schluessel as unternehmen_normalisiert
from quelle
group by schluessel
