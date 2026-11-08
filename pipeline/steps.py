"""The pipeline's steps, one function per Airflow task.

Each step reads its input from S3 and writes its output to S3 (or Postgres),
so any task can be retried on its own.
"""

from __future__ import annotations

import logging

from pipeline import extract as extract_mod
from pipeline import load as load_mod
from pipeline import quality, storage
from pipeline import transform as transform_mod
from pipeline.config import Settings, load_settings

log = logging.getLogger(__name__)


def extract_step(day: str, settings: Settings | None = None) -> dict:
    s = settings or load_settings()
    records = extract_mod.extract(day, s.source, app_token=s.socrata_app_token, timeout=s.api_timeout_seconds)
    key = storage.raw_key(day)
    storage.put_json(storage.s3_client(s.s3_endpoint_url), s.raw_bucket, key, records)
    log.info("wrote %d raw rows to s3://%s/%s", len(records), s.raw_bucket, key)
    return {"raw_rows": len(records), "raw_key": key}


def transform_step(day: str, settings: Settings | None = None) -> dict:
    s = settings or load_settings()
    client = storage.s3_client(s.s3_endpoint_url)
    records = storage.get_json(client, s.raw_bucket, storage.raw_key(day))
    df = transform_mod.transform(records)
    key = storage.curated_key(day)
    storage.put_parquet(client, s.curated_bucket, key, df)
    raw_distinct = len({r.get("unique_key") for r in records if r.get("unique_key") is not None})
    log.info("wrote %d clean rows to s3://%s/%s", len(df), s.curated_bucket, key)
    return {"raw_rows": len(records), "raw_distinct_keys": raw_distinct, "clean_rows": len(df)}


def quality_step(day: str, raw_distinct_keys: int, settings: Settings | None = None) -> dict:
    s = settings or load_settings()
    df = storage.get_parquet(storage.s3_client(s.s3_endpoint_url), s.curated_bucket, storage.curated_key(day))
    results = quality.run_checks(df, day, raw_distinct_keys)
    quality.enforce(results)
    return {r.name: r.passed for r in results}


def load_step(day: str, raw_rows: int, settings: Settings | None = None) -> dict:
    s = settings or load_settings()
    if not s.warehouse_db_url:
        raise RuntimeError("WAREHOUSE_DB_URL is not set")
    df = storage.get_parquet(storage.s3_client(s.s3_endpoint_url), s.curated_bucket, storage.curated_key(day))
    return load_mod.load_day(s.warehouse_db_url, df, day, raw_rows)
