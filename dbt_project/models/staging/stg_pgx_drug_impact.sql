-- Staging model: normalize drug_impact_summary.json for transplant-relevant drugs.
-- Source: data/raw/drug_impact_summary.json (pgx-latam-atlas gold layer)
-- Filters to tacrolimus and azathioprine — the two primary transplant immunosuppressants
-- with CPIC-actionable pharmacogene variants in LATAM populations.

{{ config(materialized='view') }}

WITH raw AS (
    SELECT *
    FROM read_json_auto(
        '{{ env_var("RAW_DATA_DIR", "../../data/raw") }}/drug_impact_summary.json'
    )
),
filtered AS (
    SELECT *
    FROM raw
    WHERE LOWER(TRIM(drug_name)) IN ('tacrolimus', 'azathioprine')
),
typed AS (
    SELECT
        UPPER(TRIM(population_code))                    AS population_code,
        LOWER(TRIM(drug_name))                          AS drug_name,
        UPPER(TRIM(gene_symbol))                        AS gene_symbol,
        CAST(percentage_requiring_change AS DOUBLE)     AS percentage_requiring_change,
        CAST(COALESCE(baseline_ceu_percentage, 0) AS DOUBLE) AS baseline_ceu_percentage,
        CAST(COALESCE(delta_vs_baseline, 0) AS DOUBLE)  AS delta_vs_baseline,
        TRIM(classification_strength)                   AS classification_strength
    FROM filtered
    WHERE population_code IS NOT NULL
      AND drug_name IS NOT NULL
      AND gene_symbol IS NOT NULL
)
SELECT *
FROM typed
ORDER BY population_code, drug_name, ABS(delta_vs_baseline) DESC
