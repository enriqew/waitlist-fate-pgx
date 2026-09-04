# waitlist-fate-pgx

**Transplant Waitlist Fate × Pharmacogenomics**

Intersects 32 years of US organ transplant waitlist removal data (OPTN/UNOS 1995–2026) with Latin American pharmacogenomic profiles (1000 Genomes Phase 3 × CPIC) to surface the genetic dimension of post-transplant risk, who dies waiting, and whether their ancestry predicts avoidable outcomes after transplant.

Live dashboard: [eredonda.com/projects/waitlist-fate-pgx](https://eredonda.com/projects/waitlist-fate-pgx?utm_source=github&utm_medium=referral)

---

## Background

Most pharmacogenomics (PGx) research focuses on the moment of prescribing. But for transplant patients, the prescribing window is **post-surgery**: and the drugs involved (tacrolimus, cyclosporine, mycophenolate, voriconazole, warfarin) have narrow therapeutic windows that are strongly modulated by pharmacogenes.

CPIC dosing guidelines for these drugs were anchored on European ancestry cohorts (CEU). Latin American populations (MXL Mexican, PEL Peruvian, CLM Colombian, PUR Puerto Rican) show measurable divergence across CYP3A5, CYP2C19, CYP2C9, and DPYD. This project quantifies both the scale of waitlist mortality and the magnitude of that PGx gap.

## Data sources

### OPTN/UNOS Removal Registry

- **Coverage:** USA, annual, 1995–2026 (2026 partial/YTD)
- **Granularity:** organ × year × removal reason
- **Organs:** kidney, liver, heart, lung, pancreas, kidney–pancreas, heart–lung, intestine, vascular composite allograft (VCA)
- **Removal reasons (normalized buckets):**
  - `transplanted_deceased`: deceased-donor transplant (primary outcome)
  - `transplanted_living`: living-donor transplant (kidney, select multi-organ)
  - `improved`: condition improved or changed, removed from active list
  - `removed_too_sick`: clinical deterioration, no longer transplant-eligible
  - `died_waiting`: mortality on the waitlist (primary mortality metric)
  - `other`: administrative, duplicate registration, relocation, unknown
- **Access:** [optn.transplant.hrsa.gov/data](https://optn.transplant.hrsa.gov/data/), Annual Report files

### 1000 Genomes × CPIC (from `pgx-latam-atlas`)

Gold-layer artifacts produced by the [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) pipeline:

| Artifact | Description |
|---|---|
| `actionability_ranking.json` | Top drug–gene–population pairs by Δ vs CEU baseline |
| `drug_impact_summary.json` | % of each cohort requiring dose/therapy change |
| `phenotype_distribution.json` | Metabolizer phenotype breakdown per gene × population |
| `allele_frequencies.json` | Top 3 variants per gene, alternate allele frequency per population |
| `metadata.json` | Pipeline version, snapshot date, source versions |

See [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) for the full pipeline producing these artifacts.

## Key findings

### Waitlist fate (1995–2026 aggregate)

| Organ | Total removals | Transplanted | Died waiting |
|---|---|---|---|
| Kidney | 982,110 | 62.1% | 13.1% |
| Liver | 362,119 | 62.8% | 12.6% |
| Heart | 126,135 | 70.4% | 10.7% |
| Lung | 78,127 | 74.3% | 11.5% |
| Heart-lung | 2,627 | 46.4% | 24.4% |

Kidney carries 60% of all removals on its own and has the highest waitlist
mortality of the four high-volume organs. Heart is the inverse: the smallest of
the four by an order of magnitude, the highest transplant rate and the lowest
mortality. Heart-lung is tiny and by far the worst place to be.

Key structural patterns:
- **2018 allocation policy change** is visible in heart data as a step-up in transplant rate
- **COVID-19 signal (2020–2021):** transplant rate suppression across all organs, 2022 rebound
- **Kidney** dominates by volume; living-donor transplants provide a second positive-outcome pathway not available for most other organs
- **Liver** has a persistent "too sick to transplant" removal cluster, patients who deteriorate before a compatible organ is identified

### PGx dimension (transplant-critical drugs)

| Gene | Drug | Population | Finding |
|---|---|---|---|
| NUDT15 | Azathioprine | PEL | 16.47% would require a dose adjustment vs 0% CEU: the largest transplant-relevant divergence in the dataset, and one the European-calibrated guideline does not anticipate at all |
| CYP3A5 | Tacrolimus | PEL | 2.35% would require an adjustment vs 9.09% CEU. See the note below: the direction here is contested |
| CYP2C19 | Voriconazole | PEL | 91.8% Normal Metabolizers vs 58.6% CEU (+33pp): anti-fungal prophylaxis window shifts |
| DPYD | Fluorouracil / Capecitabine | PEL | 23.5% Poor Metabolizers vs 1.0% CEU: severe toxicity risk in post-transplant malignancy protocols |
| CYP2C9 | Warfarin | MXL, PEL | Anticoagulation management; combined VKORC1 and CYP2C9 interaction under analysis |

**CYP3A5 note, and an open discrepancy.** Tacrolimus is the first-line
immunosuppressant for most solid organ transplants, and CPIC recommends dose
adjustment on CYP3A5 *1 status. What this table cannot settle is the direction
for LATAM cohorts.

The 1000 Genomes phenotype calls used here put PEL at 97.65% non-expresser
against 90.91% for CEU, so fewer Peruvians would need an adjustment, not more.
Allele-frequency estimates from gnomAD point the opposite way, and so does the
published literature on CYP3A5 *1 in Amerindian populations. Two artifacts from
the same family of pipelines disagree, which means at least one of them is
wrong. Until that is resolved, the transplant-relevant claim this project
stands behind is the NUDT15 one, not this.

**DPYD note:** post-transplant malignancy is a leading cause of long-term mortality in transplant recipients. Latin American patients receiving capecitabine-based regimens without prior DPYD testing face disproportionate toxicity risk relative to European-calibrated CPIC dosing tables.

## Pipeline architecture

```
OPTN/UNOS removals (Excel exports, annual)
    └─ Bronze: raw ingestion, snapshot-dated, SHA256-hashed
    └─ Silver: normalize reason codes → 6 buckets, organ × year schema
    └─ Gold: us_fate_distribution.json (organ × year × reason_bucket × patients)

pgx-latam-atlas gold artifacts (copied, not re-generated here)
    └─ actionability_ranking.json
    └─ phenotype_distribution.json
    └─ allele_frequencies.json
    └─ metadata.json

Portfolio (data-dive-design-hub)
    └─ src/data/transplant-waitlist-atlas/us-fate-distribution.json
    └─ src/data/pgx/*.json
    └─ src/pages/WaitlistFatePgxPage.tsx  ← React dashboard
```

### Bronze → Silver transformation

The OPTN/UNOS Annual Report files export reason codes in a wide format with ~21 distinct removal reasons. The Silver layer normalizes these into 6 outcome buckets using a mapping table:

```python
REASON_MAP = {
    # Transplanted
    "Transplant: Cadaver": "transplanted_deceased",
    "Transplant: Living Donor": "transplanted_living",
    # Mortality
    "Died": "died_waiting",
    "Too sick to transplant": "removed_too_sick",
    # Positive off-ramp
    "Condition improved": "improved",
    "Transferred to another center": "other",
    # ... (full mapping in silver/reason_map.py)
}
```

### Gold artifact schema

`us-fate-distribution.json`: flat array of records:

```json
[
  {
    "year": 2023,
    "organ": "kidney",
    "reason_bucket": "died_waiting",
    "patients": 3842
  },
  ...
]
```

Fields: `year` (int), `organ` (str), `reason_bucket` (str), `patients` (int). 1,459 rows covering 1,623,190 removal events.

## Reproducing the data

```bash
# 1. Clone and install
git clone https://github.com/enriqew/waitlist-fate-pgx
cd waitlist-fate-pgx
pip install -e ".[dev,dbt]"

# 2. Pull the upstream artifacts (waitlist + PGx gold layers)
make ingest

# 3. Build the marts and export
make dbt-run
make export
```

This pipeline does not scrape OPTN directly. It consumes the gold artifacts
published by [`transplant-waitlist-atlas`](https://github.com/enriqew/transplant-waitlist-atlas)
and [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas), which is
why `make ingest` is a download and not an ETL run. The OPTN ingestion itself
lives upstream.

PGx artifacts are not re-generated here, run the [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) pipeline and copy the gold layer.

## File structure

```
waitlist-fate-pgx/
├── pyproject.toml
├── Makefile
├── ingest/
│   ├── waitlist_artifacts.py       # pulls transplant-waitlist-atlas gold layer
│   └── pgx_artifacts.py            # pulls pgx-latam-atlas gold layer
├── src/waitlist_fate_pgx/
│   ├── fate_analysis.py            # removal trends by organ, year, reason
│   ├── pgx_context.py              # transplant-relevant drug/gene profile
│   └── export.py                   # emits the combined artifact
├── dbt_project/models/
│   ├── staging/                    # stg_fate_distribution, stg_pgx_drug_impact
│   └── marts/                      # fct_fate_trends, fct_pgx_context
├── schemas/
│   └── fate-pgx-context.schema.json
└── data/exports/                   # gold artifact (gitignored)
```

## Related projects

| Project | Description |
|---|---|
| [`transplant-atlas`](https://github.com/enriqew/transplant-atlas) | Global donation and transplant counts (IRODaT, GODT, CENATRA) |
| [`transplant-waitlist-atlas`](https://github.com/enriqew/transplant-waitlist-atlas) | Full waitlist pipeline: world + Mexico state-level waiting counts |
| [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) | Pharmacogenomics atlas: 1000 Genomes × CPIC for LATAM cohorts |

## Data & licenses

**OPTN/UNOS.** HRSA requires the following acknowledgment, reproduced verbatim:

> *This work was supported in part by Health Resources and Services Administration contract HHSH250-2019-00001C. The content is the responsibility of the authors alone and does not necessarily reflect the views or policies of the Department of Health and Human Services, nor does mention of trade names, commercial products, or organizations imply endorsement by the U.S. Government.*

**1000 Genomes Project** Phase 3: open access, no reuse restrictions.
**PharmGKB**: CC BY-SA 4.0. **CPIC**: open-access guidelines.

## Methodological limits

The cohorts are not the patients. 1000 Genomes panels are population samples of
genetic ancestry, not transplant recipients, and OPTN does not report recipient
ancestry. Joining the two gives a population-level, ecological estimate. It is
not a measurement of any patient group, and an ecological association does not
transfer to an individual. Cohort sizes are small (61 to 113 individuals), so a
percentage point is a handful of people. None of this is clinical guidance.

## License

Code: MIT. See [LICENSE](LICENSE).
