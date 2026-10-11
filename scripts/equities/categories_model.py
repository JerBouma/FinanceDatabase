"""Categories Model"""

__docformat__ = "google"

import re

import pandas as pd

REITS = "REITs"
REAL_ESTATE = "Real Estate Development & Services"
LENDING = "Investing, Lending & Payments"
# The words that name the property type of a REIT.
REIT_TYPES = {
    "Office REITs": r"\boffice",
    "Industrial REITs": r"\bindustrial|\blogistics|\bwarehouse",
    "Residential REITs": r"\bresidential|\bapartment|\bmultifamily|\bsingle-family|"
    r"\bmanufactured hom|\bstudent housing",
    "Retail REITs": r"\bretail|\bshopping|\bmall|\boutlet cent",
    "Health Care REITs": r"\bhealth ?care|\bsenior housing|\bmedical office|"
    r"\bskilled nursing|\bhospitals?\b",
    "Hotel REITs": r"\bhotels?\b|\bresorts?\b|\blodging",
    "Specialty REITs": r"\bdata cent|\bcell towers?|\bcommunications? towers?|"
    r"\bself[- ]storage|\btimber|\bfarmland|\bbillboards?|\boutdoor advertising|"
    r"\bcasinos?\b|\bgaming",
}
REIT_NAME = r"\breits?\b|real estate investment trust"
THRIFT_NAME = r"\bbank|\bbanc|\bsavings|\bthrift|\bbuilding society"


def read_renames(path: str) -> dict[tuple[str, str], tuple[str, str]]:
    """
    The renamed categories: old industry group and industry to the current ones.

    Args:
        path (str): The renames CSV.

    Returns:
        dict: (old group, old industry) -> (group, industry).
    """
    renames = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {
        (row.old_industry_group, row.old_industry): (row.industry_group, row.industry)
        for row in renames.itertuples()
    }


def get_reit_type(text: str) -> str:
    """
    The REIT industry the property types in a text point to: one type gives it,
    several (or 'diversified' without a type) give Diversified REITs.

    Args:
        text (str): Name and summary.

    Returns:
        str: The REIT industry, empty when unknown.
    """
    found = [k for k, pattern in REIT_TYPES.items() if re.search(pattern, text, re.I)]
    if len(found) == 1:
        return found[0]
    if len(found) > 1 or re.search(r"\bdiversified\b", text, re.I):
        return "Diversified REITs"
    return ""


def get_new_categories(
    group: str, industry: str, text: str, renames: dict
) -> tuple[str, str] | None:
    """
    The current industry group and industry of a row, None when unchanged.

    Args:
        group (str): The industry group.
        industry (str): The industry.
        text (str): The name and summary, for the industries that were split.
        renames (dict): See read_renames.

    Returns:
        tuple[str, str] | None: The new group and industry.
    """
    rename = renames.get((group, industry))
    if rename is None:
        return None
    new_group, new_industry = rename
    if new_group == "" and industry:
        # Savings banks stay banks; other mortgage lenders are mortgage finance.
        if re.search(THRIFT_NAME, text.split("\n", 1)[0], re.I):
            return "Banking", "Banks"
        return LENDING, "Mortgage Finance"
    if new_group == "":
        if not re.search(REIT_NAME, text, re.I):
            return REAL_ESTATE, REAL_ESTATE
        return REITS, get_reit_type(text)
    if new_group == REITS and new_industry == "" and industry:
        return REITS, get_reit_type(text)
    return new_group, new_industry


def update_categories(frame: pd.DataFrame, renames: dict) -> int:
    """
    Move the rows of an equities file to the current category names.

    Args:
        frame (pd.DataFrame): The equities file, changed in place.
        renames (dict): See read_renames.

    Returns:
        int: The number of changed rows.
    """
    old = frame["industry_group"].isin({group for group, _ in renames})
    changed = 0
    for symbol in frame.index[old]:
        current = (frame.loc[symbol, "industry_group"], frame.loc[symbol, "industry"])
        text = f"{frame.loc[symbol, 'name']}\n{frame.loc[symbol, 'summary']}"
        new = get_new_categories(*current, text, renames)
        if new and new != current:
            frame.loc[symbol, ["industry_group", "industry"]] = list(new)
            changed += 1
    return changed
