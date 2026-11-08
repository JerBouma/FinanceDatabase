"""Missing numeric values are represented as JSON null in tool responses."""

import json

import polars as pl

from financedatabase.mcp_server.formatting_model import convert_to_records, format_page


def test_nan_is_missing_in_records():
    frame = pl.DataFrame({"market_cap": [float("nan"), 10.0, None], "symbol": ["A", "B", "C"]})
    assert convert_to_records(frame) == [
        {"market_cap": None, "symbol": "A"},
        {"market_cap": 10.0, "symbol": "B"},
        {"market_cap": None, "symbol": "C"},
    ]


def test_page_with_nan_is_standard_json():
    result = format_page(pl.DataFrame({"value": [float("nan")]}), 1, 0, 10, 100)
    payload = json.loads(result, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert payload["rows"] == [{"value": None}]
