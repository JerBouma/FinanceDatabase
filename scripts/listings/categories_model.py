"""Categories Model"""

__docformat__ = "google"

import re
from collections import Counter, defaultdict

import pandas as pd

# A name term decides a value when at least this share of the ETFs carrying it agree.
TERM_SHARE = 0.85
# ... and at least this many ETFs carry it.
TERM_MINIMUM = 20
# A term at least this share of whose ETFs share one family names the issuer, not the asset.
ISSUER_SHARE = 0.8
# A category belongs to the group at least this share of its ETFs have.
PAIR_SHARE = 0.9


def get_terms(name: str) -> set[str]:
    """
    The words and word pairs of a name ('Corporate Bond', 'Small-Cap' as 'small cap').

    Args:
        name (str): The name.

    Returns:
        set[str]: The terms, lower case.
    """
    words = re.findall(r"[a-z0-9]+", name.lower().replace("-", " "))
    return set(words) | {f"{a} {b}" for a, b in zip(words, words[1:], strict=False)}


def learn_term_values(etfs: pd.DataFrame, column: str) -> dict[str, tuple]:
    """
    The terms that decide a column's value: most ETFs carrying them share one value, and
    they do not just name an issuer.

    Args:
        etfs (pd.DataFrame): The ETFs with name, family and the column.
        column (str): category_group or category.

    Returns:
        dict[str, tuple]: Term -> value, share and number of ETFs.
    """
    values: dict[str, Counter] = defaultdict(Counter)
    families: dict[str, Counter] = defaultdict(Counter)
    for name, value, family in zip(
        etfs["name"], etfs[column], etfs["family"], strict=True
    ):
        for term in get_terms(name):
            if family:
                families[term][family] += 1
            if value:
                values[term][value] += 1
    rules = {}
    for term, counter in values.items():
        issuers = families[term]
        named = sum(issuers.values())
        if (
            named >= TERM_MINIMUM
            and issuers.most_common(1)[0][1] >= ISSUER_SHARE * named
        ):
            continue
        total = sum(counter.values())
        value, count = counter.most_common(1)[0]
        if total >= TERM_MINIMUM and count >= TERM_SHARE * total:
            rules[term] = (value, count / total, total)
    return rules


def predict_value(name: str, rules: dict[str, tuple]) -> str:
    """
    The value of the most decisive term of a name, empty without one.

    Args:
        name (str): The ETF name.
        rules (dict): See learn_term_values.

    Returns:
        str: The predicted value.
    """
    hits = [rules[term] for term in get_terms(name) if term in rules]
    return max(hits, key=lambda hit: (hit[1], hit[2]))[0] if hits else ""


def get_category_groups(etfs: pd.DataFrame) -> dict[str, str]:
    """
    The group each category belongs to, where the ETFs agree on it.

    Args:
        etfs (pd.DataFrame): The ETFs with category_group and category.

    Returns:
        dict[str, str]: Category -> category group.
    """
    known = etfs[(etfs["category"] != "") & (etfs["category_group"] != "")]
    groups = {}
    for category, group in known.groupby("category")["category_group"]:
        counts = group.value_counts()
        if counts.iloc[0] >= PAIR_SHARE * len(group):
            groups[category] = counts.index[0]
    return groups


def fill_etf_categories(frames: list[pd.DataFrame]) -> int:
    """
    Fill blank ETF categories: from other listings of the same ISIN, else from the most
    decisive term of the name, keeping group and category consistent. Known values are
    never changed.

    Args:
        frames (list[pd.DataFrame]): The ETF files, changed in place.

    Returns:
        int: The number of filled values.
    """
    etfs = pd.concat(
        [
            frame[["name", "isin", "family", "category_group", "category"]]
            for frame in frames
        ]
    )
    known = etfs[(etfs["isin"].str.len() == 12) & (etfs["category"] != "")]
    siblings = (
        known.groupby("isin")[["category_group", "category"]]
        .agg(lambda values: values.mode().iloc[0])
        .to_dict("index")
    )
    category_rules = learn_term_values(etfs, "category")
    group_rules = learn_term_values(etfs, "category_group")
    groups = get_category_groups(etfs)

    filled = 0
    for frame in frames:
        blank = frame.index[(frame["category"] == "") | (frame["category_group"] == "")]
        for symbol in blank:
            name, isin = frame.loc[symbol, "name"], frame.loc[symbol, "isin"]
            group, category = (
                frame.loc[symbol, "category_group"],
                frame.loc[symbol, "category"],
            )
            sibling = siblings.get(isin, {})
            if not category:
                guess = sibling.get("category") or predict_value(name, category_rules)
                fits = groups.get(guess) and group in ("", groups.get(guess))
                category = guess if guess and (sibling or fits) else ""
                if category and not group:
                    group = sibling.get("category_group") or groups[category]
            if not group:
                # A known category gives its group; else the fund's other listings or name.
                group = (
                    groups.get(category, "")
                    or sibling.get("category_group")
                    or predict_value(name, group_rules)
                )
            changes = {
                column: value
                for column, value in (("category_group", group), ("category", category))
                if value and frame.loc[symbol, column] == ""
            }
            if changes:
                frame.loc[symbol, list(changes)] = list(changes.values())
                frame.attrs["changed"] = True
                filled += len(changes)
    return filled
