"""Tests for the local cache, lazy Polars loading and the pandas/Polars outputs."""

from __future__ import annotations

import bz2
import time
from pathlib import Path

import pandas as pd
import polars as pl
import pytest
import requests

import financedatabase as fd
from financedatabase import data_loader

CSV = "symbol,name,sector,delisted\nAAA,Alpha,Energy,False\nNA,Nano Labs,,False\nOLD,Old Co,Energy,True\n"


@pytest.fixture
def cache(tmp_path, monkeypatch) -> Path:
    directory = tmp_path / "cache"
    monkeypatch.setenv("FINANCEDATABASE_CACHE_DIR", str(directory))
    return directory


class FakeResponse:
    def __init__(
        self, status: int, content: bytes = b"", etag: str | None = None
    ) -> None:
        self.status_code = status
        self.content = content
        self.headers = {"ETag": etag} if etag else {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(str(self.status_code))


def test_csv_is_read_as_text_with_na_ticker_kept(cache, tmp_path) -> None:
    source = tmp_path / "equities.bz2"
    source.write_bytes(bz2.compress(CSV.encode()))
    frame = data_loader.load_lazy("equities.bz2", "", tmp_path).collect()
    assert frame.schema == {
        c: pl.String for c in ["symbol", "name", "sector", "delisted"]
    }
    assert frame.get_column("symbol").to_list() == ["AAA", "NA", "OLD"]
    assert frame.get_column("sector").to_list() == ["Energy", None, "Energy"]


def test_local_cache_is_rebuilt_when_the_file_changes(cache, tmp_path) -> None:
    source = tmp_path / "equities.bz2"
    source.write_bytes(bz2.compress(CSV.encode()))
    assert data_loader.load_lazy("equities.bz2", "", tmp_path).collect().height == 3
    time.sleep(0.01)
    source.write_bytes(bz2.compress((CSV + "NEW,New Co,Energy,False\n").encode()))
    assert data_loader.load_lazy("equities.bz2", "", tmp_path).collect().height == 4
    assert len(list(cache.glob("local-equities-*.parquet"))) == 1  # stale copy removed


def test_remote_file_is_downloaded_once_and_checked_daily(cache, monkeypatch) -> None:
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(headers.get("If-None-Match"))
        if headers.get("If-None-Match") == '"v1"':
            return FakeResponse(304)
        return FakeResponse(200, bz2.compress(CSV.encode()), etag='"v1"')

    monkeypatch.setattr(data_loader.requests, "get", fake_get)
    url = "https://example.test/"
    assert data_loader.load_lazy("equities.bz2", url, None).collect().height == 3
    assert data_loader.load_lazy("equities.bz2", url, None).collect().height == 3
    assert calls == [None]  # second load within a day: no request at all

    monkeypatch.setattr(data_loader, "REFRESH_SECONDS", 0)
    assert data_loader.load_lazy("equities.bz2", url, None).collect().height == 3
    assert calls == [
        None,
        '"v1"',
    ]  # conditional request, answered 304: nothing downloaded


def test_cached_copy_is_used_when_offline(cache, monkeypatch) -> None:
    monkeypatch.setattr(
        data_loader.requests,
        "get",
        lambda *a, **k: FakeResponse(200, bz2.compress(CSV.encode()), etag='"v1"'),
    )
    data_loader.load_lazy("equities.bz2", "https://example.test/", None)

    def offline(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(data_loader.requests, "get", offline)
    monkeypatch.setattr(data_loader, "REFRESH_SECONDS", 0)
    frame = data_loader.load_lazy(
        "equities.bz2", "https://example.test/", None
    ).collect()
    assert frame.height == 3


def test_offline_without_cache_raises_a_clear_error(cache, monkeypatch) -> None:
    def offline(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(data_loader.requests, "get", offline)
    with pytest.raises(ValueError, match="Failed to load data"):
        fd.Cryptos(base_url="https://example.test/")


def test_to_pandas_matches_the_csv_reader() -> None:
    frame = pl.read_csv(CSV.encode(), infer_schema=False)
    result = data_loader.to_pandas(frame)
    expected = pd.read_csv(
        pd.io.common.StringIO(CSV), index_col=0, keep_default_na=False, na_values=[""]
    )
    pd.testing.assert_frame_equal(result, expected)
    assert data_loader.from_pandas(result).equals(frame)


@pytest.mark.parametrize(
    "asset, method, kwargs",
    [
        (fd.Equities, "select", {"country": "Canada", "sector": "Financials"}),
        (fd.Equities, "search", {"name": "bank", "only_primary_listing": True}),
        (fd.ETFs, "select", {"category_group": "Fixed Income"}),
        (fd.Funds, "select", {"category": "Blend", "only_primary_listing": True}),
        (fd.Indices, "search", {"index": "^\\^"}),
        (fd.Currencies, "select", {"base_currency": "EUR"}),
        (fd.Cryptos, "select", {"cryptocurrency": "ADA"}),
        (fd.Moneymarkets, "select", {"currency": "USD"}),
    ],
)
def test_polars_output_has_the_same_rows_as_pandas(asset, method, kwargs) -> None:
    database = asset(use_local_location=True)
    as_pandas = getattr(database, method)(**kwargs)
    as_polars = getattr(database, method)(**kwargs, as_pandas=False)
    assert isinstance(as_polars, pl.DataFrame)
    assert as_polars.get_column(as_polars.columns[0]).to_list() == list(as_pandas.index)
    assert as_polars.columns[1:] == list(as_pandas.columns)
    pd.testing.assert_frame_equal(
        data_loader.to_pandas(as_polars), pd.DataFrame(as_pandas)
    )


def test_show_options_as_polars() -> None:
    equities = fd.Equities(use_local_location=True)
    sectors = equities.show_options(selection="sector", as_pandas=False)
    assert isinstance(sectors, pl.Series)
    assert sectors.to_list() == list(equities.show_options(selection="sector"))
    everything = equities.show_options(as_pandas=False)
    assert all(isinstance(v, pl.Series) for v in everything.values())


def test_search_supports_python_only_regex() -> None:
    """Look-ahead isn't supported by Polars' regex engine; Python's re takes over."""
    equities = fd.Equities(use_local_location=True)
    result = equities.search(name="^(?=.*Bank)(?=.*Canada)")
    assert len(result) > 0
    assert result["name"].str.contains("Bank").all()
    assert result["name"].str.contains("Canada").all()


def test_data_can_be_replaced_for_tests(monkeypatch) -> None:
    equities = fd.Equities(use_local_location=True)
    frame = data_loader.to_pandas(pl.read_csv(CSV.encode(), infer_schema=False))
    frame["country"] = "Canada"
    equities.data = frame
    assert list(equities.select(country="Canada").index) == [
        "AAA",
        "NA",
    ]  # OLD is delisted
    assert list(equities.select(country="Canada", exclude_delisted=False).index) == [
        "AAA",
        "NA",
        "OLD",
    ]
