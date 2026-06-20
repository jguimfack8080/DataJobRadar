{{ config(materialized='table') }}

with quelle as (
    select adzuna_id, unnest(skills) as skill
    from {{ ref('stg_stellenanzeigen') }}
    where skills is not null
)
select
    adzuna_id,
    skill,
    count(*) as gewichtung
from quelle
group by adzuna_id, skill
