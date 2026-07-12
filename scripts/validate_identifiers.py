"""Report and optionally clear invalid security identifiers in source CSVs."""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from stdnum import cusip, figi, isin
from stdnum.exceptions import InvalidChecksum, ValidationError

FIGI_FIELDS = ("figi", "composite_figi", "shareclass_figi")


@dataclass(frozen=True)
class IdentifierIssue:
    """An invalid or inconsistent identifier found in a source CSV row."""

    path: Path
    line_number: int
    symbol: str
    field: str
    value: str
    reason: str
    actionable: bool
    replacement: str | None = None


@dataclass(frozen=True)
class AuditResult:
    """Summary of an identifier audit."""

    issues: tuple[IdentifierIssue, ...]
    files_scanned: int
    identifiers_checked: int
    relationships_checked: int


@dataclass(frozen=True)
class CleanupResult:
    """Counts of deterministic repairs and removals applied to one CSV file."""

    repaired: int = 0
    cleared: int = 0

    @property
    def changed(self) -> int:
        """Return the total number of changed identifier cells."""
        return self.repaired + self.cleared


def _validate_standard_number(
    value: str, validator: Callable[[str], str], format_error: str
) -> str | None:
    """Run a python-stdnum validator and require canonical stored formatting."""
    try:
        canonical = validator(value)
    except InvalidChecksum:
        return "checksum mismatch"
    except ValidationError:
        return format_error
    if canonical != value:
        return format_error
    return None


def validate_isin(value: str) -> str | None:
    """Return an ISO 6166 validation error, or ``None`` when valid."""
    return _validate_standard_number(
        value,
        isin.validate,
        "expected a canonical 12-character ISIN with a numeric check digit",
    )


def validate_cusip(value: str) -> str | None:
    """Return a CUSIP validation error, or ``None`` when valid."""
    return _validate_standard_number(
        value,
        cusip.validate,
        "expected a canonical 9-character CUSIP with a check digit",
    )


def validate_figi(value: str) -> str | None:
    """Return a FIGI validation error, or ``None`` when valid."""
    return _validate_standard_number(
        value,
        figi.validate,
        "expected a canonical 12-character FIGI with a valid prefix",
    )


def validate_isin_cusip_consistency(isin: str, cusip: str) -> str | None:
    """Check whether a valid US/Canadian ISIN embeds the supplied CUSIP."""
    if not isin or not cusip or isin[:2] not in {"US", "CA"}:
        return None
    if validate_isin(isin) is not None or validate_cusip(cusip) is not None:
        return None
    if isin[2:11] != cusip:
        return "ISIN national identifier does not match CUSIP"
    return None


STANDARD_VALIDATORS: dict[str, Callable[[str], str]] = {
    "isin": isin.validate,
    "cusip": cusip.validate,
    **{field: figi.validate for field in FIGI_FIELDS},
}

FIELD_VALIDATORS: dict[str, Callable[[str], str | None]] = {
    "isin": validate_isin,
    "cusip": validate_cusip,
    **{field: validate_figi for field in FIGI_FIELDS},
}


def _canonical_value(field: str, value: str) -> str | None:
    """Return python-stdnum's canonical value when the identifier is valid."""
    try:
        return STANDARD_VALIDATORS[field](value)
    except ValidationError:
        return None


def _repair_cusip_from_isin(cusip_value: str, isin_value: str) -> str | None:
    """Recover spreadsheet-damaged CUSIPs corroborated by a valid ISIN."""
    canonical_isin = _canonical_value("isin", isin_value)
    if canonical_isin is None or canonical_isin[:2] not in {"US", "CA"}:
        return None

    embedded_cusip = canonical_isin[2:11]
    if validate_cusip(embedded_cusip) is not None:
        return None

    numeric_value = cusip_value.removesuffix(".0")
    if numeric_value.isdigit() and numeric_value.lstrip("0") == embedded_cusip.lstrip(
        "0"
    ):
        return embedded_cusip
    return None


def repair_identifier(field: str, value: str, row_values: dict[str, str]) -> str | None:
    """Return a deterministic replacement for an invalid stored identifier."""
    canonical = _canonical_value(field, value)
    if canonical is not None and canonical != value:
        return canonical
    without_decimal_suffix = value.removesuffix(".0")
    if without_decimal_suffix != value:
        canonical = _canonical_value(field, without_decimal_suffix)
        if canonical == without_decimal_suffix:
            return canonical
    if field == "cusip":
        return _repair_cusip_from_isin(value, row_values.get("isin", ""))
    return None


def discover_csv_files(paths: Iterable[Path]) -> list[Path]:
    """Expand files and directories into a stable list of CSV paths."""
    csv_files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            csv_files.update(
                candidate for candidate in path.rglob("*.csv") if candidate.is_file()
            )
        elif path.is_file() and path.suffix.lower() == ".csv":
            csv_files.add(path)
    return sorted(csv_files)


def _column_index(header: list[str], name: str) -> int | None:
    try:
        return header.index(name)
    except ValueError:
        return None


def audit_identifiers(paths: Iterable[Path]) -> AuditResult:
    """Audit populated identifier fields in CSV files below *paths*."""
    issues: list[IdentifierIssue] = []
    files_scanned = 0
    identifiers_checked = 0
    relationships_checked = 0

    for path in discover_csv_files(paths):
        with path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            try:
                header = next(reader)
            except StopIteration:
                continue

            field_indices = {
                field: index
                for field in FIELD_VALIDATORS
                if (index := _column_index(header, field)) is not None
            }
            if not field_indices:
                continue

            files_scanned += 1
            symbol_index = _column_index(header, "symbol")
            next_line_number = reader.line_num + 1
            for row in reader:
                line_number = next_line_number
                next_line_number = reader.line_num + 1
                symbol = (
                    row[symbol_index]
                    if symbol_index is not None and symbol_index < len(row)
                    else ""
                )

                values = {
                    field: row[index]
                    for field, index in field_indices.items()
                    if index < len(row) and row[index]
                }
                for field, value in values.items():
                    identifiers_checked += 1
                    error = FIELD_VALIDATORS[field](value)
                    if error is not None:
                        replacement = repair_identifier(field, value, values)
                        issues.append(
                            IdentifierIssue(
                                path,
                                line_number,
                                symbol,
                                field,
                                value,
                                error,
                                field != "cusip" or replacement is not None,
                                replacement,
                            )
                        )

                isin = values.get("isin", "")
                cusip = values.get("cusip", "")
                if (
                    isin[:2] in {"US", "CA"}
                    and validate_isin(isin) is None
                    and validate_cusip(cusip) is None
                ):
                    relationships_checked += 1
                    error = validate_isin_cusip_consistency(isin, cusip)
                    if error is not None:
                        issues.append(
                            IdentifierIssue(
                                path,
                                line_number,
                                symbol,
                                "isin/cusip",
                                f"{isin} != {cusip}",
                                error,
                                False,
                            )
                        )

    return AuditResult(
        tuple(issues), files_scanned, identifiers_checked, relationships_checked
    )


def _replace_csv_field(record: str, field_index: int, replacement: str) -> str:
    """Replace one field without reserializing any other part of a CSV record."""
    content_end = len(record.rstrip("\r\n"))
    field_spans: list[tuple[int, int]] = []
    field_start = 0
    in_quotes = False
    position = 0
    while position < content_end:
        character = record[position]
        if character == '"':
            if in_quotes and position + 1 < content_end and record[position + 1] == '"':
                position += 2
                continue
            in_quotes = not in_quotes
        elif character == "," and not in_quotes:
            field_spans.append((field_start, position))
            field_start = position + 1
        position += 1
    field_spans.append((field_start, content_end))

    if in_quotes or field_index >= len(field_spans):
        raise ValueError("cannot safely locate identifier field in CSV record")
    start, end = field_spans[field_index]
    return f"{record[:start]}{replacement}{record[end:]}"


def apply_identifier_cleanup(path: Path) -> CleanupResult:
    """Repair or clear invalid cells while preserving all other CSV content."""
    with path.open(encoding="utf-8", newline="") as csv_file:
        lines = csv_file.readlines()

    reader = csv.reader(lines)
    try:
        header = next(reader)
    except StopIteration:
        return CleanupResult()

    field_indices = {
        field: index
        for field in FIELD_VALIDATORS
        if (index := _column_index(header, field)) is not None
    }
    if not field_indices:
        return CleanupResult()

    output_records = ["".join(lines[: reader.line_num])]
    previous_line = reader.line_num
    repaired = 0
    cleared = 0
    for row in reader:
        current_line = reader.line_num
        record = "".join(lines[previous_line:current_line])
        previous_line = current_line
        values = {
            field: row[index]
            for field, index in field_indices.items()
            if index < len(row) and row[index]
        }
        replacements: list[tuple[int, str]] = []
        for field, value in values.items():
            if FIELD_VALIDATORS[field](value) is None:
                continue
            replacement = repair_identifier(field, value, values)
            if field != "cusip" or replacement is not None:
                replacements.append((field_indices[field], replacement or ""))
        for index, replacement in sorted(replacements, reverse=True):
            record = _replace_csv_field(record, index, replacement)
            repaired += bool(replacement)
            cleared += not replacement
        output_records.append(record)

    if not repaired and not cleared:
        return CleanupResult()

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_file.writelines(output_records)
            temporary_path = Path(temporary_file.name)
        temporary_path.chmod(path.stat().st_mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return CleanupResult(repaired, cleared)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Validate ISIN, CUSIP, and FIGI fields in source CSV files.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("database")],
        help="CSV files or directories to scan (default: database)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Repair deterministic damage and clear other invalid identifiers",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the identifier audit command."""
    arguments = build_parser().parse_args(argv)
    if not discover_csv_files(arguments.paths):
        print("No CSV files found.")
        return 2

    result = audit_identifiers(arguments.paths)
    for issue in result.issues:
        symbol = f" ({issue.symbol})" if issue.symbol else ""
        replacement = f"; repair as {issue.replacement!r}" if issue.replacement else ""
        print(
            f"{issue.path}:{issue.line_number}{symbol}: {issue.field} "
            f"{issue.value!r}: {issue.reason}{replacement}"
        )

    actionable = [issue for issue in result.issues if issue.actionable]
    repairable = [issue for issue in actionable if issue.replacement]
    removable = [issue for issue in actionable if not issue.replacement]
    review_only = [
        issue
        for issue in result.issues
        if not issue.actionable and issue.field != "isin/cusip"
    ]
    consistency = [issue for issue in result.issues if issue.field == "isin/cusip"]
    print(
        f"Checked {result.identifiers_checked} populated identifiers and "
        f"{result.relationships_checked} US/Canadian ISIN-CUSIP pairs in "
        f"{result.files_scanned} CSV files; found {len(actionable) + len(review_only)} "
        f"invalid values ({len(repairable)} repairable, {len(removable)} removable, "
        f"{len(review_only)} review-only) and {len(consistency)} consistency issues."
    )
    if not result.issues:
        return 0

    if not arguments.apply:
        print(
            "Dry run: no files changed. Re-run with --apply to repair deterministic "
            "damage and clear other identifiers that fail validation."
        )
        return 1

    affected_paths = sorted({issue.path for issue in actionable})
    cleanup_results = [apply_identifier_cleanup(path) for path in affected_paths]
    repaired = sum(result.repaired for result in cleanup_results)
    cleared = sum(result.cleared for result in cleanup_results)
    print(
        f"Repaired {repaired} and cleared {cleared} invalid identifier values "
        f"in {len(affected_paths)} CSV files."
    )
    if review_only or consistency:
        print(
            f"Left {len(review_only)} invalid CUSIPs and {len(consistency)} ISIN-CUSIP "
            "consistency issues unchanged for manual review."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
