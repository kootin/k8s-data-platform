"""Extract one day of NYC 311 service requests.

Source: NYC Open Data, dataset erm2-nwe9 ("311 Service Requests from 2010 to
Present"), via the Socrata API. No API key is needed; an app token only
raises the rate limit.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta

import requests

from pipeline import sample

log = logging.getLogger(__name__)

API_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGE_SIZE = 50_000
COLUMNS = [
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
]


def day_window(day: str) -> tuple[str, str]:
    start = date.fromisoformat(day)
    end = start + timedelta(days=1)
    return f"{start.isoformat()}T00:00:00", f"{end.isoformat()}T00:00:00"


def build_params(day: str, offset: int, limit: int = PAGE_SIZE) -> dict[str, str]:
    start, end = day_window(day)
    return {
        "$select": ",".join(COLUMNS),
        "$where": f"created_date >= '{start}' AND created_date < '{end}'",
        "$order": "unique_key",
        "$limit": str(limit),
        "$offset": str(offset),
    }


def _get_with_retry(session: requests.Session, params: dict, timeout: int, attempts: int = 4):
    for attempt in range(1, attempts + 1):
        try:
            resp = session.get(API_URL, params=params, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"retryable status {resp.status_code}", response=resp)
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            retryable = not isinstance(exc, requests.HTTPError) or (
                exc.response is not None and exc.response.status_code in (429, 500, 502, 503, 504)
            )
            if not retryable or attempt == attempts:
                raise
            wait = 2**attempt
            log.warning("API call failed (%s), retry %d/%d in %ds", exc, attempt, attempts, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_from_api(
    day: str,
    app_token: str | None = None,
    timeout: int = 60,
    session: requests.Session | None = None,
) -> list[dict]:
    session = session or requests.Session()
    if app_token:
        session.headers["X-App-Token"] = app_token

    records: list[dict] = []
    offset = 0
    while True:
        page = _get_with_retry(session, build_params(day, offset), timeout)
        records.extend(page)
        log.info("fetched %d rows (offset %d)", len(page), offset)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return records


def extract(day: str, source: str, app_token: str | None = None, timeout: int = 60) -> list[dict]:
    if source == "sample":
        log.info("using the bundled offline sample for %s", day)
        return sample.generate(day)
    if source == "api":
        return fetch_from_api(day, app_token=app_token, timeout=timeout)
    raise ValueError(f"unknown NYC311_SOURCE {source!r} (expected 'api' or 'sample')")
