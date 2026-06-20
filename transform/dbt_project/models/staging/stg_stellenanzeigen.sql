{{ config(materialized='view') }}

with quelle as (
    select * from {{ source('silver', 'stellenanzeigen') }}
)
select
    adzuna_id,
    titel,
    titel_normalisiert,
    beschreibung,
    unternehmen,
    unternehmen_normalisiert,
    stadt,
    bundesland,
    region,
    gehalt_min,
    gehalt_max,
    gehalt_mittel,
    waehrung,
    vertragstyp,
    vertragszeit,
    kategorie,
    veroeffentlicht_am,
    abruf_zeitpunkt,
    skills
from quelle
where adzuna_id is not null
