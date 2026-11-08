"""Data quality checks that gate the warehouse load.

A failed "error" check stops the run before anything reaches Postgres.
A failed "warn" check is logged and the run continues.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

log = logging.getLogger(__name__)


class DataQualityError(Exception):
    pass


@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str  # "error" or "warn"
    detail: str


def run_checks(df: pd.DataFrame, day: str, raw_distinct_keys: int) -> list[CheckResult]:
    results: list[CheckResult] = []

    def add(name: str, passed: bool, severity: str, detail: str) -> None:
        results.append(CheckResult(name, bool(passed), severity, detail))

    add("row_count_positive", len(df) > 0, "error", f"{len(df)} rows")

    # Every distinct key that came from the API must land in the clean table.
    add(
        "reconciles_with_raw",
        len(df) == raw_distinct_keys,
        "error",
        f"clean={len(df)} raw_distinct_keys={raw_distinct_keys}",
    )

    dupes = int(df["unique_key"].duplicated().sum())
    add("unique_key_unique", dupes == 0, "error", f"{dupes} duplicate keys")

    for col in ["unique_key", "created_at", "complaint_type"]:
        nulls = int(df[col].isna().sum())
        add(f"{col}_not_null", nulls == 0, "error", f"{nulls} nulls")

    start = pd.Timestamp(date.fromisoformat(day))
    end = start + timedelta(days=1)
    outside = int(((df["created_at"] < start) | (df["created_at"] >= end)).sum())
    add("created_at_in_partition", outside == 0, "error", f"{outside} rows outside {day}")

    if len(df):
        unknown_pct = float(df["borough"].isna().mean() * 100)
        add("borough_known", unknown_pct <= 10, "warn", f"{unknown_pct:.1f}% unknown borough")

        bad_close = int((df["closed_at"] < df["created_at"]).sum())
        add("closed_after_created", bad_close == 0, "warn", f"{bad_close} rows closed before created")

    return results


def enforce(results: list[CheckResult]) -> None:
    for r in results:
        level = logging.INFO if r.passed else (logging.ERROR if r.severity == "error" else logging.WARNING)
        log.log(level, "%-26s %s  (%s)", r.name, "PASS" if r.passed else "FAIL", r.detail)
    failed = [r for r in results if not r.passed and r.severity == "error"]
    if failed:
        names = ", ".join(r.name for r in failed)
        raise DataQualityError(f"{len(failed)} blocking check(s) failed: {names}")
