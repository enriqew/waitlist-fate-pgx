"""Export combined fate × PGx context artifacts to data/exports/ and artifacts/."""
from __future__ import annotations

import json
import pathlib
from dataclasses import asdict

from .fate_analysis import compute_fate_trends
from .pgx_context import load_pgx_risk_profile

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
EXPORTS_DIR = DATA_DIR / "exports"
ARTIFACTS_DIR = ROOT / "artifacts"

FATE_SOURCE = DATA_DIR / "raw" / "us-fate-distribution.json"
PGX_SOURCE = DATA_DIR / "raw" / "drug_impact_summary.json"

TRANSPLANT_DRUGS = ["tacrolimus", "azathioprine"]


def _load_json(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Source file not found: {path}\n"
            "Run `make ingest` or place the raw data files in data/raw/ first."
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def export_fate_trends(organs: list[str] | None = None) -> pathlib.Path:
    """Export fate trend summaries as JSON to data/exports/fate_trends.json."""
    raw = _load_json(FATE_SOURCE)
    all_results = []
    if organs:
        for organ in organs:
            all_results.extend(compute_fate_trends(raw, organ_filter=organ))
    else:
        all_results = compute_fate_trends(raw)

    out = EXPORTS_DIR / "fate_trends.json"
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump([asdict(r) for r in all_results], fh, indent=2)
    print(f"Exported {len(all_results)} fate trend records → {out}")
    return out


def export_pgx_context(min_gap: float = 5.0) -> pathlib.Path:
    """Export PGx context for transplant drugs to data/exports/pgx_context.json."""
    raw = _load_json(PGX_SOURCE)
    entries = load_pgx_risk_profile(raw, drug_filter=TRANSPLANT_DRUGS, min_absolute_gap=min_gap)

    out = EXPORTS_DIR / "pgx_context.json"
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump([asdict(e) for e in entries], fh, indent=2)
    print(f"Exported {len(entries)} PGx context records → {out}")
    return out


def export_combined_artifact() -> pathlib.Path:
    """Export a combined summary artifact to artifacts/fate_pgx_combined.json."""
    fate_raw = _load_json(FATE_SOURCE)
    pgx_raw = _load_json(PGX_SOURCE)

    fate_summaries = compute_fate_trends(fate_raw)
    pgx_entries = load_pgx_risk_profile(pgx_raw, drug_filter=TRANSPLANT_DRUGS)

    combined = {
        "fate_trends": [asdict(r) for r in fate_summaries],
        "pgx_context": [asdict(e) for e in pgx_entries],
    }

    out = ARTIFACTS_DIR / "fate_pgx_combined.json"
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(combined, fh, indent=2)
    print(f"Exported combined artifact → {out}")
    return out


if __name__ == "__main__":
    export_fate_trends()
    export_pgx_context()
    export_combined_artifact()
