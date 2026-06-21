{{ config(materialized='table') }}

with quelle as (
    select job_id, unnest(skills) as skill
    from {{ ref('stg_stellenanzeigen') }}
    where skills is not null
)
select
    job_id,
    skill,
    count(*) as gewichtung
from quelle
group by job_id, skill
