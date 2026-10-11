"""Integrity Model"""

__docformat__ = "google"

import io
from collections import Counter

import pandas as pd

# An asset class may shrink by at most this share in one run (delisted rows are kept).
MAX_ROW_DROP = 0.1


def read_symbols(text: str) -> tuple[str, list[str]]:
    """
    The header and symbols of a database CSV.

    Args:
        text (str): The CSV content.

    Returns:
        tuple[str, list[str]]: The header line and the symbol column.
    """
    header = text.split("\n", 1)[0].strip()
    symbols = pd.read_csv(
        io.StringIO(text), usecols=[0], dtype=str, keep_default_na=False
    ).iloc[:, 0]
    return header, symbols.tolist()


def get_asset_class(path: str) -> str:
    """
    The asset class of a database file: its folder, or its name for single files.

    Args:
        path (str): The path relative to the database folder.

    Returns:
        str: The asset class.
    """
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else parts[0].removesuffix(".csv")


def find_problems(
    current: dict[str, tuple[str, list[str]]],
    reference: dict[str, tuple[str, list[str]]],
) -> list[str]:
    """
    The problems an update introduced compared with the last commit: changed headers,
    empty or duplicate symbols, symbols in two asset classes and shrunken asset classes.

    Args:
        current (dict): Path -> header and symbols now.
        reference (dict): Path -> header and symbols at the last commit.

    Returns:
        list[str]: The new problems, empty when the update is sound.
    """
    problems = []
    for path, (header, _) in current.items():
        if path in reference and reference[path][0] != header:
            problems.append(f"{path}: header changed")
    headers = {get_asset_class(path): header for path, (header, _) in reference.items()}
    for path in current.keys() - reference.keys():
        expected = headers.get(get_asset_class(path))
        if expected and current[path][0] != expected:
            problems.append(f"{path}: new file with other columns than its asset class")
    for path in reference.keys() - current.keys():
        problems.append(f"{path}: file removed")

    def summarise(files: dict) -> tuple[Counter, dict[str, set[str]], Counter]:
        rows: Counter = Counter()
        symbols: dict[str, set[str]] = {}
        duplicates: Counter = Counter()
        for path, (_, column) in files.items():
            asset = get_asset_class(path)
            rows[asset] += len(column)
            seen = symbols.setdefault(asset, set())
            for symbol in column:
                if symbol in seen or symbol == "":
                    duplicates[(asset, symbol)] += 1
                seen.add(symbol)
        return rows, symbols, duplicates

    rows, symbols, duplicates = summarise(current)
    old_rows, old_symbols, old_duplicates = summarise(reference)
    for (asset, symbol), count in duplicates.items():
        if count > old_duplicates.get((asset, symbol), 0):
            problems.append(f"{asset}: symbol {symbol!r} appears more than once")
    for asset, count in old_rows.items():
        if count and rows.get(asset, 0) < (1 - MAX_ROW_DROP) * count:
            problems.append(f"{asset}: {count} rows dropped to {rows.get(asset, 0)}")

    def collisions(classes: dict[str, set[str]]) -> set[tuple[str, str, str]]:
        names = sorted(classes)
        return {
            (a, b, symbol)
            for i, a in enumerate(names)
            for b in names[i + 1 :]
            for symbol in classes[a] & classes[b]
        }

    for a, b, symbol in sorted(collisions(symbols) - collisions(old_symbols)):
        problems.append(f"symbol {symbol!r} is in both {a} and {b}")
    return problems
