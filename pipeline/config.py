"""Runtime settings, read from environment variables.

Inside the cluster these come from the platform-config ConfigMap and the
platform-credentials Secret that Terraform creates.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    source: str
    s3_endpoint_url: str | None
    raw_bucket: str
    curated_bucket: str
    warehouse_db_url: str | None
    socrata_app_token: str | None
    api_timeout_seconds: int


def load_settings() -> Settings:
    return Settings(
        source=os.environ.get("NYC311_SOURCE", "api"),
        s3_endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
        raw_bucket=os.environ.get("RAW_BUCKET", "nyc311-raw"),
        curated_bucket=os.environ.get("CURATED_BUCKET", "nyc311-curated"),
        warehouse_db_url=os.environ.get("WAREHOUSE_DB_URL") or None,
        socrata_app_token=os.environ.get("SOCRATA_APP_TOKEN") or None,
        api_timeout_seconds=int(os.environ.get("NYC311_API_TIMEOUT", "60")),
    )
