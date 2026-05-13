"""Tests for SEC enrichment parser tooling."""

# ruff: noqa: S101

from pathlib import Path

import pandas as pd

from parsers.sec_enrichment_controller import (
    SourceRecord,
    build_source_index,
    choose_candidate,
    compose_series_class_name,
    enrich_dataset,
    is_us_candidate_row,
)


def test_foreign_suffix_rows_are_not_us_candidates():
    row = pd.Series({"symbol": "ABC.L", "exchange": "LSE", "country": ""})

    assert not is_us_candidate_row(row)


def test_us_exchange_rows_with_missing_fields_are_accepted():
    row = pd.Series(
        {"symbol": "AAPL", "name": "", "currency": "", "exchange": "NMS", "country": ""}
    )
    records = [
        SourceRecord(
            ticker="AAPL",
            name="Apple Inc.",
            source="company_tickers_exchange",
            security_types=frozenset({"equities"}),
            exchange="Nasdaq",
        )
    ]

    decision = choose_candidate(row, records, "equities")

    assert decision.status == "accepted"
    assert decision.proposed_name == "Apple Inc."
    assert decision.proposed_currency == "USD"


def test_existing_identifier_without_sec_identifier_match_requires_review():
    row = pd.Series(
        {
            "symbol": "OLD",
            "name": "",
            "currency": "",
            "exchange": "NMS",
            "isin": "US0000000001",
        }
    )
    records = [
        SourceRecord(
            ticker="OLD",
            name="New Reused Ticker Corp.",
            source="company_tickers_exchange",
            security_types=frozenset({"equities"}),
            exchange="NYSE",
        )
    ]

    decision = choose_candidate(row, records, "equities")

    assert decision.status == "review"
    assert decision.reason == "row_has_identifier_without_sec_identifier_match"


def test_ambiguous_names_require_review():
    row = pd.Series(
        {"symbol": "TEST", "name": "", "currency": "USD", "exchange": "NMS"}
    )
    records = [
        SourceRecord("TEST", "First Company", "source_a", frozenset({"equities"})),
        SourceRecord("TEST", "Second Company", "source_b", frozenset({"equities"})),
    ]

    decision = choose_candidate(row, records, "equities")

    assert decision.status == "review"
    assert decision.reason == "ambiguous_sec_names"


def test_series_class_name_is_combined_for_generic_class_names():
    assert (
        compose_series_class_name(
            "COMMERCE CAPITAL GOVERNMENT MONEY MARKET FUND",
            "ADMINISTRATIVE CLASS SHARES",
        )
        == "Commerce Capital Government Money Market Fund - Administrative Class Shares"
    )


def test_generic_series_name_is_prefixed_with_entity_name():
    assert (
        compose_series_class_name("Money Market Fund", "Class A", "EAGLE CASH TRUST")
        == "Eagle Cash Trust - Money Market Fund - Class A"
    )


def test_more_generic_series_names_are_prefixed_with_sec_entity_name():
    assert (
        compose_series_class_name(
            "Government Portfolio",
            "Institutional",
            "NEUBERGER BERMAN INSTITUTIONAL LIQUIDITY FUNDS",
        )
        == "Neuberger Berman Institutional Liquidity Funds - Government Portfolio - Institutional"
    )
    assert (
        compose_series_class_name(
            "INSTITUTIONAL MONEY MARKET SERIES",
            "Class I",
            "PRUDENTIAL INSTITUTIONAL LIQUIDITY PORTFOLIO INC",
        )
        == "Prudential Institutional Liquidity Portfolio Inc - Institutional Money Market Series - Class I"
    )
    assert (
        compose_series_class_name(
            "Connecticut Municipal Money-Market Fund",
            "Connecticut Municipal Money-Market Fund Class R",
            "RESERVE MUNICIPAL MONEY-MARKET TRUST II",
        )
        == "Reserve Municipal Money-Market Trust Ii - Connecticut Municipal Money-Market Fund - Class R"
    )


def test_generic_fund_class_name_can_be_upgraded():
    row = pd.Series(
        {
            "symbol": "CADXX",
            "name": "ADMINISTRATIVE CLASS SHARES",
            "currency": "USD",
            "exchange": "NAS",
        }
    )
    records = [
        SourceRecord(
            "CADXX",
            "Commerce Capital Government Money Market Fund - Administrative Class Shares",
            "investment_company_series_class_2011",
            frozenset({"moneymarkets"}),
            series_id="S000005806",
            class_id="C000015942",
            identifiers=frozenset({"S000005806", "C000015942"}),
        )
    ]

    decision = choose_candidate(row, records, "moneymarkets")

    assert decision.status == "accepted"
    assert (
        decision.proposed_name
        == "Commerce Capital Government Money Market Fund - Administrative Class Shares"
    )
    assert decision.proposed_currency == ""
    assert decision.reason == "incomplete_name_sec_series_class_match"


def test_fund_name_suffix_can_be_upgraded_with_entity_context():
    row = pd.Series(
        {
            "symbol": "LBBXX",
            "name": "Money Market Portfolio - Institutional",
            "currency": "USD",
            "exchange": "NAS",
        }
    )
    records = [
        SourceRecord(
            "LBBXX",
            "Neuberger Berman Institutional Liquidity Funds - Money Market Portfolio - Institutional",
            "investment_company_series_class_2010",
            frozenset({"moneymarkets"}),
            series_id="S000015113",
            class_id="C000041259",
            identifiers=frozenset({"S000015113", "C000041259"}),
        )
    ]

    decision = choose_candidate(row, records, "moneymarkets")

    assert decision.status == "accepted"
    assert (
        decision.proposed_name
        == "Neuberger Berman Institutional Liquidity Funds - Money Market Portfolio - Institutional"
    )
    assert decision.reason == "incomplete_name_sec_series_class_match"


def test_enrich_dataset_apply_preserves_columns_and_updates_only_accepted(tmp_path):
    dataset = tmp_path / "equities.csv"
    pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "name": "",
                "summary": "",
                "currency": "",
                "exchange": "NMS",
                "isin": "",
            },
            {
                "symbol": "OLD",
                "name": "",
                "summary": "",
                "currency": "",
                "exchange": "NMS",
                "isin": "US0000000001",
            },
        ]
    ).to_csv(dataset, index=False)
    source_index = build_source_index(
        [
            SourceRecord(
                "AAPL",
                "Apple Inc.",
                "company_tickers_exchange",
                frozenset({"equities"}),
                exchange="Nasdaq",
            ),
            SourceRecord(
                "OLD",
                "New Reused Ticker Corp.",
                "company_tickers_exchange",
                frozenset({"equities"}),
            ),
        ]
    )

    report = enrich_dataset(Path(dataset), source_index, apply=True)
    updated = pd.read_csv(dataset, dtype=str, keep_default_na=False)

    assert updated.columns.tolist() == [
        "symbol",
        "name",
        "summary",
        "currency",
        "exchange",
        "isin",
    ]
    assert updated.loc[0, "name"] == "Apple Inc."
    assert updated.loc[0, "currency"] == "USD"
    assert updated.loc[1, "name"] == ""
    assert updated.loc[1, "currency"] == ""
    assert [row["status"] for row in report] == ["accepted", "review"]
