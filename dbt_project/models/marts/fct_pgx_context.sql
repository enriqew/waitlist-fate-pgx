{{ config(materialized='table') }}

-- PGx context: transplant-relevant drugs for each LATAM cohort
-- Used alongside fate distribution as ecological context

SELECT
    population_code,
    drug_name,
    gene_symbol,
    percentage_requiring_change,
    baseline_ceu_percentage,
    delta_vs_baseline,
    classification_strength,
    -- Absolute gap (positive = LATAM needs more dose changes than CEU)
    ABS(delta_vs_baseline) AS absolute_gap
FROM {{ ref('stg_pgx_drug_impact') }}
WHERE drug_name IN ('tacrolimus', 'azathioprine')
ORDER BY population_code, ABS(delta_vs_baseline) DESC
