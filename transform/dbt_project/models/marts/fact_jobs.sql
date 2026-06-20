{{ config(materialized='table') }}

with quelle as (
    select * from {{ ref('stg_stellenanzeigen') }}
),
unternehmen as (
    select * from {{ ref('dim_company') }}
),
standorte as (
    select * from {{ ref('dim_location') }}
)
select
    q.adzuna_id,
    u.unternehmens_id,
    s.standort_id,
    q.titel,
    q.beschreibung,
    q.kategorie,
    q.vertragstyp,
    q.vertragszeit,
    q.gehalt_min,
    q.gehalt_max,
    q.gehalt_mittel,
    q.waehrung,
    q.veroeffentlicht_am,
    q.abruf_zeitpunkt,
    q.skills
from quelle q
left join unternehmen u
    on u.unternehmen_normalisiert = coalesce(nullif(q.unternehmen_normalisiert, ''), 'unbekannt')
left join standorte s
    on s.stadt = coalesce(q.stadt, 'unbekannt')
   and s.bundesland = coalesce(q.bundesland, 'unbekannt')
   and s.region = coalesce(q.region, 'Deutschland')
