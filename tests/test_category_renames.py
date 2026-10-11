"""Category Renames Test Module"""

import json
from pathlib import Path

import pandas as pd

from scripts.equities import categories_model

ROOT = Path(__file__).resolve().parents[1]
RENAMES = categories_model.read_renames(str(ROOT / "scripts" / "category_renames.csv"))


def test_renames_point_into_the_tree() -> None:
    """Test that every rename targets a valid group and industry, and is final."""
    tree = json.loads((ROOT / "scripts" / "categories.json").read_text())
    groups = {
        group: industries
        for sector in tree.values()
        for group, industries in sector.items()
    }
    for group, industry in RENAMES.values():
        assert group == "" or group in groups
        assert industry == "" or industry in groups[group]
        assert (group, industry) not in RENAMES


def test_split_industries_follow_the_text() -> None:
    """Test the rules for the industries that were split."""
    get = categories_model.get_new_categories
    thrift = ("Banks", "Thrifts & Mortgage Finance")
    assert get(*thrift, "Brookline Savings Bank\n", RENAMES) == ("Banking", "Banks")
    assert get(*thrift, "Rocket Companies\nmortgage lender", RENAMES) == (
        "Investing, Lending & Payments",
        "Mortgage Finance",
    )
    reit = ("Real Estate", "Equity Real Estate Investment Trusts (REITs)")
    assert get(*reit, "Prologis\nlogistics warehouses", RENAMES) == (
        "REITs",
        "Industrial REITs",
    )
    assert get("Real Estate", "", "Vonovia\nresidential landlord", RENAMES) == (
        "Real Estate Development & Services",
        "Real Estate Development & Services",
    )
    assert get("Banking", "Banks", "", RENAMES) is None


def test_update_categories_is_idempotent() -> None:
    """Test that a second run changes nothing."""
    frame = pd.DataFrame(
        {
            "name": ["Delta Air Lines", "Visa"],
            "summary": ["", ""],
            "industry_group": ["Transportation", "Diversified Financials"],
            "industry": ["Airlines", "Diversified Financial Services"],
        },
        index=["DAL", "V"],
    )
    assert categories_model.update_categories(frame, RENAMES) == 2
    assert frame.loc["DAL", "industry"] == "Airlines"
    assert frame.loc["V", "industry"] == "Payments & Specialty Finance"
    assert categories_model.update_categories(frame, RENAMES) == 0
