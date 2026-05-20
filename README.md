# waitlist-fate-pgx

**Transplant Waitlist Fate × Pharmacogenomics**

Intersects 30 years of US organ transplant waitlist removal data (OPTN/UNOS 1995–2026) with Latin American pharmacogenomic profiles (1000 Genomes Phase 3 × CPIC) to surface the genetic dimension of post-transplant risk — who dies waiting, and whether their ancestry predicts avoidable outcomes after transplant.

Live dashboard: [db0dj7zz9je7r.cloudfront.net/projects/waitlist-fate-pgx/demo](https://db0dj7zz9je7r.cloudfront.net/projects/waitlist-fate-pgx/demo)

---

## Background

Most pharmacogenomics (PGx) research focuses on the moment of prescribing. But for transplant patients, the prescribing window is **post-surgery** — and the drugs involved (tacrolimus, cyclosporine, mycophenolate, voriconazole, warfarin) have narrow therapeutic windows that are strongly modulated by pharmacogenes.

CPIC dosing guidelines for these drugs were anchored on European ancestry cohorts (CEU). Latin American populations — MXL (Mexican), PEL (Peruvian), CLM (Colombian), PUR (Puerto Rican) — show measurable divergence across CYP3A5, CYP2C19, CYP2C9, and DPYD. This project quantifies both the scale of waitlist mortality and the magnitude of that PGx gap.

## Data sources

### OPTN/UNOS Removal Registry

- **Coverage:** USA, annual, 1995–2026 (2026 partial/YTD)
- **Granularity:** organ × year × removal reason
- **Organs:** kidney, liver, heart, lung, pancreas, kidney–pancreas, heart–lung, intestine, vascular composite allograft (VCA)
- **Removal reasons (normalized buckets):**
  - `transplanted_deceased` — deceased-donor transplant (primary outcome)
  - `transplanted_living` — living-donor transplant (kidney, select multi-organ)
  - `improved` — condition improved or changed, removed from active list
  - `removed_too_sick` — clinical deterioration, no longer transplant-eligible
  - `died_waiting` — mortality on the waitlist (primary mortality metric)
  - `other` — administrative, duplicate registration, relocation, unknown
- **Access:** [optn.transplant.hrsa.gov/data](https://optn.transplant.hrsa.gov/data/) — Annual Report files

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

| Organ | Total Removals | Transplanted | Died Waiting |
|---|---|---|---|
| Kidney | ~430,000 | ~57% | ~8% |
| Liver | ~140,000 | ~68% | ~10% |
| Heart | ~80,000 | ~64% | ~15% |
| Lung | ~70,000 | ~58% | ~14% |

Key structural patterns:
- **2018 allocation policy change** is visible in heart data as a step-up in transplant rate
- **COVID-19 signal (2020–2021):** transplant rate suppression across all organs, 2022 rebound
- **Kidney** dominates by volume; living-donor transplants provide a second positive-outcome pathway not available for most other organs
- **Liver** has a persistent "too sick to transplant" removal cluster — patients who deteriorate before a compatible organ is identified

### PGx dimension (transplant-critical drugs)

| Gene | Drug | Population | Finding |
|---|---|---|---|
| CYP3A5 | Tacrolimus | PEL | Higher *1/*1 (extensive metabolizer) frequency vs CEU — standard dose produces subtherapeutic levels, increased rejection risk |
| CYP2C19 | Voriconazole | PEL | 91.8% Normal Metabolizers vs 58.6% CEU (+33pp) — anti-fungal prophylaxis window shifts |
| DPYD | Fluorouracil / Capecitabine | PEL | 23.5% Poor Metabolizers vs 1.0% CEU — severe toxicity risk in post-transplant malignancy protocols |
| CYP2C9 | Warfarin | MXL, PEL | Anticoagulation management; combined VKORC1+CYP2C9 interaction under analysis |

**CYP3A5 note:** tacrolimus is the first-line immunosuppressant for most solid organ transplants. The CPIC guideline recommends dose adjustment based on CYP3A5 *1 status, but this is not universally applied in Latin American transplant centers. The frequency difference between PEL and CEU in extensive metabolizer status is clinically actionable with a simple genotype test.

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

`us-fate-distribution.json` — flat array of records:

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

Fields: `year` (int), `organ` (str), `reason_bucket` (str), `patients` (int). 2,912 rows total.

## Reproducing the data

```bash
# 1. Clone and install
git clone https://github.com/enriqew/waitlist-fate-pgx
cd waitlist-fate-pgx
pip install -r requirements.txt

# 2. Download OPTN/UNOS Annual Report data
#    → optn.transplant.hrsa.gov/data/ → "By Organ" removal data tables
#    Place Excel files in data/raw/optn/

# 3. Run the pipeline
python pipeline/bronze/ingest_optn.py
python pipeline/silver/normalize_reasons.py
python pipeline/gold/export_fate_distribution.py

# 4. Copy gold artifact to portfolio
cp output/us_fate_distribution.json \
   ../data-dive-design-hub/src/data/transplant-waitlist-atlas/us-fate-distribution.json
```

PGx artifacts are not re-generated here — run the [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) pipeline and copy the gold layer.

## File structure

```
waitlist-fate-pgx/
├── README.md
├── requirements.txt
├── pipeline/
│   ├── bronze/
│   │   └── ingest_optn.py          # Raw file ingestion + snapshot dating
│   ├── silver/
│   │   ├── normalize_reasons.py    # Reason code → bucket mapping
│   │   └── reason_map.py           # Full OPTN reason code table
│   └── gold/
│       └── export_fate_distribution.py
├── data/
│   ├── raw/optn/                   # OPTN/UNOS Excel exports (gitignored, large)
│   └── snapshots/                  # SHA256 manifest per ingestion run
└── output/
    └── us_fate_distribution.json   # Gold artifact (committed here for reference)
```

## Related projects

| Project | Description |
|---|---|
| [`transplant-atlas`](https://github.com/enriqew/transplant-atlas) | Global donation and transplant counts (IRODaT, GODT, CENATRA) |
| [`transplant-waitlist-atlas`](https://github.com/enriqew/transplant-waitlist-atlas) | Full waitlist pipeline: world + Mexico state-level waiting counts |
| [`pgx-latam-atlas`](https://github.com/enriqew/pgx-latam-atlas) | Pharmacogenomics atlas: 1000 Genomes × CPIC for LATAM cohorts |

## License

Data: OPTN/UNOS data is publicly available under their terms of use. 1000 Genomes data is public domain. CPIC guidelines are CC-BY-4.0.

Code: MIT.
