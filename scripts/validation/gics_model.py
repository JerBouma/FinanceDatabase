"""GICS Model"""

__docformat__ = "google"

import pandas as pd


def find_invalid_gics(equities: pd.DataFrame, gics: dict) -> dict[str, str]:
    """
    The equities whose sector, industry group and industry are not in the GICS tree.

    Args:
        equities (pd.DataFrame): The equities as text, by symbol.
        gics (dict): Sector -> industry group -> industry, as in categories.json.

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
        try:
            gics[sector][group][industry]
        except KeyError as error:
            invalid[symbol] = str(error)
    return invalid
