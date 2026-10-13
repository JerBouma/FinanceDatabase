"""US Listing Status Test Module"""

import pandas as pd

from scripts.equities import equities_model, status_model

NASDAQ = b"""Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N
ZXZZT|NASDAQ TEST STOCK|G|Y|N|100|N|N
"""
OTHER = b"""ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
BRK.B|Berkshire Hathaway Inc. Class B|N|BRK.B|N|100|N|BRK.B
ABR$D|Arbor Realty Trust 6.375% Series D Preferred|N|ABRpD|N|100|N|ABR-D
BCO|Brinks Company (The) Common Stock|N|BCO|N|100|N|BCO
PMTV|PennyMac Mortgage Investment Trust 9.00% Senior Notes due 2030|N|PMTV|N|100|N|PMTV
"""


def test_symbols_match_in_every_spelling() -> None:
    """Test that directory and database spellings share one key."""
    assert status_model.convert_symbol("BRK.B") == status_model.convert_symbol("BRK-B")
    assert (
        status_model.convert_symbol("ABR$D")
        == status_model.convert_symbol("ABR^D")
        == status_model.convert_symbol("ABR-PD")
    )
    assert status_model.convert_symbol("X.U") == status_model.convert_symbol("X-UN")
    assert status_model.convert_symbol("X.WS") == status_model.convert_symbol("X-WT")


def test_status_changes_follow_the_directory() -> None:
    """Test delisting what is gone and relisting the same company, never notes."""
    listed = status_model.read_directory(NASDAQ, OTHER)
    assert "ZXZZT" not in listed
    frame = pd.DataFrame(
        {
            "name": [
                "Apple Inc.",
                "Berkshire Hathaway Inc.",
                "Arbor Realty Trust",
                "Talend S.A.",
                "The Brink's Company",
                "PennyMac Mortgage Investment Trust",
            ],
            "delisted": ["False", "False", "False", "False", "True", "True"],
        },
        index=["AAPL", "BRK-B", "ABR^D", "TLND", "BCO", "PMTV"],
    )
    delist, relist = status_model.get_status_changes(frame, listed)
    assert delist == ["TLND"]
    assert relist == ["BCO"]


def test_lines_abroad_of_a_delisted_home_share_are_stale() -> None:
    """Test that a German line of a share delisted at home goes too."""
    equities = pd.DataFrame(
        {
            "exchange": ["NYQ", "NYQ", "GER", "GER", "GER", "NYQ", "GER"],
            "country": [
                "United States",
                "United States",
                "Germany",
                "United States",
                "United States",
                "United States",
                "United States",
            ],
            "isin": ["US1", "US2", "DE1", "US1", "US2", "US3", "US3"],
            "delisted": ["True", "False", "False", "False", "False", "True", "False"],
        },
        index=["EA", "MSFT", "SAP.DE", "ERT.DE", "MSF.DE", "TWTR", "TWR.DE"],
    )
    german = pd.DataFrame(
        {"exchange": "GER", "country": "Germany", "isin": "", "delisted": "False"},
        index=[f"DE{i}.DE" for i in range(5)],
    )
    equities = pd.concat([equities, german])
    equities["isin"] = (
        equities["isin"].str.ljust(12, "0").where(equities["isin"] != "", "")
    )
    assert sorted(status_model.find_stale_lines(equities)) == ["ERT.DE", "TWR.DE"]


def test_us_lines_follow_the_directory_not_the_home_market() -> None:
    """Test that a NASDAQ line stays when the home listing abroad is delisted."""
    equities = pd.DataFrame(
        {
            "exchange": ["VAN", "NMS", "NMS", "NMS", "BER", "BER", "BER"],
            "country": ["Canada", "Canada", "United States", "United States"]
            + ["Canada", "Germany", "Germany"],
            "isin": ["CA0000000001", "CA0000000001", "US0000000001", "US0000000002"]
            + ["CA0000000001", "DE0000000001", "DE0000000002"],
            "delisted": ["True", "False", "False", "False", "False", "False", "False"],
        },
        index=["AZ.V", "AZ", "AAPL", "MSFT", "A23.BE", "SAP.BE", "BAS.BE"],
    )
    assert status_model.find_stale_lines(equities) == ["A23.BE"]


def test_regional_german_lines_follow_xetra_and_frankfurt() -> None:
    """Test that a Berlin line goes when its ticker is delisted on Xetra and Frankfurt."""
    equities = pd.DataFrame(
        {
            "exchange": ["GER", "FRA", "BER", "GER", "BER"],
            "delisted": ["True", "True", "False", "False", "False"],
        },
        index=["GLP.DE", "GLP.F", "GLP.BE", "SAP.DE", "SAP.BE"],
    )
    assert status_model.find_stale_german_lines(equities) == ["GLP.BE"]


def test_reused_tickers_make_way_for_the_new_company() -> None:
    """Test that only a delisted row of another company gives up its ticker."""
    equities = pd.DataFrame(
        {
            "name": ["Barnes Group Inc.", "Barrick Gold Corporation", "Apple Inc."],
            "delisted": ["True", "True", "False"],
        },
        index=["B", "GOLD", "AAPL"],
    )
    feed = pd.DataFrame(
        {
            "name": [
                "Barrick Mining Corporation Common Shares",
                "Barrick Gold Corp",
                "Apple Inc. Common Stock",
            ]
        },
        index=["B", "GOLD", "AAPL"],
    )
    assert equities_model.find_reused_tickers(equities, feed) == ["B"]


def test_new_rows_carry_the_company_name() -> None:
    """Test that the share-type suffix of a feed name is dropped."""
    for feed, name in [
        ("Zevia PBC Class A Common Stock", "Zevia PBC"),
        ("Boyd Group Services Inc. Common Shares", "Boyd Group Services Inc."),
        (
            "Velos Acquisition I Corp. Class A Ordinary shares",
            "Velos Acquisition I Corp.",
        ),
        ("XCHG Limited American Depositary Share", "XCHG Limited"),
        (
            "Haleon plc American Depositary Shares (Each representing two Ordinary Shares)",
            "Haleon plc",
        ),
        ("Star Holdings Shares of Beneficial Interest", "Star Holdings"),
        ("Boeing Company (The)", "The Boeing Company"),
        (
            "Pebblebrook Hotel Trust Preferred Shares of Beneficial Interest",
            "Pebblebrook Hotel Trust Preferred Shares of Beneficial Interest",
        ),
        ("Apple Inc.", "Apple Inc."),
        ("Common Stock", "Common Stock"),
    ]:
        assert equities_model.remove_share_type(feed) == name
