"""Daily NYC 311 pipeline.

extract (NYC Open Data API -> S3 raw JSON)
  -> transform (clean, type, de-duplicate -> S3 Parquet)
  -> quality_checks (block bad data)
  -> load_warehouse (idempotent upsert + daily summary in Postgres)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="nyc311_daily",
    schedule="@daily",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["nyc311", "s3", "postgres"],
    doc_md=__doc__,
)
def nyc311_daily():
    @task
    def extract(ds=None) -> dict:
        from pipeline.steps import extract_step

        return extract_step(ds)

    @task
    def transform(_extracted: dict, ds=None) -> dict:
        from pipeline.steps import transform_step

        return transform_step(ds)

    @task
    def quality_checks(transformed: dict, ds=None) -> dict:
        from pipeline.steps import quality_step

        return quality_step(ds, transformed["raw_distinct_keys"])

    @task
    def load_warehouse(transformed: dict, _checked: dict, ds=None) -> dict:
        from pipeline.steps import load_step

        return load_step(ds, transformed["raw_rows"])

    extracted = extract()
    transformed = transform(extracted)
    checked = quality_checks(transformed)
    load_warehouse(transformed, checked)


nyc311_daily()
