{{ config(materialized='view') }}

with quelle as (
    select * from {{ source('silver', 'stellenanzeigen') }}
    where job_id is not null
),
job_id_dedup as (
    -- Gleiche (quelle, quell_id) ueber mehrere Tage: juengste Beobachtung gewinnt.
    select *,
           row_number() over (
               partition by job_id
               order by abruf_zeitpunkt desc nulls last
           ) as rang
    from quelle
),
titel_dedup as (
    -- Aggregatoren vergeben neue IDs fuer denselben Job an verschiedenen Tagen.
    -- Gleicher Titel + gleiche Firma = ein Eintrag, aktuellster gewinnt.
    select *,
           row_number() over (
               partition by titel_normalisiert,
                            coalesce(nullif(unternehmen_normalisiert, ''), 'unbekannt')
               order by abruf_zeitpunkt desc nulls last
           ) as rang_titel
    from job_id_dedup
    where rang = 1
)
select
    job_id,
    quelle,
    quell_id,
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
    angebots_url,
    dedup_signatur
from titel_dedup
where rang_titel = 1
