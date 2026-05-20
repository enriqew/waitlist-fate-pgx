-- Staging model: normalize raw us-fate-distribution.json into typed columns.
-- Source: data/raw/us-fate-distribution.json (OPTN/UNOS removal registry, 1995–2026)
-- Schema: year (int), organ (str), reason_bucket (str), patients (int)

{{ config(materialized='view') }}

WITH raw AS (
    SELECT *
    FROM read_json_auto(
        '{{ env_var("RAW_DATA_DIR", "../../data/raw") }}/us-fate-distribution.json'
    )
),
typed AS (
    SELECT
        CAST(year AS INTEGER)           AS year,
        LOWER(TRIM(organ))              AS organ,
        LOWER(TRIM(reason_bucket))      AS reason_bucket,
        CAST(COALESCE(patients, 0) AS INTEGER) AS patients
    FROM raw
    WHERE year IS NOT NULL
      AND organ IS NOT NULL
      AND reason_bucket IS NOT NULL
)
SELECT *
FROM typed
ORDER BY organ, year, reason_bucket
