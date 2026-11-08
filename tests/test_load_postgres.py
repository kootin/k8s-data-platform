"""Integration test for the warehouse load. Needs a Postgres to talk to:

TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:55432/postgres pytest
"""

import os

import psycopg2
import pytest

from pipeline import sample
from pipeline.load import load_day
from pipeline.transform import transform

DB_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="TEST_DATABASE_URL not set")


def _count(sql):
    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


def test_load_is_idempotent():
    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS nyc311 CASCADE")

    raw = sample.generate("2026-11-01", rows=200)
    df = transform(raw)

    first = load_day(DB_URL, df, "2026-11-01", len(raw))
    second = load_day(DB_URL, df, "2026-11-01", len(raw))  # re-run the same day

    assert first["warehouse_rows"] == second["warehouse_rows"] == 200
    assert _count("SELECT count(*) FROM nyc311.service_requests") == 200
    assert _count("SELECT sum(requests) FROM nyc311.daily_borough_summary") == 200
    assert _count("SELECT count(*) FROM nyc311.load_audit") == 2
