"""Listings Tests"""

import json
import sys
from pathlib import Path

import pandas as pd
import requests

from scripts.listings import (
    database_model,
    enrichment_model,
    helpers,
    listings_controller,
    sources_model,
)

EQ_HEADER = (
    "symbol,name,summary,currency,sector,industry_group,industry,exchange,mic,market,"
    "country,state,city,zipcode,website,market_cap,isin,cusip,figi,composite_figi,"
    "shareclass_figi,delisted\n"
)
ETF_HEADER = "symbol,name,currency,summary,category_group,category,family,exchange,mic,isin,delisted\n"


def create_equity_row(symbol, name, exchange, mic, market, isin="", delisted="False"):
    return f"{symbol},{name},,CAD,,,,{exchange},{mic},{market},,,,,,,{isin},,,,,{delisted}\n"


def create_database(tmp_path: Path) -> Path:
    """A tiny database: Toronto/Venture equities, one ETF file and an index file."""
    root = tmp_path / "database"
    (root / "equities").mkdir(parents=True)
    (root / "etfs").mkdir()
    (root / "equities" / "TOR.csv").write_text(
        EQ_HEADER
        + create_equity_row(
            "ABC.TO", "Abc Mining Corp.", "TOR", "XTSE", "Toronto Stock Exchange"
        )
        + create_equity_row(
            "OLD.TO", "Renamed Holdings Inc.", "TOR", "XTSE", "Toronto Stock Exchange"
        )
    )
    (root / "equities" / "VAN.csv").write_text(
        EQ_HEADER
        + create_equity_row(
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


def create_tsx_json(companies: list[tuple[str, list[str]]]) -> bytes:
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
    """Test that Canadian symbols are converted to Yahoo Finance symbols."""
    assert helpers.convert_to_yahoo_canada("BCE.PR.A") == "BCE-PA"
    assert helpers.convert_to_yahoo_canada("TD.PF.A") == "TD-PFA"
    assert helpers.convert_to_yahoo_canada("GASX.WT.A") == "GASX-WTA"
    assert helpers.convert_to_yahoo_canada("AD.UN") == "AD-UN"
    assert helpers.convert_to_yahoo_canada("BN") == "BN"


def test_canada_names_distinguish_classes() -> None:
    """Test that Canadian names distinguish share classes."""
    assert helpers.get_canada_name("BCE Inc.", "BCE") == "BCE Inc."
    assert (
        helpers.get_canada_name("BCE Inc.", "BCE.PR.A")
        == "BCE Inc. Preferred Shares (BCE.PR.A)"
    )
    assert (
        helpers.get_canada_name("Algoma Steel", "ASTL.WT")
        == "Algoma Steel Warrants (ASTL.WT)"
    )
    assert (
        helpers.get_canada_name("Spectre Capital", "SOO.P") == "Spectre Capital"
    )  # CPC: only listing


def test_symbol_key_and_name_normalisation() -> None:
    """Test that symbol keys and names are normalised."""
    assert helpers.get_symbol_key("HCO.P.V") == helpers.get_symbol_key("HCO-P.V")
    assert helpers.get_symbol_key("ESGF.TO") == helpers.get_symbol_key(
        "ESG-F.TO"
    )  # names decide, see below
    assert helpers.normalize_name("ABC Holdings Limited") == helpers.normalize_name(
        "Abc Ltd."
    )


def test_dated_name_skips_debt_but_keeps_shares() -> None:
    """Test that notes and debentures are skipped while shares and preferreds are kept."""
    for debt in [
        "Brookfield Finance Inc. 4.50% Perpetual Subordinated Notes",
        "Dime Commercial Bancshares Inc. 9.000% Junior Subordinated Notes",
        "DTE Energy Company 2021 Series E 4.375% Junior Subordinated Debentures",
        "BRC Group Holdings Inc. 5% Sr. Notes due 2026",
        "Corts Trust for BellSouth Debentures",
        "Sify Technologies Limited Rights expiring 6/21/2024",
        "ContraVir Pharmaceuticals, Inc. Warrants expiration 07/03/2023",
    ]:
        assert helpers.DATED_NAME.search(debt), debt
    for share in [
        "Apple Inc. Common Stock",
        "KeyCorp Depositary Shares each representing a 1/40th ownership interest",
        "Soluna Holdings Inc 9.0% Series A Cumulative Perpetual Preferred Stock",
        "Senior Connect Acquisition Corp. I Class A Ordinary Shares",
    ]:
        assert not helpers.DATED_NAME.search(share), share


def test_parse_tsx_skips_debt_and_ambiguous_funds() -> None:
    """Test that the TSX parser skips debt and ambiguous funds."""
    raw = create_tsx_json(
        [
            ("Abc Mining Corp.", ["ABC", "ABC.DB.A"]),
            ("Maple ETF", ["MPL", "MPL.U"]),
            ("Maple Income Fund", ["MIF"]),
        ]
    )
    result = sources_model.parse_tsx(raw, raw)
    tor = {x.symbol: x for x in result.listings if x.file == "TOR"}
    assert "ABC-DBA.TO" not in tor and "MIF.TO" not in tor
    assert tor["MPL.TO"].kind == "etfs" and tor["MPL-U.TO"].currency == "USD"
    assert "ABC-DBA.TO" in result.official["TOR"]  # still counts as listed


def test_parse_nasdaq_trader_only_etfs() -> None:
    """Test that the Nasdaq Trader parser only returns ETFs."""
    nasdaq = "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
    nasdaq += "AAAP|Pacer ETF |G|N|N|100|Y|N\nAAPL|Apple Inc.|Q|N|N|100|N|N\nTEST|Test ETF|G|Y|N|100|Y|N\n"
    nasdaq += "".join(f"X{i}|Pad|Q|N|N|100|N|N\n" for i in range(3001))
    other = "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
    other += "SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY\nABR$D|Arbor Pref|N|ABRpD|N|100|N|ABR-D\n"
    other += "".join(f"Y{i}|Pad|N|Y{i}|N|100|N|Y{i}\n" for i in range(5001))
    result = sources_model.parse_nasdaq_trader(nasdaq.encode(), other.encode())
    got = {(x.file, x.symbol, x.name) for x in result.listings}
    assert got == {
        ("NGM", "AAAP", "Pacer ETF"),
        ("PCX", "SPY", "SPDR S&P 500 ETF Trust"),
    }


def test_broken_source_is_rejected() -> None:
    """Test that a broken source is rejected."""
    try:
        sources_model.parse_tsx(b'{"results": []}', b'{"results": []}')
    except ValueError:
        return
    raise AssertionError("an empty directory must not be accepted")


def test_apply_source_adds_dedupes_and_delists(tmp_path: Path) -> None:
    """Test that applying a source adds, deduplicates and delists rows."""
    root = create_database(tmp_path)
    db = database_model.Database(str(root))
    result = sources_model.SourceResult(
        listings=[
            sources_model.Listing(
                "equities", "TOR", "ABC.TO", "Abc Mining Corp.", "CAD"
            ),  # exists
            sources_model.Listing(
                "equities", "TOR", "NEWI.TO", "New Index Name", "CAD"
            ),  # other asset class
            sources_model.Listing(
                "equities", "VAN", "HCO-P.V", "Hansco Capital Corp.", "CAD"
            ),  # format variant
            sources_model.Listing(
                "equities", "TOR", "RNH.TO", "Renamed Holdings Inc.", "CAD"
            ),  # ticker change
            sources_model.Listing(
                "equities", "TOR", "NEW.TO", "Brand New Corp.", "CAD"
            ),
            sources_model.Listing("etfs", "TOR", "ESG-F.TO", "Other ESG ETF", "CAD"),
        ],
        official={
            "TOR": {"ABC.TO", "RNH.TO", "NEW.TO", "ESG-F.TO"},
            "VAN": {"HCO-P.V"},
        },
    )
    summary = listings_controller.apply_source(
        db, "test", result, db.get_etf_families(), use_openfigi=False
    )
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
        "Toronto Stock Exchange",
        "False",
    ]
    assert tor.loc["NEW.TO", "sector"] == ""  # unknown stays blank
    van = (root / "equities" / "VAN.csv").read_text()
    assert "HCO-P.V" not in van


def test_too_many_delistings_are_not_applied(tmp_path: Path, monkeypatch) -> None:
    """Test that too many delistings are not applied."""
    root = create_database(tmp_path)
    db = database_model.Database(str(root))
    monkeypatch.setattr(listings_controller, "MAX_DELISTINGS_PER_SOURCE", 0)
    result = sources_model.SourceResult(
        listings=[
            sources_model.Listing(
                "equities", "TOR", "RNH.TO", "Renamed Holdings Inc.", "CAD"
            )
        ],
        official={"TOR": {"RNH.TO"}},
    )
    summary = listings_controller.apply_source(
        db, "test", result, db.get_etf_families(), use_openfigi=False
    )
    assert summary["delisted"] == [] and len(summary["added"]) == 1


def test_untouched_files_are_not_rewritten(tmp_path: Path) -> None:
    """Test that untouched files are not rewritten."""
    root = create_database(tmp_path)
    before = (root / "etfs" / "TOR.csv").read_bytes()
    db = database_model.Database(str(root))
    listings_controller.apply_source(
        db,
        "test",
        sources_model.SourceResult(),
        db.get_etf_families(),
        use_openfigi=False,
    )
    db.write()
    assert (root / "etfs" / "TOR.csv").read_bytes() == before


def test_learn_categories_requires_agreement() -> None:
    """Test that learned categories require agreement."""
    rows = {f"B{i}.T": ("Financials", "Banks", "Banks") for i in range(10)}
    rows |= {
        f"S{i}.T": ("Industrials" if i % 2 else "Consumer Discretionary", "", "")
        for i in range(12)
    }
    frame = pd.DataFrame.from_dict(
        rows, orient="index", columns=["sector", "industry_group", "industry"]
    )
    labels = {s: ("Banks" if s.startswith("B") else "Services") for s in rows}
    mapping = enrichment_model.learn_categories(frame, labels)
    assert mapping == {
        "Banks": {
            "sector": "Financials",
            "industry_group": "Banks",
            "industry": "Banks",
        }
    }


def test_figi_jobs_and_names() -> None:
    """Test that OpenFIGI jobs and names are built correctly."""
    hk = sources_model.Listing(
        "etfs", "HKG", "2801.HK", "ISHARES CHINA", "HKD", isin="HK2801040828"
    )
    assert enrichment_model.create_figi_job(hk) == (
        {"idType": "ID_ISIN", "idValue": "HK2801040828", "exchCode": "HK"},
        "2801",
    )
    assert (
        enrichment_model.create_figi_job(
            sources_model.Listing("equities", "HKG", "0001.HK", "CKH", "HKD")
        )[0]["idValue"]
        == "1"
    )
    assert (
        enrichment_model.create_figi_job(
            sources_model.Listing("equities", "TOR", "AD-UN.TO", "Alaris", "CAD")
        )[0]["idValue"]
        == "AD-U"
    )
    assert (
        enrichment_model.create_figi_job(
            sources_model.Listing("equities", "TOR", "BCE-PA.TO", "BCE", "CAD")
        )
        is None
    )
    assert (
        enrichment_model.create_figi_job(
            sources_model.Listing("etfs", "PCX", "SPY", "SPDR", "USD")
        )
        is None
    )
    assert (
        enrichment_model.get_openfigi_name({"name": "ISHARES CORE MSCI CHINA -HKD"})
        == "ISHARES CORE MSCI CHINA"
    )
    assert (
        enrichment_model.get_openfigi_name({"name": "CK HUTCHISON HOLDINGS LTD"})
        == "CK HUTCHISON HOLDINGS LTD"
    )
    assert (
        enrichment_model.get_openfigi_name({"name": "KING INTERNATIONAL INVESTMEN"})
        == ""
    )  # truncated


def test_openfigi_enrichment_fills_and_refiles(monkeypatch) -> None:
    """Test that the OpenFIGI enrichment fills fields and refiles rows."""
    listings = [
        sources_model.Listing("equities", "HKG", "0001.HK", "CKH HOLDINGS", "HKD"),
        sources_model.Listing("equities", "HKG", "2800.HK", "TRACKER FUND", "HKD"),
        sources_model.Listing("equities", "JPX", "9999.T", "Unknown Co.", "JPY"),
    ]
    records = [
        {
            "name": "CK HUTCHISON HOLDINGS LTD",
            "securityType": "Common Stock",
            "figi": "F1",
            "compositeFIGI": "C1",
            "shareClassFIGI": "S1",
        },
        {"name": "TRACKER FUND OF HONG KONG", "securityType": "ETP"},
        None,
    ]
    monkeypatch.setattr(
        enrichment_model, "lookup_openfigi", lambda jobs, key: records[: len(jobs)]
    )
    kept, notes = enrichment_model.enrich_with_openfigi(listings, None)
    assert [x.symbol for x in kept] == ["0001.HK", "2800.HK", "9999.T"]
    assert kept[0].name == "CK HUTCHISON HOLDINGS LTD"
    assert (kept[0].figi, kept[0].composite_figi, kept[0].shareclass_figi) == (
        "F1",
        "C1",
        "S1",
    )
    assert kept[1].kind == "etfs" and kept[1].figi == ""  # a fund listed as an equity
    assert kept[2].figi == "" and notes == ["2800.HK filed as ETF (OpenFIGI type ETP)"]


def test_etf_family_matches_upper_case_names(tmp_path: Path) -> None:
    """Test that an ETF family matches upper case names."""
    root = create_database(tmp_path)
    rows = "".join(
        f"I{i}.TO,iShares Fund {i} ETF,CAD,,,,BlackRock Asset Management,TOR,XTSE,,False\n"
        for i in range(12)
    )
    with open(root / "etfs" / "TOR.csv", "a") as handle:
        handle.write(rows)
    family = database_model.Database(str(root)).get_etf_families()
    assert family("ISHARES CHINA") == "BlackRock Asset Management"
    assert family("Unknown Issuer ETF") == ""


def test_blocked_or_broken_source_is_skipped_and_others_continue(
    tmp_path: Path, monkeypatch
) -> None:
    """A bot-check page, an HTTP error or a crash mid-source never stops the run."""
    root = create_database(tmp_path)
    block_page = (
        b'<html><head><script src="/_Incapsula_Resource"></script></head></html>'
    )
    crashing = {"on": False}
    real_get_defaults = database_model.Database.get_defaults

    def get_crashing_defaults(self, kind, file):
        if crashing["on"]:
            raise RuntimeError("unexpected data")
        return real_get_defaults(self, kind, file)

    monkeypatch.setattr(database_model.Database, "get_defaults", get_crashing_defaults)

    def load_blocked_source():
        return sources_model.parse_tsx(block_page, block_page)

    def load_http_error_source():
        raise requests.HTTPError("403 Forbidden")

    def load_crashing_source():
        # OLD.TO is delisted as superseded by RNH.TO, then adding RNH.TO crashes.
        crashing["on"] = True
        listing = sources_model.Listing(
            "equities", "TOR", "RNH.TO", "Renamed Holdings Inc.", "CAD"
        )
        return sources_model.SourceResult(
            listings=[listing], official={"TOR": {"RNH.TO"}}
        )

    def load_good_source():
        listing = sources_model.Listing(
            "equities", "TOR", "NEW.TO", "Brand New Corp.", "CAD"
        )
        return sources_model.SourceResult(
            listings=[listing], official={"TOR": {"NEW.TO", "ABC.TO", "OLD.TO"}}
        )

    # TOR.csv is loaded by "good" first, so "crash" exercises the in-memory rollback;
    # "crash_first" (fresh database) exercises dropping a file first loaded by the failed source.
    sources = {
        "good": load_good_source,
        "blocked": load_blocked_source,
        "http": load_http_error_source,
        "crash": load_crashing_source,
    }
    failures = listings_controller.run(str(root), sources=sources, use_openfigi=False)
    assert failures == ["blocked", "http", "crash"]
    second = create_database(tmp_path / "second")
    assert listings_controller.run(
        str(second),
        sources={"crash_first": load_crashing_source},
        use_openfigi=False,
    ) == ["crash_first"]
    crashing["on"] = False
    assert (
        pd.read_csv(second / "equities" / "TOR.csv", index_col=0, dtype=str).loc[
            "OLD.TO", "delisted"
        ]
        == "False"
    )
    tor = pd.read_csv(
        root / "equities" / "TOR.csv", index_col=0, dtype=str, keep_default_na=False
    )
    assert "NEW.TO" in tor.index and "RNH.TO" not in tor.index
    assert (
        tor.loc["OLD.TO", "delisted"] == "False"
    )  # the crashed source was rolled back


def test_main_never_raises(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that main reports a failure instead of raising."""
    monkeypatch.setattr(sys, "argv", ["update_listings", "--database", str(tmp_path)])
    listings_controller.main()  # an empty directory is not a database: reported, not raised
    assert "Listings update skipped entirely" in capsys.readouterr().out


def test_factual_summary_states_only_known_fields() -> None:
    """Test that the factual summary states only known fields."""
    row = {
        "name": "Abc Mining Corp.",
        "exchange": "TOR",
        "currency": "CAD",
        "sector": "",
        "country": "",
    }
    assert enrichment_model.create_factual_summary("ABC.TO", row, "equities") == (
        "Abc Mining Corp. is a company listed on the Toronto Stock Exchange under the ticker ABC "
        "and traded in CAD."
    )
    etf = {
        "name": "ISHARES CORE MSCI CHINA",
        "exchange": "HKG",
        "currency": "HKD",
        "family": "BlackRock Asset Management",
        "category_group": "Equities",
        "category": "Emerging Markets",
    }
    text = enrichment_model.create_factual_summary("2801.HK", etf, "etfs")
    assert (
        "exchange-traded fund listed on the Hong Kong Stock Exchange under the ticker 2801"
        in text
    )
    assert (
        "BlackRock Asset Management" in text and "Equities (Emerging Markets)" in text
    )
    assert (
        enrichment_model.create_factual_summary(
            "X.TO", {"name": "", "exchange": "TOR"}, "equities"
        )
        == ""
    )


def test_extract_objective_from_summary_prospectus() -> None:
    """Test that the objective is extracted from a summary prospectus."""
    page = (
        "<html><p>Summary Prospectus</p><h2>Investment Objective</h2><p>The Sequoia Global "
        "Value ETF (the &#8220; Fund &#8221;) seeks to achieve long term capital appreciation .</p>"
        "<h2>Fees and Expenses of the Fund</h2></html>"
    )
    assert enrichment_model.extract_objective(page) == (
        "The Sequoia Global Value ETF (the “Fund”) seeks to achieve long term capital appreciation."
    )
    assert (
        enrichment_model.extract_objective(
            "<p>Investment Objective</p><p>Some unrelated text here.</p>"
        )
        == ""
    )


def test_sec_disabled_without_contact() -> None:
    """Test that SEC lookups are disabled without a contact email."""
    sec = enrichment_model.SecFunds(None)
    assert sec.get_objective("SPY") == "" and sec.get_registrant("SPY") == ""


def test_us_etfs_get_sec_objective_and_registrant_family(tmp_path: Path) -> None:
    """Test that US ETFs get the SEC objective and the registrant family."""
    root = create_database(tmp_path)
    rows = "".join(
        f"T{i},Trust Fund {i} ETF,USD,,,,Acme Funds,PCX,ARCX,,False\n" for i in range(6)
    )
    (root / "etfs" / "PCX.csv").write_text(ETF_HEADER + rows)
    db = database_model.Database(str(root))

    class FakeSec(enrichment_model.SecFunds):
        def __init__(self) -> None:
            self.headers = {"User-Agent": "test"}
            self.funds = {f"T{i}": [111, "S1", "C1", f"T{i}"] for i in range(6)}
            self.funds |= {
                "NEWF": [111, "S2", "C2", "NEWF"],
                "OTHR": [222, "S3", "C3", "OTHR"],
            }

        def get_objective(self, symbol: str) -> str:
            return "The Fund seeks income." if symbol == "NEWF" else ""

    result = sources_model.SourceResult(
        listings=[
            sources_model.Listing("etfs", "PCX", "NEWF", "Brand New ETF", "USD"),
            sources_model.Listing("etfs", "PCX", "OTHR", "Other Issuer ETF", "USD"),
        ],
        official={"PCX": {"NEWF", "OTHR"}},
    )
    listings_controller.apply_source(
        db, "test", result, db.get_etf_families(), use_openfigi=False, sec=FakeSec()
    )
    db.write()
    pcx = pd.read_csv(
        root / "etfs" / "PCX.csv", index_col=0, dtype=str, keep_default_na=False
    )
    assert pcx.loc["NEWF", "summary"] == (
        "The Fund seeks income. Brand New ETF is an exchange-traded fund listed on the NYSE Arca"
        " under the ticker NEWF and traded in USD. The fund is part of the Acme Funds range."
    )  # short objective: the factual sentence follows it
    assert (
        pcx.loc["NEWF", "family"] == "Acme Funds"
    )  # registrant 111: 6/6 existing ETFs agree
    assert pcx.loc["OTHR", "family"] == ""  # unknown registrant: left blank
    assert pcx.loc["OTHR", "summary"].startswith(
        "Other Issuer ETF is an exchange-traded fund listed on the NYSE Arca"
    )


def test_extract_objective_keeps_before_fees_and_skips_website_sentence() -> None:
    """Test that the objective keeps 'before fees' and skips the website sentence."""
    leveraged = (
        "<p>Investment Objective</p><p>The Fund seeks daily investment results, before fees and"
        " expenses, of 200% of the daily performance of SMCI.</p><h2>Fees and Expenses of the"
        " Fund</h2>"
    )
    assert enrichment_model.extract_objective(leveraged) == (
        "The Fund seeks daily investment results, before fees and expenses, of 200% of the daily"
        " performance of SMCI."
    )
    buffer = (
        "<p>Investment Objective</p><p>The Fund&#8217;s website, www.example.com/APRT, provides,"
        " on a daily basis, important Fund information (including Outcome Period dates). The Fund"
        " seeks to match the S&amp;P 500 up to a cap.</p><p>Fees and Expenses</p>"
    )
    assert (
        enrichment_model.extract_objective(buffer)
        == "The Fund seeks to match the S&P 500 up to a cap."
    )


def test_sec_objective_skips_supplements() -> None:
    """Test that the SEC objective skips supplements."""
    pages = {
        "atom": "<filing-href>https://sec/f1-index.htm</filing-href>"
        "<filing-href>https://sec/f2-index.htm</filing-href>",
        "https://sec/f1-index.htm": 'href="/Archives/edgar/data/1/supp.htm"',
        "https://sec/f2-index.htm": 'href="/Archives/edgar/data/1/sp.htm"',
        "https://www.sec.gov/Archives/edgar/data/1/supp.htm": "<p>This supplement does not change"
        " the Fund's investment objective or principal investment strategies.</p>",
        "https://www.sec.gov/Archives/edgar/data/1/sp.htm": "<p>Investment Objective</p><p>The"
        " Fund seeks long-term capital appreciation.</p><p>Fees and Expenses</p>",
    }

    class FakeSec(enrichment_model.SecFunds):
        def __init__(self) -> None:
            self.headers = {"User-Agent": "test"}
            self.funds = {"ABFL": [1, "S1", "C1", "ABFL"]}

        def get(self, url: str) -> str:
            return pages["atom"] if "browse-edgar" in url else pages[url]

    assert (
        FakeSec().get_objective("ABFL")
        == "The Fund seeks long-term capital appreciation."
    )


def test_dated_instruments_are_not_added(tmp_path: Path) -> None:
    """Test that warrants, rights and notes with a maturity date are not added."""
    db = database_model.Database(str(create_database(tmp_path)))
    listings = [
        ("GASX-WTA.TO", "Gasx Corp. Warrants (GASX.WT.A)"),
        ("PUL-RT.TO", "Pulse Oil Corp Rights"),
        ("ABCN.TO", "Abc Mining Corp. 6.00% Notes due 2029"),
        ("MOEX.TO", "Moscow Exchange MICEX-RTS"),
        ("NEW.TO", "Brand New Corp."),
    ]
    result = sources_model.SourceResult(
        listings=[
            sources_model.Listing("equities", "TOR", symbol, name, "CAD")
            for symbol, name in listings
        ],
        official={"TOR": {symbol for symbol, _ in listings} | {"ABC.TO", "OLD.TO"}},
    )
    summary = listings_controller.apply_source(
        db, "TSX", result, lambda name: "", use_openfigi=False
    )
    assert [listing.symbol for listing in summary["added"]] == ["MOEX.TO", "NEW.TO"]
