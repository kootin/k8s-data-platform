import pandas as pd

from pipeline import sample
from pipeline.transform import OUTPUT_COLUMNS, transform

RAW = [
    {
        "unique_key": "100",
        "created_date": "2026-11-01T08:00:00.000",
        "closed_date": "2026-11-01T10:30:00.000",
        "agency": "NYPD",
        "complaint_type": " Noise - Residential ",
        "borough": "brooklyn",
        "incident_zip": "11201-1234",
        "latitude": "40.69",
        "longitude": "-73.99",
    },
    {
        "unique_key": "101",
        "created_date": "2026-11-01T09:00:00.000",
        "closed_date": "2026-11-01T08:00:00.000",  # closed before created
        "agency": "DOT",
        "complaint_type": "Street Condition",
        "borough": "Unspecified",
        "incident_zip": "N/A",
    },
    {  # repeated row from the API
        "unique_key": "100",
        "created_date": "2026-11-01T08:00:00.000",
        "closed_date": "2026-11-01T10:30:00.000",
        "agency": "NYPD",
        "complaint_type": "Noise - Residential",
        "borough": "BROOKLYN",
        "incident_zip": "11201",
    },
]


def test_output_columns_and_dedupe():
    df = transform(RAW)
    assert list(df.columns) == OUTPUT_COLUMNS
    assert len(df) == 2
    assert df["unique_key"].is_unique


def test_types_and_cleaning():
    df = transform(RAW).set_index("unique_key")
    assert df.loc[100, "borough"] == "BROOKLYN"
    assert df.loc[100, "incident_zip"] == "11201"
    assert df.loc[100, "complaint_type"] == "Noise - Residential"
    assert df.loc[100, "hours_to_close"] == 2.5
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])


def test_bad_values_become_null_not_errors():
    df = transform(RAW).set_index("unique_key")
    assert pd.isna(df.loc[101, "borough"])  # "Unspecified"
    assert pd.isna(df.loc[101, "incident_zip"])  # "N/A"
    assert pd.isna(df.loc[101, "hours_to_close"])  # negative duration
    assert pd.isna(df.loc[101, "latitude"])  # missing column value


def test_sample_round_trip():
    raw = sample.generate("2026-11-01", rows=50)
    df = transform(raw)
    assert len(df) == 50  # the repeated row is dropped
