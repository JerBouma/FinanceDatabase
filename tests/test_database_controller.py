"""Database Controller Tests"""

import pandas as pd
import polars as pl
import pytest

import financedatabase as fd
from financedatabase.utilities import dataframe_model

CSV = "symbol,name,sector,delisted\nAAA,Alpha,Energy,False\nNA,Nano Labs,,False\nOLD,Old Co,Energy,True\n"


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
    """Test that the Polars output has the same rows as the pandas output."""
    database = asset(use_local_location=True)
    as_pandas = getattr(database, method)(**kwargs)
    as_polars = getattr(database, method)(**kwargs, as_pandas=False)
    assert isinstance(as_polars, pl.DataFrame)
    assert as_polars.get_column(as_polars.columns[0]).to_list() == list(as_pandas.index)
    assert as_polars.columns[1:] == list(as_pandas.columns)
    pd.testing.assert_frame_equal(
        dataframe_model.convert_to_pandas(as_polars), pd.DataFrame(as_pandas)
    )


def test_show_options_as_polars() -> None:
    """Test that show_options returns Polars Series with as_pandas=False."""
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
    """Test that .data can be replaced and queries use the new frame."""
    equities = fd.Equities(use_local_location=True)
    frame = dataframe_model.convert_to_pandas(
        pl.read_csv(CSV.encode(), infer_schema=False)
    )
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


def test_module_show_options_as_polars() -> None:
    """Test that the module-level show_options returns Polars Series with as_pandas=False."""
    as_numpy = fd.show_options("equities", use_local_location=True)
    as_polars = fd.show_options("equities", use_local_location=True, as_pandas=False)
    assert list(as_polars) == list(as_numpy)
    assert all(isinstance(v, pl.Series) for v in as_polars.values())
    assert as_polars["sector"].to_list() == [str(v) for v in as_numpy["sector"]]
