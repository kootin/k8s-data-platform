"""Load the clean day into the Postgres warehouse.

Every step is idempotent: re-running a day updates rows in place instead of
duplicating them, so backfills and retries are safe.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

log = logging.getLogger(__name__)

SCHEMA_SQL = (Path(__file__).parent / "sql" / "schema.sql").read_text()

COLUMNS = [
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

UPSERT_SQL = f"""
INSERT INTO nyc311.service_requests ({", ".join(COLUMNS)}, loaded_at)
VALUES %s
ON CONFLICT (unique_key) DO UPDATE SET
  {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != "unique_key")},
  loaded_at = now()
"""

SUMMARY_SQL = """
DELETE FROM nyc311.daily_borough_summary WHERE report_date = %(day)s;
INSERT INTO nyc311.daily_borough_summary
  (report_date, borough, complaint_type, requests, closed_requests, median_hours_to_close)
SELECT
  %(day)s::date,
  COALESCE(borough, 'UNKNOWN'),
  complaint_type,
  count(*),
  count(closed_at),
  percentile_cont(0.5) WITHIN GROUP (ORDER BY hours_to_close)
FROM nyc311.service_requests
WHERE created_at >= %(day)s::date AND created_at < %(next_day)s::date
GROUP BY 1, 2, 3;
"""


def _clean(value):
    if value is None or value is pd.NaT:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


def rows_from_frame(df: pd.DataFrame) -> list[tuple]:
    return [tuple(_clean(v) for v in row) for row in df[COLUMNS].itertuples(index=False, name=None)]


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)


def load_day(db_url: str, df: pd.DataFrame, day: str, raw_rows: int) -> dict:
    next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    rows = rows_from_frame(df)
    with psycopg2.connect(db_url) as conn:  # one transaction: all or nothing
        ensure_schema(conn)
        with conn.cursor() as cur:
            execute_values(
                cur,
                UPSERT_SQL,
                rows,
                template="(" + ", ".join(["%s"] * len(COLUMNS)) + ", now())",
                page_size=5000,
            )
            cur.execute(SUMMARY_SQL, {"day": day, "next_day": next_day})
            cur.execute(
                "SELECT count(*) FROM nyc311.service_requests "
                "WHERE created_at >= %s::date AND created_at < %s::date",
                (day, next_day),
            )
            in_warehouse = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO nyc311.load_audit (report_date, raw_rows, clean_rows, warehouse_rows)
                VALUES (%s, %s, %s, %s)
                """,
                (day, raw_rows, len(df), in_warehouse),
            )
    conn.close()
    log.info("loaded %s: raw=%d clean=%d warehouse=%d", day, raw_rows, len(df), in_warehouse)
    return {"day": day, "raw_rows": raw_rows, "clean_rows": len(df), "warehouse_rows": in_warehouse}
