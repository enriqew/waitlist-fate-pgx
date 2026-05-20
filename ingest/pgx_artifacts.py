"""
Ingest PGx gold-layer artifacts from pgx-latam-atlas pipeline.

These files are NOT re-generated here. Run the pgx-latam-atlas pipeline
and copy the gold artifacts into data/raw/:

    drug_impact_summary.json
    actionability_ranking.json
    phenotype_distribution.json
    allele_frequencies.json
    metadata.json

See https://github.com/enriqew/pgx-latam-atlas for the source pipeline.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from ._common import RAW_DIR, load_raw_json, snapshot_manifest

PGX_ARTIFACTS = [
    "drug_impact_summary.json",
    "actionability_ranking.json",
    "phenotype_distribution.json",
    "allele_frequencies.json",
    "metadata.json",
]

REQUIRED_ARTIFACTS = {"drug_impact_summary.json", "actionability_ranking.json"}


def validate_drug_impact(records: list[dict]) -> list[str]:
    """Return validation errors for drug_impact_summary.json records."""
    errors: list[str] = []
    required_fields = (
        "population_code",
        "drug_name",
        "gene_symbol",
        "percentage_requiring_change",
        "baseline_ceu_percentage",
        "delta_vs_baseline",
        "classification_strength",
    )
    for i, r in enumerate(records):
        for field in required_fields:
            if field not in r:
                errors.append(f"Record {i}: missing field '{field}'")
    return errors


def ingest_pgx_artifacts(source_dir: pathlib.Path | None = None) -> dict[str, list[dict]]:
    """
    Ingest PGx artifacts into data/raw/.

    If source_dir is provided, copies all known PGx artifact files from it.
    Otherwise expects them already present in data/raw/.
    """
    if source_dir is not None:
        for fname in PGX_ARTIFACTS:
            src = source_dir / fname
            if src.exists():
                dest = RAW_DIR / fname
                manifest = snapshot_manifest(src, dest, extra_meta={"pipeline": "pgx-latam-atlas"})
                print(f"Ingested {fname} — SHA256: {manifest['sha256']}")
            else:
                print(f"[skip] {fname} not found in {source_dir}")

    loaded: dict[str, list[dict]] = {}
    missing: list[str] = []
    for fname in REQUIRED_ARTIFACTS:
        dest = RAW_DIR / fname
        if not dest.exists():
            missing.append(fname)
        else:
            loaded[fname] = load_raw_json(fname)
            print(f"Loaded {fname}: {len(loaded[fname])} records")

    if missing:
        print(
            f"[error] Required PGx artifacts missing from data/raw/: {missing}\n"
            "Copy them from the pgx-latam-atlas gold layer or pass --source <dir>.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate drug impact
    if "drug_impact_summary.json" in loaded:
        errors = validate_drug_impact(loaded["drug_impact_summary.json"])
        if errors:
            print(f"[warning] drug_impact_summary.json: {len(errors)} validation issue(s)")
            for e in errors[:10]:
                print(f"  {e}")
        else:
            print("drug_impact_summary.json validation passed.")

    return loaded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PGx artifacts from pgx-latam-atlas")
    parser.add_argument(
        "--source",
        type=pathlib.Path,
        default=None,
        help="Directory containing pgx-latam-atlas gold artifacts",
    )
    args = parser.parse_args()
    ingest_pgx_artifacts(args.source)
