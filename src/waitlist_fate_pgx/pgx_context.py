"""PGx risk profile for transplant-relevant drugs in LATAM populations."""
from __future__ import annotations

from dataclasses import dataclass

# Transplant-critical drugs with CPIC dosing guidelines
TRANSPLANT_DRUGS = [
    "tacrolimus",       # CNI immunosuppressant — CYP3A5
    "cyclosporine",     # CNI immunosuppressant — CYP3A4/5
    "azathioprine",     # Antimetabolite — TPMT, NUDT15
    "mycophenolate",    # Antimetabolite — UGT1A9
    "voriconazole",     # Antifungal prophylaxis — CYP2C19
    "warfarin",         # Anticoagulation — CYP2C9, VKORC1
]

# Primary pharmacogene per transplant drug
DRUG_GENE_MAP: dict[str, list[str]] = {
    "tacrolimus":   ["CYP3A5", "CYP3A4"],
    "cyclosporine": ["CYP3A5", "CYP3A4"],
    "azathioprine": ["TPMT", "NUDT15"],
    "mycophenolate": ["UGT1A9"],
    "voriconazole": ["CYP2C19"],
    "warfarin":     ["CYP2C9", "VKORC1"],
}


@dataclass
class PgxRiskEntry:
    population_code: str
    drug_name: str
    gene_symbol: str
    percentage_requiring_change: float
    baseline_ceu_percentage: float
    delta_vs_baseline: float
    classification_strength: str
    absolute_gap: float


def load_pgx_risk_profile(
    drug_impact: list[dict],
    drug_filter: list[str] | None = None,
    min_absolute_gap: float = 0.0,
) -> list[PgxRiskEntry]:
    """
    Build PGx risk profile from drug_impact_summary.json artifacts.

    Args:
        drug_impact: records from drug_impact_summary.json (pgx-latam-atlas gold layer)
        drug_filter: if provided, restrict to these drug names
        min_absolute_gap: only include entries where |delta_vs_baseline| >= this threshold
    Returns:
        PgxRiskEntry list sorted by population, then absolute_gap descending
    """
    filter_set = set(drug_filter) if drug_filter else None

    results: list[PgxRiskEntry] = []
    for r in drug_impact:
        drug = r.get("drug_name", "")
        if filter_set and drug not in filter_set:
            continue

        delta = float(r.get("delta_vs_baseline", 0) or 0)
        abs_gap = abs(delta)
        if abs_gap < min_absolute_gap:
            continue

        results.append(PgxRiskEntry(
            population_code=r.get("population_code", ""),
            drug_name=drug,
            gene_symbol=r.get("gene_symbol", ""),
            percentage_requiring_change=float(r.get("percentage_requiring_change", 0) or 0),
            baseline_ceu_percentage=float(r.get("baseline_ceu_percentage", 0) or 0),
            delta_vs_baseline=round(delta, 2),
            classification_strength=r.get("classification_strength", ""),
            absolute_gap=round(abs_gap, 2),
        ))

    return sorted(results, key=lambda e: (e.population_code, -e.absolute_gap))


def summarize_by_drug(entries: list[PgxRiskEntry]) -> dict[str, list[PgxRiskEntry]]:
    """Group PgxRiskEntry list by drug name."""
    summary: dict[str, list[PgxRiskEntry]] = {}
    for entry in entries:
        summary.setdefault(entry.drug_name, []).append(entry)
    return summary
