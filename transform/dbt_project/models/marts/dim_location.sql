{{ config(materialized='table') }}

with quelle as (
    select
        coalesce(stadt, 'unbekannt') as stadt,
        coalesce(bundesland, 'unbekannt') as bundesland,
        coalesce(region, 'Deutschland') as region
    from {{ ref('stg_stellenanzeigen') }}
)
select
    md5(stadt || '|' || bundesland || '|' || region) as standort_id,
    stadt,
    bundesland,
    region
from quelle
group by stadt, bundesland, region
