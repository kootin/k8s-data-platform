import pytest

from pipeline import sample
from pipeline.quality import DataQualityError, enforce, run_checks
from pipeline.transform import transform


def _clean_day():
    raw = sample.generate("2026-11-01", rows=100)
    return transform(raw), len({r["unique_key"] for r in raw})


def _by_name(results):
    return {r.name: r for r in results}


def test_clean_day_passes_blocking_checks():
    df, distinct = _clean_day()
    results = run_checks(df, "2026-11-01", distinct)
    enforce(results)  # does not raise
    assert all(r.passed for r in results if r.severity == "error")


def test_missing_rows_fail_reconciliation():
    df, distinct = _clean_day()
    results = _by_name(run_checks(df.iloc[:-5], "2026-11-01", distinct))
    assert not results["reconciles_with_raw"].passed
    with pytest.raises(DataQualityError, match="reconciles_with_raw"):
        enforce(list(results.values()))


def test_rows_from_another_day_fail():
    df, distinct = _clean_day()
    results = _by_name(run_checks(df, "2026-11-02", distinct))
    assert not results["created_at_in_partition"].passed


def test_empty_extract_fails():
    df, _ = _clean_day()
    with pytest.raises(DataQualityError, match="row_count_positive"):
        enforce(run_checks(df.iloc[0:0], "2026-11-01", 0))


def test_unknown_borough_is_only_a_warning():
    df, distinct = _clean_day()
    df["borough"] = None
    results = run_checks(df, "2026-11-01", distinct)
    enforce(results)  # warn, not error
    assert not _by_name(results)["borough_known"].passed
