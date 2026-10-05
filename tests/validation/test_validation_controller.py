"""Validation Controller Tests"""

import csv
import warnings
from pathlib import Path

import pytest

from financedatabase.validation.identifiers_model import (
    CleanupResult,
)
from financedatabase.validation.validation_controller import (
    apply_identifier_cleanup,
    audit_identifiers,
    main,
)

DATABASE_DIR = Path(__file__).resolve().parents[2] / "database"


def test_audit_and_apply_invalid_identifiers(tmp_path: Path) -> None:
    """Test that invalid identifiers are audited and cleared."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_text(
        "symbol,isin,cusip,figi,composite_figi,shareclass_figi,delisted\n"
        "AAPL,US0378331005,037833100,BBG000BLNQ16,BBG000BLNQ16,BBG000BLNQ16,False\n"
        "BAD,US0378331004,037833101,#REF!,,,False\n"
        "MISMATCH,US0378331005,594918104,,,,False\n",
        encoding="utf-8",
    )

    result = audit_identifiers([tmp_path])

    assert result.files_scanned == 1
    assert result.identifiers_checked == 10
    assert result.relationships_checked == 2
    assert len(result.issues) == 4
    assert sum(issue.actionable for issue in result.issues) == 3
    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=1, cleared=2)
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip,figi,composite_figi,shareclass_figi,delisted\n"
        "AAPL,US0378331005,037833100,BBG000BLNQ16,BBG000BLNQ16,BBG000BLNQ16,False\n"
        "BAD,,037833101,,,,False\n"
        "MISMATCH,US0378331005,037833100,,,,False\n"
    )


def test_apply_repairs_corroborated_cusip_and_clears_isin_incompatible_cusip(
    tmp_path: Path,
) -> None:
    """Test that a corroborated CUSIP is repaired and one incompatible with the ISIN is cleared."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_text(
        "symbol,isin,cusip\n"
        "ACER,US0044342055,4434205.0\n"
        "ABITARE,IT0005445280,2824100\n",
        encoding="utf-8",
    )

    result = audit_identifiers([csv_path])
    issues = {issue.symbol: issue for issue in result.issues}
    assert issues["ACER"].replacement == "004434205"
    assert issues["ABITARE"].replacement is None
    assert issues["ABITARE"].actionable
    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=1, cleared=1)
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip\n" "ACER,US0044342055,004434205\n" "ABITARE,IT0005445280,\n"
    )


def test_apply_preserves_cusip_when_isin_is_missing_or_invalid(
    tmp_path: Path,
) -> None:
    """Test that the CUSIP is kept when the ISIN is missing or invalid."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_text(
        "symbol,isin,cusip\nUNKNOWN,,2824100\n",
        encoding="utf-8",
    )

    result = audit_identifiers([csv_path])
    assert not result.issues[0].actionable
    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=0, cleared=0)
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip\nUNKNOWN,,2824100\n"
    )


def test_apply_preserves_quoting_and_line_endings(tmp_path: Path) -> None:
    """Test that applying fixes keeps the quoting and line endings."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_bytes(
        b'symbol,name,isin,cusip\r\nBAD,"Unnecessarily quoted",US0378331004,037833101\r\n'
    )

    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=0, cleared=1)
    assert csv_path.read_bytes() == (
        b'symbol,name,isin,cusip\r\nBAD,"Unnecessarily quoted",,037833101\r\n'
    )


def test_main_is_a_dry_run_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main only reports by default."""
    csv_path = tmp_path / "equities.csv"
    original = "symbol,isin,cusip\nBAD,US0378331004,037833101\n"
    csv_path.write_text(original, encoding="utf-8")

    assert main([str(tmp_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == original
    assert "Report only: no files changed" in capsys.readouterr().out


def test_main_apply_repairs_or_clears_invalid_identifiers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main with --apply repairs or clears invalid identifiers."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_text(
        "symbol,isin,cusip,figi\nBAD,US0378331004,037833101,#REF!\n",
        encoding="utf-8",
    )

    assert main(["--apply", str(csv_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip,figi\nBAD,,037833101,\n"
    )
    assert (
        "Repaired 0 and cleared 2 invalid identifier values" in capsys.readouterr().out
    )


def test_main_apply_repairs_cusip_from_authoritative_isin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main with --apply repairs a CUSIP from an authoritative ISIN."""
    csv_path = tmp_path / "equities.csv"
    csv_path.write_text(
        "symbol,isin,cusip\nMISMATCH,US0378331005,594918104\n",
        encoding="utf-8",
    )

    assert main(["--apply", str(csv_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip\nMISMATCH,US0378331005,037833100\n"
    )
    assert (
        "Repaired 1 and cleared 0 invalid identifier values" in capsys.readouterr().out
    )


def test_main_apply_leaves_consistency_issues_for_manual_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main with --apply leaves consistency issues for manual review."""
    csv_path = tmp_path / "equities.csv"
    # US6604876473 is a valid ISIN whose embedded national code is not itself a
    # valid CUSIP, so it cannot corroborate a repair of the stored (valid) CUSIP.
    original = "symbol,isin,cusip\nMISMATCH,US6604876473,037833100\n"
    csv_path.write_text(original, encoding="utf-8")

    assert main(["--apply", str(csv_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == original
    assert "consistency issues" in capsys.readouterr().out


def test_main_writes_post_cleanup_findings_to_csv_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that main writes the remaining findings to a CSV report."""
    csv_path = tmp_path / "equities.csv"
    report_path = tmp_path / "identifier-findings.csv"
    csv_path.write_text(
        "symbol,isin,cusip\nBAD,US0378331004,037833101\n",
        encoding="utf-8",
    )

    assert main(["--apply", "--report-file", str(report_path), str(csv_path)]) == 0

    with report_path.open(encoding="utf-8", newline="") as report_file:
        rows = list(csv.DictReader(report_file))
    assert rows == [
        {
            "file": str(csv_path),
            "line": "2",
            "symbol": "BAD",
            "field": "cusip",
            "value": "037833101",
            "problem": "checksum mismatch",
            "actionable": "False",
            "suggested_replacement": "",
        }
    ]
    output = capsys.readouterr().out
    assert "Wrote 1 identifier findings" in output
    assert "037833101" not in output


def test_database_identifiers_have_no_actionable_issues() -> None:
    """Fail the contributor's own test run when a CSV holds a repairable or clearable
    identifier, so bad data is caught before a PR is opened rather than auto-fixed
    later. Run `uv run python -m financedatabase.validation --apply`
    to fix these.
    """
    result = audit_identifiers([DATABASE_DIR])
    actionable = [issue for issue in result.issues if issue.actionable]
    non_actionable = [issue for issue in result.issues if not issue.actionable]

    if non_actionable:
        warnings.warn(
            f"{len(non_actionable)} identifier finding(s) require manual review "
            "(ambiguous CUSIPs or ISIN/CUSIP mismatches, e.g. dual-listed shares) "
            "and were left unchanged; run "
            "`uv run python -m financedatabase.validation database` "
            "for the full report.",
            stacklevel=1,
        )

    assert not actionable, (
        f"{len(actionable)} repairable/removable identifier finding(s) found:\n"
        + "\n".join(
            f"{issue.path}:{issue.line_number}: {issue.field} ({issue.symbol}) "
            f"{issue.value!r}: {issue.reason}"
            for issue in actionable
        )
        + "\nRun `uv run python -m financedatabase.validation "
        "database --apply` to fix these automatically."
    )
