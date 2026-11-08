"""Thin S3 helpers. Works against LocalStack or real AWS."""

from __future__ import annotations

import io
import json

import boto3
import pandas as pd


def s3_client(endpoint_url: str | None):
    return boto3.client("s3", endpoint_url=endpoint_url)


def raw_key(day: str) -> str:
    return f"nyc311/dt={day}/service_requests.json"


def curated_key(day: str) -> str:
    return f"nyc311/dt={day}/service_requests.parquet"


def put_json(client, bucket: str, key: str, records: list[dict]) -> None:
    body = json.dumps(records).encode("utf-8")
    client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")


def get_json(client, bucket: str, key: str) -> list[dict]:
    obj = client.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read())


def put_parquet(client, bucket: str, key: str, df: pd.DataFrame) -> None:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    client.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())


def get_parquet(client, bucket: str, key: str) -> pd.DataFrame:
    obj = client.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))
