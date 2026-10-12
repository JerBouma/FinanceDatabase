"""Validation Module"""

__docformat__ = "google"

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd

from scripts.validation import categories_model, integrity_model
from scripts.validation.identifiers_model import (
    FIELD_VALIDATORS,
    AuditResult,
    CleanupResult,
    IdentifierIssue,
    check_isin_precludes_cusip,
    get_cusip_from_authoritative_isin,
    repair_identifier,
    validate_cusip,
    validate_isin,
    validate_isin_cusip_consistency,
)


def discover_csv_files(paths: Iterable[Path]) -> list[Path]:
    """
    Expand files and directories into a stable list of CSV paths.
    """
    csv_files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            csv_files.update(
                candidate for candidate in path.rglob("*.csv") if candidate.is_file()
            )
        elif path.is_file() and path.suffix.lower() == ".csv":
            csv_files.add(path)
    return sorted(csv_files)


def _get_column_index(header: list[str], name: str) -> int | None:
    """
    Get the position of a column in the header, or None if it is missing.
    """
    try:
        return header.index(name)
    except ValueError:
        return None


def audit_identifiers(paths: Iterable[Path]) -> AuditResult:
    """
    Audit populated identifier fields in CSV files below *paths*.
    """
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
                if (index := _get_column_index(header, field)) is not None
            }
            if not field_indices:
                continue

            files_scanned += 1
            symbol_index = _get_column_index(header, "symbol")
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
                        actionable = (
                            field != "cusip"
                            or replacement is not None
                            or check_isin_precludes_cusip(values.get("isin", ""))
                        )
                        issues.append(
                            IdentifierIssue(
                                path,
                                line_number,
                                symbol,
                                field,
                                value,
                                error,
                                actionable,
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
                        replacement = get_cusip_from_authoritative_isin(isin)
                        issues.append(
                            IdentifierIssue(
                                path,
                                line_number,
                                symbol,
                                "isin/cusip",
                                f"{isin} != {cusip}",
                                error,
                                replacement is not None,
                                replacement,
                            )
                        )

    return AuditResult(
        tuple(issues), files_scanned, identifiers_checked, relationships_checked
    )


def _replace_csv_field(record: str, field_index: int, replacement: str) -> str:
    """
    Replace one field without reserializing any other part of a CSV record.
    """
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
    """
    Repair or clear invalid cells while preserving all other CSV content.
    """
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
        if (index := _get_column_index(header, field)) is not None
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
            if (
                field != "cusip"
                or replacement is not None
                or check_isin_precludes_cusip(values.get("isin", ""))
            ):
                replacements.append((field_indices[field], replacement or ""))

        isin_value = values.get("isin", "")
        cusip_value = values.get("cusip", "")
        if (
            "cusip" in field_indices
            and validate_isin_cusip_consistency(isin_value, cusip_value) is not None
        ):
            embedded_cusip = get_cusip_from_authoritative_isin(isin_value)
            if embedded_cusip is not None:
                replacements.append((field_indices["cusip"], embedded_cusip))

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
    """
    Build the command-line argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="validate_identifiers.py",
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
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Write detailed findings to a CSV report instead of standard output",
    )
    return parser


def _format_issue_message(issue: IdentifierIssue) -> str:
    """
    Describe an issue in one line, with the suggested repair if there is one.
    """
    symbol = f" ({issue.symbol})" if issue.symbol else ""
    replacement = f"; repair as {issue.replacement!r}" if issue.replacement else ""
    return f"{issue.field}{symbol} {issue.value!r}: {issue.reason}{replacement}"


def _print_issues(issues: Iterable[IdentifierIssue]) -> None:
    """
    Print every issue with its file and line number.
    """
    for issue in issues:
        print(f"{issue.path}:{issue.line_number}: {_format_issue_message(issue)}")


def _write_report(path: Path, issues: Iterable[IdentifierIssue]) -> None:
    """
    Write detailed identifier findings to a CSV artifact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as report_file:
        writer = csv.writer(report_file)
        writer.writerow(
            [
                "file",
                "line",
                "symbol",
                "field",
                "value",
                "problem",
                "actionable",
                "suggested_replacement",
            ]
        )
        for issue in issues:
            writer.writerow(
                [
                    issue.path.as_posix(),
                    issue.line_number,
                    issue.symbol,
                    issue.field,
                    issue.value,
                    issue.reason,
                    issue.actionable,
                    issue.replacement or "",
                ]
            )


def _print_audit_summary(result: AuditResult) -> None:
    """
    Print how many issues can be repaired, cleared or need a manual review.
    """
    actionable = [issue for issue in result.issues if issue.actionable]
    repairable = [issue for issue in actionable if issue.replacement]
    removable = [issue for issue in actionable if not issue.replacement]
    review_only = [
        issue
        for issue in result.issues
        if not issue.actionable and issue.field != "isin/cusip"
    ]
    consistency = [
        issue
        for issue in result.issues
        if issue.field == "isin/cusip" and not issue.actionable
    ]
    print(
        f"Checked {result.identifiers_checked} populated identifiers and "
        f"{result.relationships_checked} US/Canadian ISIN-CUSIP pairs in "
        f"{result.files_scanned} CSV files; found {len(actionable) + len(review_only)} "
        f"invalid values ({len(repairable)} repairable, {len(removable)} removable, "
        f"{len(review_only)} review-only) and {len(consistency)} consistency issues."
    )


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the identifier audit command.
    """
    arguments = build_parser().parse_args(argv)
    if not discover_csv_files(arguments.paths):
        print("No CSV files found.")
        return 2

    result = audit_identifiers(arguments.paths)

    if arguments.apply:
        actionable = [issue for issue in result.issues if issue.actionable]
        affected_paths = sorted({issue.path for issue in actionable})
        cleanup_results = [apply_identifier_cleanup(path) for path in affected_paths]
        repaired = sum(cleanup.repaired for cleanup in cleanup_results)
        cleared = sum(cleanup.cleared for cleanup in cleanup_results)
        print(
            f"Repaired {repaired} and cleared {cleared} invalid identifier values "
            f"in {len(affected_paths)} CSV files."
        )
        result = audit_identifiers(arguments.paths)

    if arguments.report_file is not None:
        _write_report(arguments.report_file, result.issues)
        print(
            f"Wrote {len(result.issues)} identifier findings to "
            f"{arguments.report_file}."
        )
    else:
        _print_issues(result.issues)
    _print_audit_summary(result)
    if result.issues and not arguments.apply:
        print(
            "Report only: no files changed. Re-run with --apply to repair deterministic "
            "damage and clear other identifiers that fail validation."
        )
    return 0


def check_categories(database: str = "database") -> dict[str, str]:
    """
    Check every equity's sector, industry group and industry against scripts/categories.json.

    Args:
        database (str): The database folder.

    Returns:
        dict[str, str]: Symbol -> the level that is not found, empty when all are valid.
    """
    tree = json.loads(Path("scripts/categories.json").read_text(encoding="utf-8"))
    columns = ["symbol", "sector", "industry_group", "industry"]
    equities = pd.concat(
        [
            pd.read_csv(path, usecols=columns, dtype=str, keep_default_na=False)
            for path in sorted(Path(database, "equities").glob("*.csv"))
        ]
    ).set_index("symbol")
    return categories_model.find_invalid_categories(equities, tree)


def run_categories_check() -> None:
    """
    Command line entry of the categories check; fails on an unknown combination.

    Raises:
        ValueError: When invalid combinations are found.
    """
    invalid = check_categories()
    if invalid:
        print("Invalid Rows for:")
        for symbol, error in invalid.items():
            print(f"{symbol}: {error}")
        raise ValueError(
            "There are invalid sector, industry groups and/or industries found. "
            "Please check if it adheres to scripts/categories.json"
        )
    print("All sectors, industry groups and industries are in scripts/categories.json.")


def run_git(*arguments: str) -> str:
    """
    Run a git command in the repository and return its output.

    Args:
        *arguments (str): The git arguments.

    Returns:
        str: The standard output.
    """
    return subprocess.run(  # noqa: S603
        ["git", *arguments],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def check_database(database: str = "database", reference: str = "HEAD") -> list[str]:
    """
    The problems an update of the database files introduced compared with a commit.

    Args:
        database (str): The database folder.
        reference (str): The commit to compare with.

    Returns:
        list[str]: The new problems, empty when the update is sound.
    """
    root = Path(database)
    current = {}
    for path in sorted(root.glob("*.csv")) + sorted(root.glob("*/*.csv")):
        name = path.relative_to(root).as_posix()
        try:
            current[name] = integrity_model.read_symbols(path.read_text("utf-8"))
        except (ValueError, UnicodeDecodeError) as error:
            current[name] = ("", [])
            print(f"{name}: unreadable ({error})")
    listed = run_git("ls-tree", "-r", "--name-only", reference, database).split()
    previous = {}
    for path in (p for p in listed if p.endswith(".csv")):
        text = run_git("show", f"{reference}:{path}")
        previous[Path(path).relative_to(root).as_posix()] = (
            integrity_model.read_symbols(text)
        )
    problems = integrity_model.find_problems(current, previous)
    problems += [
        f"{name}: unreadable" for name, (header, _) in current.items() if not header
    ]
    return problems


def run_database_check() -> None:
    """
    Command line entry of the database check; with --restore an update that introduced
    problems is undone, so the pipeline never commits it.
    """
    parser = argparse.ArgumentParser(description="Check the database before a commit.")
    parser.add_argument("--database", default="database")
    parser.add_argument("--restore", action="store_true")
    arguments = parser.parse_args()
    problems = check_database(arguments.database)
    if not problems:
        print("The database update is sound.")
        return
    print(f"The database update introduced {len(problems)} problem(s):")
    for problem in problems[:50]:
        print(f"  {problem}")
    if arguments.restore:
        run_git("checkout", "HEAD", "--", arguments.database)
        run_git("clean", "-fdq", arguments.database)
        print("The database files are restored to the last commit.")
    else:
        sys.exit(1)
