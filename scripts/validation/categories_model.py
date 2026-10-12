"""Categories Model"""

__docformat__ = "google"

import pandas as pd


def find_invalid_categories(equities: pd.DataFrame, tree: dict) -> dict[str, str]:
    """
    The equities whose sector, industry group and industry are not in the category tree.

    Args:
        equities (pd.DataFrame): The equities as text, by symbol.
        tree (dict): Sector -> industry group -> industries, as in scripts/categories.json.

    Returns:
        dict[str, str]: Symbol -> the level that is not found.
    """
    complete = equities[
        (equities["sector"] != "")
        & (equities["industry_group"] != "")
        & (equities["industry"] != "")
    ]
    invalid = {}
    for symbol, sector, group, industry in zip(
        complete.index,
        complete["sector"],
        complete["industry_group"],
        complete["industry"],
        strict=True,
    ):
        if sector not in tree:
            invalid[symbol] = f"sector {sector!r}"
        elif group not in tree[sector]:
            invalid[symbol] = f"industry group {group!r}"
        elif industry not in tree[sector][group]:
            invalid[symbol] = f"industry {industry!r}"
    return invalid
