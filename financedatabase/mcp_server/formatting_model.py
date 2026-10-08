"""Formatting Model"""

__docformat__ = "google"

import json
from typing import Any

import polars as pl

ELLIPSIS = "…"


def truncate_text(frame: pl.DataFrame, max_length: int) -> pl.DataFrame:
    """
    Cut every text value longer than ``max_length`` characters.

    Args:
        frame (pl.DataFrame): The frame to shorten.
        max_length (int): Maximum characters per value, including the ellipsis.

    Returns:
        pl.DataFrame: The frame with long text values ending in an ellipsis.
    """
    text_columns = [name for name, dtype in frame.schema.items() if dtype == pl.String]
    if not text_columns or max_length < 1:
        return frame
    return frame.with_columns(
        pl.when(pl.col(name).str.len_chars() > max_length)
        .then(pl.col(name).str.slice(0, max_length - 1) + ELLIPSIS)
        .otherwise(pl.col(name))
        .alias(name)
        for name in text_columns
    )


def convert_to_records(frame: pl.DataFrame) -> list[dict[str, Any]]:
    """
    Convert a frame to a list of JSON-serialisable records.

    ``delisted`` is stored as a Boolean, so it is returned as a real boolean.

    Args:
        frame (pl.DataFrame): The (already bounded) frame.

    Returns:
        list[dict[str, Any]]: One dict per row, with None for missing values.
    """
    return frame.to_dicts()


def convert_to_json(payload: dict[str, Any]) -> str:
    """
    Serialise a payload as compact JSON.

    Args:
        payload (dict[str, Any]): The response payload.

    Returns:
        str: JSON without insignificant whitespace, keeping non-ASCII characters
            readable (company names such as 'Société Générale').
    """
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def format_page(
    frame: pl.DataFrame,
    total: int,
    offset: int,
    limit: int,
    max_text_length: int,
    notes: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    empty_note: str = "No rows match. Check the filter values with show_options.",
) -> str:
    """
    Format one page of results as the standard response payload.

    Args:
        frame (pl.DataFrame): The rows of this page (at most ``limit``).
        total (int): Number of rows matching the request across all pages.
        offset (int): Position of the first row of this page.
        limit (int): Requested page size.
        max_text_length (int): Maximum characters per text value.
        notes (list[str] | None): Hints for the caller, e.g. how to get the next page.
        extra (dict[str, Any] | None): Fields placed before the rows, e.g. the asset class.
        empty_note (str): Hint added when nothing matches.

    Returns:
        str: ``{"total", "returned", "offset", "limit", "columns", "rows", "_notes"}``
            as compact JSON.
    """
    frame = truncate_text(frame.head(limit), max_text_length)
    notes = list(notes or [])
    returned = frame.height
    if offset + returned < total:
        notes.append(
            f"Showing rows {offset + 1}-{offset + returned} of {total}. "
            f"Use offset={offset + returned} to get the next page, or narrow the filters."
        )
    elif total and not returned:
        notes.append(f"offset={offset} is past the last row; there are {total} rows.")
    elif not total:
        notes.append(empty_note)

    payload: dict[str, Any] = dict(extra or {})
    payload.update(
        {
            "total": total,
            "returned": returned,
            "offset": offset,
            "limit": limit,
            "columns": frame.columns,
            "rows": convert_to_records(frame),
        }
    )
    if notes:
        payload["_notes"] = notes
    return convert_to_json(payload)


def format_markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    """
    Render a small Markdown table.

    Args:
        headers (list[str]): Column headers.
        rows (list[list[Any]]): Cell values; pipes are escaped.

    Returns:
        str: The table as Markdown.
    """

    def format_cell(value: Any) -> str:
        return str(value).replace("|", "\\|")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(format_cell(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)
