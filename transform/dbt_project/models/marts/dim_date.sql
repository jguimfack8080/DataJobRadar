{{ config(materialized='table') }}

with rahmen as (
    select unnest(
        generate_series(
            date '2023-01-01',
            current_date + interval '30' day,
            interval '1' day
        )
    ) as datum
)
select
    datum,
    extract(year from datum)::int as jahr,
    extract(quarter from datum)::int as quartal,
    extract(month from datum)::int as monat,
    extract(week from datum)::int as kalenderwoche,
    extract(day from datum)::int as tag,
    extract(dow from datum)::int as wochentag_nr,
    case extract(dow from datum)
        when 0 then 'Sonntag'
        when 1 then 'Montag'
        when 2 then 'Dienstag'
        when 3 then 'Mittwoch'
        when 4 then 'Donnerstag'
        when 5 then 'Freitag'
        when 6 then 'Samstag'
    end as wochentag
from rahmen
