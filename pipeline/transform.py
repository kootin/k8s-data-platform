"""Clean the raw API rows into a typed, de-duplicated table."""

from __future__ import annotations

import pandas as pd

OUTPUT_COLUMNS = [
    "unique_key",
    "created_at",
    "closed_at",
    "agency",
    "complaint_type",
    "descriptor",
    "status",
    "borough",
    "incident_zip",
    "latitude",
    "longitude",
    "hours_to_close",
]

VALID_BOROUGHS = {"MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"}


def transform(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    for col in [
        "unique_key",
        "created_date",
        "closed_date",
        "agency",
        "complaint_type",
        "descriptor",
        "status",
        "borough",
        "incident_zip",
        "latitude",
        "longitude",
    ]:
        if col not in df.columns:
            df[col] = None

    out = pd.DataFrame()
    out["unique_key"] = pd.to_numeric(df["unique_key"], errors="coerce").astype("Int64")
    out["created_at"] = pd.to_datetime(df["created_date"], errors="coerce")
    out["closed_at"] = pd.to_datetime(df["closed_date"], errors="coerce")
    for col in ["agency", "complaint_type", "descriptor", "status"]:
        out[col] = df[col].astype("string").str.strip()

    borough = df["borough"].astype("string").str.strip().str.upper()
    out["borough"] = borough.where(borough.isin(VALID_BOROUGHS))

    zip5 = df["incident_zip"].astype("string").str.extract(r"^(\d{5})", expand=False)
    out["incident_zip"] = zip5
    out["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    hours = (out["closed_at"] - out["created_at"]).dt.total_seconds() / 3600
    # A close time before the open time is a source data error; keep the row
    # but don't report a negative duration.
    out["hours_to_close"] = hours.where(hours >= 0).round(2)

    out = out.drop_duplicates(subset="unique_key", keep="last").reset_index(drop=True)
    return out[OUTPUT_COLUMNS]
