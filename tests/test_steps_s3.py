"""Runs extract -> transform -> quality against a mocked S3 (moto)."""

import boto3
import pytest
from moto import mock_aws

from pipeline import steps
from pipeline.config import Settings


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    return Settings(
        source="sample",
        s3_endpoint_url=None,
        raw_bucket="nyc311-raw",
        curated_bucket="nyc311-curated",
        warehouse_db_url=None,
        socrata_app_token=None,
        api_timeout_seconds=5,
    )


@mock_aws
def test_steps_through_quality(settings):
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="nyc311-raw")
    s3.create_bucket(Bucket="nyc311-curated")

    extracted = steps.extract_step("2026-11-01", settings)
    transformed = steps.transform_step("2026-11-01", settings)
    checks = steps.quality_step("2026-11-01", transformed["raw_distinct_keys"], settings)

    assert extracted["raw_rows"] == 501
    assert transformed["clean_rows"] == 500
    assert checks["reconciles_with_raw"]
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket="nyc311-curated")["Contents"]]
    assert keys == ["nyc311/dt=2026-11-01/service_requests.parquet"]


@mock_aws
def test_load_requires_database(settings):
    with pytest.raises(RuntimeError, match="WAREHOUSE_DB_URL"):
        steps.load_step("2026-11-01", 1, settings)
