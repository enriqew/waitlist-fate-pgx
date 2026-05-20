"""
Ingest OPTN/UNOS waitlist fate distribution artifacts.

Expected input: us-fate-distribution.json produced by the transplant-waitlist-atlas pipeline.
The file should be placed in data/raw/ manually, or the path provided via CLI.

Schema:
    [{"year": int, "organ": str, "reason_bucket": str, "patients": int}, ...]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from ._common import RAW_DIR, load_raw_json, snapshot_manifest

FATE_FILENAME = "us-fate-distribution.json"
EXPECTED_BUCKETS = {
    "transplanted_deceased",
    "transplanted_living",
    "died_waiting",
    "removed_too_sick",
    "improved",
    "other",
}


def validate_fate_records(records: list[dict]) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    errors: list[str] = []
    for i, r in enumerate(records):
        for field in ("year", "organ", "reason_bucket", "patients"):
            if field not in r:
                errors.append(f"Record {i}: missing field '{field}'")
        if "reason_bucket" in r and r["reason_bucket"] not in EXPECTED_BUCKETS:
            errors.append(
                f"Record {i}: unexpected reason_bucket '{r['reason_bucket']}'"
                f" (expected one of {sorted(EXPECTED_BUCKETS)})"
            )
    return errors


def ingest_fate_distribution(source_path: pathlib.Path | None = None) -> list[dict]:
    """
    Ingest OPTN fate distribution JSON into data/raw/.

    If source_path is None, expects the file to already be at data/raw/us-fate-distribution.json
    (e.g. copied manually from the transplant-waitlist-atlas gold layer).
    """
    dest = RAW_DIR / FATE_FILENAME

    if source_path is not None:
        print(f"Copying {source_path} → {dest}")
        manifest = snapshot_manifest(source_path, dest, extra_meta={"pipeline": "transplant-waitlist-atlas"})
        print(f"SHA256: {manifest['sha256']}")

    if not dest.exists():
        print(
            f"[error] {dest} not found.\n"
            "Place us-fate-distribution.json in data/raw/ or pass --source <path>.",
            file=sys.stderr,
        )
        sys.exit(1)

    records = load_raw_json(FATE_FILENAME)
    print(f"Loaded {len(records)} fate distribution records.")

    errors = validate_fate_records(records)
    if errors:
        print(f"[warning] {len(errors)} validation issue(s):")
        for e in errors[:10]:
            print(f"  {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print("Validation passed.")

    organs = sorted({r["organ"] for r in records})
    years = sorted({r["year"] for r in records})
    print(f"Organs: {organs}")
    print(f"Years:  {min(years)}–{max(years)} ({len(years)} years)")

    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest OPTN fate distribution data")
    parser.add_argument("--source", type=pathlib.Path, default=None, help="Path to source JSON file")
    args = parser.parse_args()
    ingest_fate_distribution(args.source)
