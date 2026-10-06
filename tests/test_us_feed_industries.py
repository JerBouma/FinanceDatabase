"""US Feed Industries Test Module"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_us_feed_industries_map_to_valid_gics_industries() -> None:
    """Test that every feed label maps once to an industry of the GICS tree."""
    mapping = pd.read_csv(
        ROOT / "scripts" / "us_feed_industries.csv", dtype=str, keep_default_na=False
    )
    tree = json.loads(
        (ROOT / "compression" / "categories" / "categories.json").read_text()
    )
    industries = {
        industry
        for groups in tree.values()
        for group in groups.values()
        for industry in group
    }
    assert list(mapping.columns) == ["feed_industry", "industry"]
    assert mapping["feed_industry"].is_unique
    assert (mapping["feed_industry"] != "").all()
    assert set(mapping["industry"]) <= industries
