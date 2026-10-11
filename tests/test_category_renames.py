"""Category Renames Test Module"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_renames_point_into_the_tree() -> None:
    """Test that every rename targets a current group and industry, never an old name."""
    tree = json.loads((ROOT / "scripts" / "categories.json").read_text())
    groups = {
        group: industries
        for sector in tree.values()
        for group, industries in sector.items()
    }
    renames = pd.read_csv(
        ROOT / "scripts" / "category_renames.csv", dtype=str, keep_default_na=False
    )
    old = set(zip(renames["old_industry_group"], renames["old_industry"], strict=True))
    for group, industry in zip(
        renames["industry_group"], renames["industry"], strict=True
    ):
        assert group == "" or group in groups
        assert industry == "" or industry in groups[group]
        assert (group, industry) not in old or group == ""
