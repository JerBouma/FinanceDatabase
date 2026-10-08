"""Cache Model Tests"""

import bz2
import io
import time
from pathlib import Path

import polars as pl
import pytest
import requests

import financedatabase as fd
from financedatabase import cache_model

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
            raise requests.exceptions.HTTPError(str(self.status_code), response=self)


def test_csv_is_read_as_text_with_na_ticker_kept(cache, tmp_path) -> None:
    """Test that the CSV is read as text, the NA ticker kept and delisted typed."""
    source = tmp_path / "equities.bz2"
    source.write_bytes(bz2.compress(CSV.encode()))
    frame = cache_model.load_lazy_frame("equities.bz2", "", tmp_path).collect()
    assert frame.schema == {
        "symbol": pl.String,
        "name": pl.String,
        "sector": pl.String,
        "delisted": pl.Boolean,
    }
    assert frame.get_column("symbol").to_list() == ["AAA", "NA", "OLD"]
    assert frame.get_column("sector").to_list() == ["Energy", None, "Energy"]


def test_local_cache_is_rebuilt_when_the_file_changes(cache, tmp_path) -> None:
    """Test that the local cache is rebuilt when the file changes."""
    source = tmp_path / "equities.bz2"
    source.write_bytes(bz2.compress(CSV.encode()))
    assert (
        cache_model.load_lazy_frame("equities.bz2", "", tmp_path).collect().height == 3
    )
    time.sleep(0.01)
    source.write_bytes(bz2.compress((CSV + "NEW,New Co,Energy,False\n").encode()))
    assert (
        cache_model.load_lazy_frame("equities.bz2", "", tmp_path).collect().height == 4
    )
    assert len(list(cache.glob("local-equities-*.parquet"))) == 1  # stale copy removed


def test_remote_file_is_downloaded_once_and_checked_daily(cache, monkeypatch) -> None:
    """Test that a remote file is downloaded once and then checked daily."""
    calls, parquet_calls = [], []

    def get_fake_response(url, headers, timeout):
        if url.endswith(".parquet"):
            parquet_calls.append(url)
            return FakeResponse(404)
        calls.append(headers.get("If-None-Match"))
        if headers.get("If-None-Match") == '"v1"':
            return FakeResponse(304)
        return FakeResponse(200, bz2.compress(CSV.encode()), etag='"v1"')

    monkeypatch.setattr(cache_model.requests, "get", get_fake_response)
    url = "https://example.test/"
    assert cache_model.load_lazy_frame("equities.bz2", url, None).collect().height == 3
    assert cache_model.load_lazy_frame("equities.bz2", url, None).collect().height == 3
    assert calls == [None]  # second load within a day: no request at all
    assert len(parquet_calls) == 1  # an unpublished Parquet file is not asked for again

    monkeypatch.setattr(cache_model, "REFRESH_SECONDS", 0)
    assert cache_model.load_lazy_frame("equities.bz2", url, None).collect().height == 3
    assert calls == [
        None,
        '"v1"',
    ]  # conditional request, answered 304: nothing downloaded
    assert len(parquet_calls) == 2


def test_cached_copy_is_used_when_offline(cache, monkeypatch) -> None:
    """Test that the cached copy is used when offline."""
    monkeypatch.setattr(
        cache_model.requests,
        "get",
        lambda url, **k: (
            FakeResponse(404)
            if url.endswith(".parquet")
            else FakeResponse(200, bz2.compress(CSV.encode()), etag='"v1"')
        ),
    )
    cache_model.load_lazy_frame("equities.bz2", "https://example.test/", None)

    def raise_offline_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(cache_model.requests, "get", raise_offline_error)
    monkeypatch.setattr(cache_model, "REFRESH_SECONDS", 0)
    frame = cache_model.load_lazy_frame(
        "equities.bz2", "https://example.test/", None
    ).collect()
    assert frame.height == 3


def test_offline_without_cache_raises_a_clear_error(cache, monkeypatch) -> None:
    """Test that being offline without a cache raises a clear error."""

    def raise_offline_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(cache_model.requests, "get", raise_offline_error)
    with pytest.raises(ValueError, match="Failed to load data"):
        fd.Cryptos(base_url="https://example.test/")


def test_published_parquet_is_used_without_conversion(cache, monkeypatch) -> None:
    """Test that a published Parquet file is stored and read as it is."""
    typed = pl.read_csv(CSV.encode(), infer_schema=False).with_columns(
        pl.col("delisted").eq("True")
    )
    buffer = io.BytesIO()
    typed.write_parquet(buffer)
    requested = []

    def get_fake_response(url, headers, timeout):
        requested.append(url)
        return FakeResponse(200, buffer.getvalue(), etag='"p1"')

    monkeypatch.setattr(cache_model.requests, "get", get_fake_response)
    frame = cache_model.load_lazy_frame(
        "equities.bz2", "https://example.test/", None
    ).collect()
    assert requested == ["https://example.test/equities.parquet"]
    assert frame.equals(typed)


def test_local_parquet_is_preferred(cache, tmp_path) -> None:
    """Test that a local Parquet file next to the bz2 is read directly."""
    typed = pl.read_csv(CSV.encode(), infer_schema=False).with_columns(
        pl.col("delisted").eq("True")
    )
    typed.write_parquet(tmp_path / "equities.parquet")
    (tmp_path / "equities.bz2").write_bytes(b"not used")
    frame = cache_model.load_lazy_frame("equities.bz2", "", tmp_path).collect()
    assert frame.equals(typed)
