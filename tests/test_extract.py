import pytest

from pipeline import extract


def test_day_window_covers_one_day():
    assert extract.day_window("2026-11-01") == ("2026-11-01T00:00:00", "2026-11-02T00:00:00")


def test_build_params_filters_orders_and_pages():
    params = extract.build_params("2026-11-01", offset=50_000)
    assert params["$where"] == (
        "created_date >= '2026-11-01T00:00:00' AND created_date < '2026-11-02T00:00:00'"
    )
    assert params["$order"] == "unique_key"
    assert params["$offset"] == "50000"
    assert "complaint_type" in params["$select"]


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages):
        self.pages = list(pages)
        self.headers = {}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(params)
        return FakeResponse(self.pages.pop(0))


def test_fetch_pages_until_short_page(monkeypatch):
    monkeypatch.setattr(extract, "PAGE_SIZE", 2)
    session = FakeSession([[{"unique_key": "1"}, {"unique_key": "2"}], [{"unique_key": "3"}]])
    rows = extract.fetch_from_api("2026-11-01", session=session)
    assert [r["unique_key"] for r in rows] == ["1", "2", "3"]
    assert [c["$offset"] for c in session.calls] == ["0", "2"]


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError):
        extract.extract("2026-11-01", source="ftp")
