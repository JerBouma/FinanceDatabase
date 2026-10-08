"""MCP tool tests: registration, bounded output, pagination, errors and search."""

import asyncio
import json

import polars as pl
import pytest

import financedatabase as fd
from tests.mcp_server.conftest import call_json, call_text

ASSET_TOOLS = {
    "equities": fd.Equities,
    "etfs": fd.ETFs,
    "funds": fd.Funds,
    "indices": fd.Indices,
    "currencies": fd.Currencies,
    "cryptos": fd.Cryptos,
    "moneymarkets": fd.Moneymarkets,
}
UTILITY_TOOLS = {"search_categories", "show_options", "search_instruments"}


@pytest.fixture(scope="module")
def tools(server):
    return {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}


def test_every_tool_is_registered(tools):
    """Test that one tool per asset class plus the discovery tools exist."""
    assert set(tools) == set(ASSET_TOOLS) | UTILITY_TOOLS


def test_tools_are_annotated_read_only(tools):
    """Test that every tool is marked read-only, idempotent and titled."""
    for tool in tools.values():
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is False
        assert tool.annotations.title
        assert tool.description


@pytest.mark.parametrize("name", list(ASSET_TOOLS))
def test_asset_tool_parameters_mirror_select(tools, name):
    """Test that the filters are the class's select() filters, each described."""
    cls = ASSET_TOOLS[name]
    properties = tools[name].inputSchema["properties"]
    for field in cls.FIELDS:
        assert field in properties
    for common in ("query", "show_columns", "include_summary", "limit", "offset"):
        assert common in properties
    for key, schema in properties.items():
        assert schema.get("description"), f"{name}.{key} has no description"
    assert ("include_delisted" in properties) == (name in ("equities", "etfs"))
    assert ("only_primary_listing" in properties) == (
        name in ("equities", "etfs", "funds")
    )
    assert properties["limit"]["default"] == 25
    assert not tools[name].inputSchema.get("required")


@pytest.mark.parametrize("name", list(ASSET_TOOLS))
def test_asset_tool_returns_bounded_json(server, name):
    """Test that every asset tool returns compact JSON within the limit, without summaries."""
    spec = server.provider.specs[name]
    payload = call_json(server.mcp, name, {"limit": 5})
    assert payload["asset_class"] == name
    assert payload["returned"] == len(payload["rows"]) <= 5
    assert payload["total"] >= payload["returned"] > 0
    assert payload["offset"] == 0
    assert payload["columns"] == spec.default_columns
    assert "summary" not in payload["columns"]
    for row in payload["rows"]:
        assert list(row) == payload["columns"]
    if payload["total"] > 5:
        assert "offset=5" in payload["_notes"][-1]


def test_default_limit_and_hard_cap(server):
    """Test the default page size and that no call returns more than 200 rows."""
    assert call_json(server.mcp, "equities")["returned"] == 25

    capped = call_json(server.mcp, "equities", {"limit": 100_000})
    assert capped["returned"] == capped["limit"] == 200
    assert capped["total"] > 200
    assert any("capped at 200" in note for note in capped["_notes"])

    assert call_json(server.mcp, "equities", {"limit": 0})["returned"] == 1


def test_pagination_walks_without_overlap(server):
    """Test that consecutive pages share the total and don't repeat rows."""
    arguments = {"country": "Netherlands", "limit": 10}
    first = call_json(server.mcp, "equities", arguments)
    second = call_json(server.mcp, "equities", {**arguments, "offset": 10})
    assert first["total"] == second["total"] > 20
    assert second["offset"] == 10
    first_symbols = {row["symbol"] for row in first["rows"]}
    second_symbols = {row["symbol"] for row in second["rows"]}
    assert len(first_symbols) == len(second_symbols) == 10
    assert not first_symbols & second_symbols
    assert "offset=10" in first["_notes"][-1]

    beyond = call_json(server.mcp, "equities", {**arguments, "offset": 100_000})
    assert beyond["returned"] == 0
    assert "past the last row" in beyond["_notes"][-1]


def test_pages_match_the_package_select(server):
    """Test that the tool returns exactly what select() returns, in the same order."""
    expected = fd.Equities(use_local_location=True).select(
        country="Netherlands", sector="Financials", as_pandas=False
    )
    payload = call_json(
        server.mcp,
        "equities",
        {"country": "netherlands", "sector": "Financials", "limit": 200},
    )
    assert payload["total"] == expected.height
    assert [row["symbol"] for row in payload["rows"]] == expected.get_column(
        "symbol"
    ).to_list()[:200]


def test_show_columns_and_summary_truncation(server):
    """Test column selection, the opt-in summary and its truncation."""
    payload = call_json(
        server.mcp, "equities", {"query": "AAPL", "show_columns": "Name, country"}
    )
    assert payload["columns"] == ["symbol", "name", "country"]

    payload = call_json(
        server.mcp, "equities", {"query": "AAPL", "include_summary": True, "limit": 3}
    )
    assert payload["columns"][:3] == ["symbol", "name", "summary"]
    summaries = [row["summary"] for row in payload["rows"] if row["summary"]]
    assert summaries
    assert all(len(summary) <= 300 for summary in summaries)
    assert any(summary.endswith("…") for summary in summaries)


def test_multiple_values_keep_commas_inside_values(server):
    """Test comma-separated and list input, including values that contain commas."""
    expected = fd.Equities(use_local_location=True).select(
        country="Germany",
        industry=["Hotels, Restaurants & Leisure", "Banks"],
        as_pandas=False,
    )
    as_text = call_json(
        server.mcp,
        "equities",
        {"country": "Germany", "industry": "Hotels, Restaurants & Leisure, Banks"},
    )
    as_list = call_json(
        server.mcp,
        "equities",
        {"country": "Germany", "industry": ["Banks", "Hotels, Restaurants & Leisure"]},
    )
    assert as_text["total"] == as_list["total"] == expected.height


def test_invalid_filter_returns_package_message_with_suggestions(server):
    """Test that a typo returns the package's message plus a 'Did you mean'."""
    text = call_text(server.mcp, "equities", {"sector": "Tech"})
    assert text.startswith("Invalid input for `equities`")
    assert "The sector 'Tech' is not available in the database." in text
    assert "Did you mean 'Information Technology'" in text

    text = call_text(server.mcp, "equities", {"country": "Netherland"})
    assert "Did you mean 'Netherlands'" in text

    # Many values: point to show_options rather than listing them all.
    text = call_text(server.mcp, "etfs", {"family": "Vanguard"})
    assert "'Vanguard Asset Management'" in text
    assert "show_options(asset_class='etfs', selection='family')" in text


def test_invalid_column_returns_suggestions(server):
    """Test that an unknown column name is explained with suggestions."""
    text = call_text(server.mcp, "equities", {"show_columns": "sectr"})
    assert "Unknown column 'sectr'" in text
    assert "Did you mean: sector?" in text


@pytest.fixture(scope="module")
def delisted_symbol():
    lazy = fd.Equities(use_local_location=True).get_lazy_frame()
    return lazy.filter(pl.col("delisted")).select("symbol").head(1).collect().item()


def test_include_delisted(server, delisted_symbol):
    """Test that delisted equities are hidden by default and flagged when included."""
    hidden = call_json(server.mcp, "equities", {"query": delisted_symbol})
    assert delisted_symbol not in {row["symbol"] for row in hidden["rows"]}

    shown = call_json(
        server.mcp, "equities", {"query": delisted_symbol, "include_delisted": True}
    )
    assert shown["columns"][-1] == "delisted"
    assert shown["rows"][0]["symbol"] == delisted_symbol
    assert shown["rows"][0]["delisted"] is True

    listed = call_json(server.mcp, "equities", {"limit": 1})["total"]
    everything = call_json(
        server.mcp, "equities", {"limit": 1, "include_delisted": True}
    )["total"]
    assert everything > listed


def test_query_ranks_exact_symbol_first(server):
    """Test that an exact symbol match comes first and the query is case-insensitive."""
    payload = call_json(server.mcp, "equities", {"query": "aapl", "limit": 3})
    assert payload["rows"][0]["symbol"] == "AAPL"
    for row in payload["rows"]:
        assert "aapl" in row["symbol"].lower() or "aapl" in row["name"].lower()


def test_query_is_literal_not_regex(server):
    """Test that characters with a regex meaning are matched literally."""
    payload = call_json(server.mcp, "indices", {"query": "S&P 500", "limit": 5})
    assert payload["total"] > 0
    assert all("s&p 500" in row["name"].lower() for row in payload["rows"])
    assert call_json(server.mcp, "equities", {"query": "(["})["total"] == 0


def test_search_instruments_across_asset_classes(server):
    """Test the cross-class search, its counts and its asset class column."""
    payload = call_json(server.mcp, "search_instruments", {"query": "apple"})
    assert payload["columns"][0] == "asset_class"
    assert len(payload["matches_per_asset_class"]) >= 2
    assert payload["total"] == sum(payload["matches_per_asset_class"].values())
    assert payload["rows"][0]["symbol"] == "AAPL"
    assert {row["asset_class"] for row in payload["rows"]} <= set(ASSET_TOOLS)

    only_cryptos = call_json(
        server.mcp,
        "search_instruments",
        {"query": "ethereum", "asset_classes": "cryptos", "limit": 5},
    )
    assert only_cryptos["returned"] == 5
    assert {row["asset_class"] for row in only_cryptos["rows"]} == {"cryptos"}

    paged = call_json(
        server.mcp, "search_instruments", {"query": "apple", "limit": 5, "offset": 5}
    )
    first = call_json(server.mcp, "search_instruments", {"query": "apple", "limit": 10})
    assert [row["symbol"] for row in paged["rows"]] == [
        row["symbol"] for row in first["rows"][5:10]
    ]


def test_search_instruments_matches_isin(server):
    """Test that an ISIN finds its instrument."""
    lazy = fd.Equities(use_local_location=True).get_lazy_frame()
    symbol, isin = (
        lazy.filter(
            pl.col("isin").is_not_null()
            & ~pl.col("delisted")
            & ~pl.col("symbol").str.contains(".", literal=True)
        )
        .select("symbol", "isin")
        .head(1)
        .collect()
        .row(0)
    )
    payload = call_json(server.mcp, "search_instruments", {"query": isin.lower()})
    assert symbol in [row["symbol"] for row in payload["rows"]]


def test_search_instruments_errors_are_returned(server):
    """Test that bad input to search_instruments comes back as text."""
    assert "query is empty" in call_text(
        server.mcp, "search_instruments", {"query": "  "}
    )
    text = call_text(
        server.mcp, "search_instruments", {"query": "x", "asset_classes": "equity"}
    )
    assert "Unknown asset class 'equity'" in text
    assert "Did you mean: equities?" in text


def test_search_categories_lists_every_asset_class(server):
    """Test the markdown overview of asset classes."""
    text = call_text(server.mcp, "search_categories")
    assert text.startswith("| Tool | Asset class | Entries | Filters | Description |")
    for name, cls in ASSET_TOOLS.items():
        assert f"`{name}`" in text
        assert ", ".join(cls.FIELDS) in text
    assert "delisted)" in text


def test_show_options_matches_the_package(server):
    """Test that show_options returns the package's values for a selection."""
    expected = (
        fd.Equities(use_local_location=True)
        .show_options("sector", as_pandas=False)
        .to_list()
    )
    payload = call_json(
        server.mcp, "show_options", {"asset_class": "equities", "selection": "sector"}
    )
    assert payload["values"] == expected
    assert payload["total"] == payload["returned"] == len(expected)


def test_show_options_filters_and_caps(server):
    """Test narrowing by filters, the value cap and the per-field overview."""
    narrowed = call_json(
        server.mcp,
        "show_options",
        {
            "asset_class": "equities",
            "selection": "industry",
            "filters": {"sector": "Health Care"},
        },
    )
    assert "Biotechnology" in narrowed["values"]
    assert "Banks" not in narrowed["values"]

    capped = call_json(
        server.mcp,
        "show_options",
        {"asset_class": "etfs", "selection": "family", "limit": 10},
    )
    assert capped["returned"] == len(capped["values"]) == 10
    assert capped["total"] > 10
    assert "_notes" in capped

    overview = call_json(server.mcp, "show_options", {"asset_class": "funds"})
    assert set(overview["options"]) == set(fd.Funds.FIELDS)
    assert all(len(v["values"]) <= 25 for v in overview["options"].values())


def test_show_options_errors_are_returned(server):
    """Test that a bad selection or filter value comes back with suggestions."""
    text = call_text(
        server.mcp, "show_options", {"asset_class": "equities", "selection": "sectr"}
    )
    assert "The selection variable provided is not valid" in text
    assert "Did you mean: sector?" in text

    text = call_text(
        server.mcp,
        "show_options",
        {"asset_class": "equities", "filters": {"sector": "Helth Care"}},
    )
    assert "Did you mean 'Health Care'" in text

    text = call_text(
        server.mcp,
        "show_options",
        {"asset_class": "equities", "filters": {"sectors": "Energy"}},
    )
    assert "'sectors' is not a filter of equities" in text


def test_responses_are_compact_json(server):
    """Test that payloads carry no insignificant whitespace and use null for gaps."""
    text = call_text(server.mcp, "funds", {"limit": 3})
    assert text == json.dumps(
        json.loads(text), ensure_ascii=False, separators=(",", ":")
    )
