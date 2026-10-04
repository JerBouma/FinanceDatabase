"""Tests for scripts/update_listings.py (weekly listings update)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_listings.py"
spec = importlib.util.spec_from_file_location("update_listings", SCRIPT)
ul = importlib.util.module_from_spec(spec)
sys.modules["update_listings"] = ul  # dataclasses resolve types via sys.modules
spec.loader.exec_module(ul)

EQ_HEADER = (
    "symbol,name,summary,currency,sector,industry_group,industry,exchange,mic,market,"
    "country,state,city,zipcode,website,market_cap,isin,cusip,figi,composite_figi,"
    "shareclass_figi,delisted\n"
)
ETF_HEADER = "symbol,name,currency,summary,category_group,category,family,exchange,mic,isin,delisted\n"


def eq_row(symbol, name, exchange, mic, market, isin="", delisted="False"):
    return f"{symbol},{name},,CAD,,,,{exchange},{mic},{market},,,,,,,{isin},,,,,{delisted}\n"


def make_db(tmp_path: Path) -> Path:
    """A tiny database: Toronto/Venture equities, one ETF file and an index file."""
    root = tmp_path / "database"
    (root / "equities").mkdir(parents=True)
    (root / "etfs").mkdir()
    (root / "equities" / "TOR.csv").write_text(
        EQ_HEADER
        + eq_row("ABC.TO", "Abc Mining Corp.", "TOR", "XTSE", "TSX Toronto Exchange")
        + eq_row(
            "OLD.TO", "Renamed Holdings Inc.", "TOR", "XTSE", "TSX Toronto Exchange"
        )
    )
    (root / "equities" / "VAN.csv").write_text(
        EQ_HEADER
        + eq_row(
            "HCO.P.V", "Hansco Capital Corp", "VAN", "XTSX", "TSX Venture Exchange"
        )
    )
    (root / "etfs" / "TOR.csv").write_text(
        ETF_HEADER
        + "ZZZ.TO,Existing ETF,CAD,,,,,TOR,XTSE,,False\n"
        + "iii.TO,iShares One ETF,CAD,,,,BlackRock Asset Management,TOR,XTSE,,False\n"
    )
    (root / "indices.csv").write_text("symbol,name\nNEWI.TO,An index that collides\n")
    return root


def tsx_json(companies: list[tuple[str, list[str]]]) -> bytes:
    """TSX directory JSON with enough padding companies to pass the length check."""
    results = [
        {
            "symbol": s[0],
            "name": name,
            "instruments": [{"symbol": x, "name": name} for x in s],
        }
        for name, s in companies
    ]
    results += [
        {
            "symbol": f"PAD{i}",
            "name": f"Padding {i} Inc.",
            "instruments": [{"symbol": f"PAD{i}", "name": "x"}],
        }
        for i in range(1001)
    ]
    return json.dumps({"results": results}).encode()


def test_yahoo_canada_symbols() -> None:
    assert ul.yahoo_canada("BCE.PR.A") == "BCE-PA"
    assert ul.yahoo_canada("TD.PF.A") == "TD-PFA"
    assert ul.yahoo_canada("GASX.WT.A") == "GASX-WTA"
    assert ul.yahoo_canada("AD.UN") == "AD-UN"
    assert ul.yahoo_canada("BN") == "BN"


def test_canada_names_distinguish_classes() -> None:
    assert ul.canada_name("BCE Inc.", "BCE") == "BCE Inc."
    assert (
        ul.canada_name("BCE Inc.", "BCE.PR.A") == "BCE Inc. Preferred Shares (BCE.PR.A)"
    )
    assert (
        ul.canada_name("Algoma Steel", "ASTL.WT") == "Algoma Steel Warrants (ASTL.WT)"
    )
    assert (
        ul.canada_name("Spectre Capital", "SOO.P") == "Spectre Capital"
    )  # CPC: only listing


def test_symbol_key_and_name_normalisation() -> None:
    assert ul.symbol_key("HCO.P.V") == ul.symbol_key("HCO-P.V")
    assert ul.symbol_key("ESGF.TO") == ul.symbol_key(
        "ESG-F.TO"
    )  # names decide, see below
    assert ul.normalise_name("ABC Holdings Limited") == ul.normalise_name("Abc Ltd.")


def test_parse_tsx_skips_debt_and_ambiguous_funds() -> None:
    raw = tsx_json(
        [
            ("Abc Mining Corp.", ["ABC", "ABC.DB.A"]),
            ("Maple ETF", ["MPL", "MPL.U"]),
            ("Maple Income Fund", ["MIF"]),
        ]
    )
    result = ul.parse_tsx(raw, raw)
    tor = {x.symbol: x for x in result.listings if x.file == "TOR"}
    assert "ABC-DBA.TO" not in tor and "MIF.TO" not in tor
    assert tor["MPL.TO"].kind == "etfs" and tor["MPL-U.TO"].currency == "USD"
    assert "ABC-DBA.TO" in result.official["TOR"]  # still counts as listed


def test_parse_nasdaq_trader_only_etfs() -> None:
    nasdaq = "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
    nasdaq += "AAAP|Pacer ETF |G|N|N|100|Y|N\nAAPL|Apple Inc.|Q|N|N|100|N|N\nTEST|Test ETF|G|Y|N|100|Y|N\n"
    nasdaq += "".join(f"X{i}|Pad|Q|N|N|100|N|N\n" for i in range(3001))
    other = "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
    other += "SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY\nABR$D|Arbor Pref|N|ABRpD|N|100|N|ABR-D\n"
    other += "".join(f"Y{i}|Pad|N|Y{i}|N|100|N|Y{i}\n" for i in range(5001))
    result = ul.parse_nasdaq_trader(nasdaq.encode(), other.encode())
    got = {(x.file, x.symbol, x.name) for x in result.listings}
    assert got == {
        ("NGM", "AAAP", "Pacer ETF"),
        ("PCX", "SPY", "SPDR S&P 500 ETF Trust"),
    }


def test_broken_source_is_rejected() -> None:
    try:
        ul.parse_tsx(b'{"results": []}', b'{"results": []}')
    except ValueError:
        return
    raise AssertionError("an empty directory must not be accepted")


def test_apply_source_adds_dedupes_and_delists(tmp_path: Path) -> None:
    root = make_db(tmp_path)
    db = ul.Database(str(root))
    result = ul.SourceResult(
        listings=[
            ul.Listing(
                "equities", "TOR", "ABC.TO", "Abc Mining Corp.", "CAD"
            ),  # exists
            ul.Listing(
                "equities", "TOR", "NEWI.TO", "New Index Name", "CAD"
            ),  # other asset class
            ul.Listing(
                "equities", "VAN", "HCO-P.V", "Hansco Capital Corp.", "CAD"
            ),  # format variant
            ul.Listing(
                "equities", "TOR", "RNH.TO", "Renamed Holdings Inc.", "CAD"
            ),  # ticker change
            ul.Listing("equities", "TOR", "NEW.TO", "Brand New Corp.", "CAD"),
            ul.Listing("etfs", "TOR", "ESG-F.TO", "Other ESG ETF", "CAD"),
        ],
        official={
            "TOR": {"ABC.TO", "RNH.TO", "NEW.TO", "ESG-F.TO"},
            "VAN": {"HCO-P.V"},
        },
    )
    summary = ul.apply_source(db, "test", result, db.etf_families())
    assert {x.symbol for x in summary["added"]} == {"RNH.TO", "NEW.TO", "ESG-F.TO"}
    assert summary["skipped_format"] == ["HCO-P.V (exists as HCO.P.V)"]
    assert summary["delisted"] == [("equities", "TOR", "OLD.TO", "RNH.TO")]
    db.write()

    tor = pd.read_csv(
        root / "equities" / "TOR.csv", index_col=0, dtype=str, keep_default_na=False
    )
    assert list(tor.index) == sorted(tor.index)
    assert tor.loc["OLD.TO", "delisted"] == "True"
    assert tor.loc["NEW.TO", ["exchange", "mic", "market", "delisted"]].tolist() == [
        "TOR",
        "XTSE",
        "TSX Toronto Exchange",
        "False",
    ]
    assert tor.loc["NEW.TO", "sector"] == ""  # unknown stays blank
    van = (root / "equities" / "VAN.csv").read_text()
    assert "HCO-P.V" not in van


def test_too_many_delistings_are_not_applied(tmp_path: Path, monkeypatch) -> None:
    root = make_db(tmp_path)
    db = ul.Database(str(root))
    monkeypatch.setattr(ul, "MAX_DELISTINGS_PER_SOURCE", 0)
    result = ul.SourceResult(
        listings=[
            ul.Listing("equities", "TOR", "RNH.TO", "Renamed Holdings Inc.", "CAD")
        ],
        official={"TOR": {"RNH.TO"}},
    )
    summary = ul.apply_source(db, "test", result, db.etf_families())
    assert summary["delisted"] == [] and len(summary["added"]) == 1


def test_untouched_files_are_not_rewritten(tmp_path: Path) -> None:
    root = make_db(tmp_path)
    before = (root / "etfs" / "TOR.csv").read_bytes()
    db = ul.Database(str(root))
    ul.apply_source(db, "test", ul.SourceResult(), db.etf_families())
    db.write()
    assert (root / "etfs" / "TOR.csv").read_bytes() == before
