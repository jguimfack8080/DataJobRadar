{{ config(materialized='view') }}

with quelle as (
    select * from {{ source('silver', 'stellenanzeigen') }}
    where job_id is not null
),
dedup as (
    -- Sicherheitsnetz: falls dieselbe job_id ueber mehrere Silver-Dateien
    -- (mehrere Tage) auftaucht, behalten wir die juengste Beobachtung.
    select *,
           row_number() over (
               partition by job_id
               order by abruf_zeitpunkt desc nulls last
           ) as rang
    from quelle
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
from dedup
where rang = 1
