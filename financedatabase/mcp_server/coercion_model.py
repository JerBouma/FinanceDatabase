"""
Type coercion and input normalisation utilities for the Finance Database MCP server.

Language models send filter values in many shapes: a single string, a
comma-separated string, a JSON array, or a boolean as the text "true". These
helpers turn that input into what the package expects without raising.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable
from typing import Any


def to_boolean(value: Any) -> bool:
    """
    Coerce a value to a boolean, with support for common string representations.

    Args:
        value (Any): Value to coerce. A bool is returned unchanged; anything else is
            compared case-insensitively against "true", "1" and "yes".

    Returns:
        bool: Boolean interpretation of the input.
    """
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def to_int(value: Any, default: int, minimum: int, maximum: int | None = None) -> int:
    """
    Coerce a value to an integer clamped to a range.

    Out-of-range or unparsable input is corrected rather than rejected, because a
    language model asking for limit=1000 should get the maximum, not an error.

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


def split_values(value: Any) -> list[str]:
    """
    Turn a filter value into a list of stripped, non-empty strings.

    Args:
        value (Any): None, a string (optionally comma-separated) or an iterable of
            strings (each of which may itself be comma-separated).

    Returns:
        list[str]: The individual comma-separated parts, in order. The parts are
            not yet resolved against the valid options; see ``resolve_values``.
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


def resolve_values(value: Any, options_lower: set[str]) -> tuple[list[str], list[str]]:
    """
    Split a filter value into known options, keeping commas that belong to a value.

    Some valid values contain commas themselves ('Hotels, Restaurants & Leisure',
    'AB Fixed-Income Shares, Inc.'), so a plain split would break them. The parts are
    therefore re-joined greedily: at each position the longest run of parts that
    forms a known option (case-insensitive) is taken as one value.

    Args:
        value (Any): The raw filter value (string, comma-separated string or list).
        options_lower (set[str]): The valid options, lower-cased.

    Returns:
        tuple[list[str], list[str]]: The resolved values (as given by the caller) and
            the parts that match no option, which the package will reject.
    """
    if isinstance(value, str) and value.strip().lower() in options_lower:
        return [value.strip()], []

    parts = split_values(value)
    resolved: list[str] = []
    unknown: list[str] = []
    position = 0
    while position < len(parts):
        for end in range(len(parts), position, -1):
            candidate = ", ".join(parts[position:end])
            if candidate.lower() in options_lower:
                resolved.append(candidate)
                position = end
                break
        else:
            resolved.append(parts[position])
            unknown.append(parts[position])
            position += 1
    return resolved, unknown


def suggest(value: str, options: Iterable[str], count: int = 5) -> list[str]:
    """
    Suggest valid options for an unknown value.

    Combines difflib's close matches (typos such as 'Finacials') with options that
    contain the value (partial names such as 'Technology' for
    'Information Technology'), both compared case-insensitively.

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
