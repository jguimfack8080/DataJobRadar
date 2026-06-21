{{ config(materialized='view') }}

with quelle as (
    select * from {{ source('silver', 'stellenanzeigen') }}
    where adzuna_id is not null
),
dedup as (
    select *,
           row_number() over (
               partition by adzuna_id
               order by abruf_zeitpunkt desc nulls last
           ) as rang
    from quelle
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
    skills,
    angebots_url
from dedup
where rang = 1
