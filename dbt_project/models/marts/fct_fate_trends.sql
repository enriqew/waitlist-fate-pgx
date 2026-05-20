{{ config(materialized='table') }}

WITH totals AS (
    SELECT
        year,
        organ,
        SUM(patients) AS total_patients
    FROM {{ ref('stg_fate_distribution') }}
    GROUP BY year, organ
),
with_pct AS (
    SELECT
        f.year,
        f.organ,
        f.reason_bucket,
        f.patients,
        ROUND(f.patients * 100.0 / NULLIF(t.total_patients, 0), 2) AS pct_of_total
    FROM {{ ref('stg_fate_distribution') }} f
    JOIN totals t ON f.year = t.year AND f.organ = t.organ
),
with_yoy AS (
    SELECT
        *,
        LAG(pct_of_total) OVER (
            PARTITION BY organ, reason_bucket
            ORDER BY year
        ) AS prior_pct
    FROM with_pct
)
SELECT
    year,
    organ,
    reason_bucket,
    patients,
    pct_of_total,
    ROUND(pct_of_total - prior_pct, 2) AS yoy_change_pp
FROM with_yoy
ORDER BY organ, year, reason_bucket
