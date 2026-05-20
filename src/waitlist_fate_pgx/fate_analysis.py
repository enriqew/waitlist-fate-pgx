"""Aggregate OPTN waitlist fate buckets and compute year-over-year trends."""
from __future__ import annotations

from dataclasses import dataclass


FATE_BUCKETS = [
    "transplanted_deceased",
    "transplanted_living",
    "died_waiting",
    "removed_too_sick",
    "improved",
    "other",
]


@dataclass
class FateSummary:
    year: int
    organ: str
    bucket: str
    patients: int
    pct_of_total: float
    yoy_change: float | None  # percentage-point change vs prior year


def compute_fate_trends(
    raw: list[dict],
    organ_filter: str | None = None,
) -> list[FateSummary]:
    """
    Compute fate distribution trends from us-fate-distribution.json.

    Args:
        raw: list of {year, organ, reason_bucket, patients}
        organ_filter: if provided, restrict to this organ
    Returns:
        FateSummary list sorted by organ, year, bucket
    """
    if organ_filter:
        raw = [r for r in raw if r.get("organ") == organ_filter]

    # Compute totals per (year, organ)
    totals: dict[tuple[int, str], int] = {}
    for r in raw:
        key = (int(r["year"]), r["organ"])
        totals[key] = totals.get(key, 0) + int(r.get("patients", 0) or 0)

    # Build per (year, organ, bucket) pct
    pct_map: dict[tuple[int, str, str], float] = {}
    for r in raw:
        key = (int(r["year"]), r["organ"])
        total = totals.get(key, 0)
        if total > 0:
            bucket_key = (int(r["year"]), r["organ"], r["reason_bucket"])
            pct_map[bucket_key] = int(r.get("patients", 0) or 0) / total * 100

    results: list[FateSummary] = []
    for r in raw:
        year = int(r["year"])
        organ = r["organ"]
        bucket = r["reason_bucket"]

        pct = pct_map.get((year, organ, bucket), 0.0)
        prior_pct = pct_map.get((year - 1, organ, bucket))
        yoy = round(pct - prior_pct, 2) if prior_pct is not None else None

        results.append(FateSummary(
            year=year,
            organ=organ,
            bucket=bucket,
            patients=int(r.get("patients", 0) or 0),
            pct_of_total=round(pct, 2),
            yoy_change=yoy,
        ))

    return sorted(results, key=lambda s: (s.organ, s.year, s.bucket))
