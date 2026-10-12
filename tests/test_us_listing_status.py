"""US Listing Status Test Module"""

import pandas as pd

from scripts.equities import status_model

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
