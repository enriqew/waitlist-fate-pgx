"""Unit tests for fate trend analysis."""
import pytest
from src.waitlist_fate_pgx.fate_analysis import compute_fate_trends, FateSummary


SAMPLE = [
    {"year": 2020, "organ": "kidney", "reason_bucket": "transplanted_deceased", "patients": 10000},
    {"year": 2020, "organ": "kidney", "reason_bucket": "died_waiting", "patients": 2000},
    {"year": 2021, "organ": "kidney", "reason_bucket": "transplanted_deceased", "patients": 11000},
    {"year": 2021, "organ": "kidney", "reason_bucket": "died_waiting", "patients": 1800},
]


def test_pct_sums_to_100_per_year_organ():
    results = compute_fate_trends(SAMPLE, organ_filter="kidney")
    totals = {}
    for r in results:
        key = (r.year, r.organ)
        totals[key] = totals.get(key, 0.0) + r.pct_of_total
    for key, total in totals.items():
        assert abs(total - 100.0) < 0.1, f"{key}: {total}"


def test_yoy_none_for_first_year():
    results = compute_fate_trends(SAMPLE, organ_filter="kidney")
    year_2020 = [r for r in results if r.year == 2020]
    for r in year_2020:
        assert r.yoy_change is None


def test_yoy_computed_for_subsequent_years():
    results = compute_fate_trends(SAMPLE, organ_filter="kidney")
    year_2021 = [r for r in results if r.year == 2021]
    for r in year_2021:
        assert r.yoy_change is not None


def test_organ_filter():
    data = SAMPLE + [
        {"year": 2020, "organ": "liver", "reason_bucket": "transplanted_deceased", "patients": 5000},
    ]
    results = compute_fate_trends(data, organ_filter="kidney")
    assert all(r.organ == "kidney" for r in results)


def test_empty_input():
    results = compute_fate_trends([])
    assert results == []


def test_returns_sorted_by_organ_year_bucket():
    results = compute_fate_trends(SAMPLE)
    keys = [(r.organ, r.year, r.bucket) for r in results]
    assert keys == sorted(keys)


def test_zero_patients_handled():
    data = [
        {"year": 2020, "organ": "heart", "reason_bucket": "transplanted_deceased", "patients": 0},
        {"year": 2020, "organ": "heart", "reason_bucket": "died_waiting", "patients": 0},
    ]
    results = compute_fate_trends(data)
    for r in results:
        assert r.pct_of_total == 0.0
