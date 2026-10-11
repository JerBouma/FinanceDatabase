"""Coercion Model"""

__docformat__ = "google"

import difflib
import unicodedata
from collections.abc import Iterable
from typing import Any

from financedatabase.listings_model import LETTERS_WITHOUT_ACCENT


def convert_to_boolean(value: Any) -> bool:
    """
    Coerce a value to a boolean, with support for common string representations.

    Args:
        value (Any): Value to coerce, a bool or e.g. "true", "1" or "yes".

    Returns:
        bool: Boolean interpretation of the input.
    """
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def convert_to_int(
    value: Any, default: int, minimum: int, maximum: int | None = None
) -> int:
    """
    Coerce a value to an integer clamped to a range, correcting rather than rejecting.

    Args:
        value (Any): Value to coerce, e.g. 25, "25" or 25.0.
        default (int): Returned when the value is missing or not a number.
        minimum (int): Smallest allowed value.
        maximum (int | None): Largest allowed value, or None for no ceiling.

    Returns:
        int: The clamped integer.
    """
    if value is None or value == "":
        number = default
    else:
        try:
            number = int(float(value))
        except (TypeError, ValueError):
            number = default
    number = max(number, minimum)
    if maximum is not None:
        number = min(number, maximum)
    return number


def fold_accents(text: str) -> str:
    """
    Lower-case a text and drop its accents, so 'Curaçao' and 'curacao' compare equal.

    Args:
        text (str): The text.

    Returns:
        str: The text without accents, lower-cased.
    """
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(
        LETTERS_WITHOUT_ACCENT.get(c, c)
        for c in decomposed
        if not unicodedata.combining(c)
    )


def split_values(value: Any) -> list[str]:
    """
    Turn a filter value into a list of stripped, non-empty strings.

    Args:
        value (Any): None, a (comma-separated) string or an iterable of strings.

    Returns:
        list[str]: The comma-separated parts in order, see ``resolve_values``.
    """
    if value is None:
        return []
    items: Iterable[Any] = [value] if isinstance(value, str) else value
    parts: list[str] = []
    for item in items:
        if item is None:
            continue
        parts.extend(part.strip() for part in str(item).split(","))
    return [part for part in parts if part]


def resolve_values(
    value: Any,
    options_lower: set[str],
    expand_prefix: bool = False,
    synonyms: dict[str, list[str]] | None = None,
) -> tuple[list[str], list[str]]:
    """
    Split a filter value into known options, keeping commas that belong to a value.

    Args:
        value (Any): The raw filter value (string, comma-separated string or list).
        options_lower (set[str]): The valid options, lower-cased.
        expand_prefix (bool): Whether a part may stand for several options.
        synonyms (dict[str, list[str]] | None): Option -> other names for it.

    Returns:
        tuple[list[str], list[str]]: The resolved values and the unmatched parts.
    """
    folded = {fold_accents(option): option for option in options_lower}
    for option, aliases in (synonyms or {}).items():
        if option.lower() in options_lower:
            for alias in aliases:
                folded.setdefault(fold_accents(alias), option.lower())

    def match(candidate: str) -> str | None:
        if candidate.lower() in options_lower:
            return candidate
        return folded.get(fold_accents(candidate))

    if isinstance(value, str) and (whole := match(value.strip())):
        return [whole], []

    parts = split_values(value)
    resolved: list[str] = []
    unknown: list[str] = []
    position = 0
    while position < len(parts):
        for end in range(len(parts), position, -1):
            option = match(", ".join(parts[position:end]))
            if option:
                resolved.append(option)
                position = end
                break
        else:
            prefix = fold_accents(parts[position]) + " "
            starting = sorted(o for f, o in folded.items() if f.startswith(prefix))
            if len(starting) == 1 or (starting and expand_prefix):
                resolved.extend(starting)
            else:
                resolved.append(parts[position])
                unknown.append(parts[position])
            position += 1
    return resolved, unknown


def suggest(value: str, options: Iterable[str], count: int = 5) -> list[str]:
    """
    Suggest valid options for an unknown value: close matches and containing options.

    Args:
        value (str): The unknown value.
        options (Iterable[str]): The valid options in their original case.
        count (int): Maximum number of suggestions.

    Returns:
        list[str]: Up to ``count`` suggestions in their original case.
    """
    by_lower = {option.lower(): option for option in options}
    needle = value.strip().lower()
    close = difflib.get_close_matches(needle, list(by_lower), n=count, cutoff=0.6)
    contains = sorted(
        (
            lower
            for lower in by_lower
            if needle and needle in lower and lower not in close
        ),
        key=len,
    )
    return [by_lower[lower] for lower in (close + contains)[:count]]
