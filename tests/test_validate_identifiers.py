import csv
from pathlib import Path

import pytest

from scripts.validate_identifiers import (
    AuditComparison,
    CleanupResult,
    apply_identifier_cleanup,
    audit_identifiers,
    compare_audits,
    main,
    repair_identifier,
    validate_cusip,
    validate_figi,
    validate_isin,
    validate_isin_cusip_consistency,
)


@pytest.mark.parametrize(
    "isin",
    ["US0378331005", "GB0002634946", "AU0000XVGZA3", "XS0971721963"],
)
def test_validate_isin_accepts_valid_values(isin: str) -> None:
    assert validate_isin(isin) is None


@pytest.mark.parametrize(
    "isin",
    [
        "us0378331005",
        " US0378331005 ",
        "US037833100",
        "US037833100A",
    ],
)
def test_validate_isin_rejects_noncanonical_or_invalid_values(isin: str) -> None:
    assert validate_isin(isin) is not None


def test_validate_isin_reports_checksum_mismatch() -> None:
    assert validate_isin("US0378331004") == "checksum mismatch"


@pytest.mark.parametrize("cusip", ["037833100", "594918104", "17275R102"])
def test_validate_cusip_accepts_valid_values(cusip: str) -> None:
    assert validate_cusip(cusip) is None


@pytest.mark.parametrize(
    "cusip",
    [
        " 037833100 ",
        "194162103.0",
        "03783310A",
    ],
)
def test_validate_cusip_rejects_noncanonical_or_invalid_values(cusip: str) -> None:
    assert validate_cusip(cusip) is not None


def test_validate_cusip_reports_checksum_mismatch() -> None:
    assert validate_cusip("037833101") == "checksum mismatch"


def test_validate_figi_accepts_valid_value() -> None:
    assert validate_figi("BBG000BLNQ16") is None


@pytest.mark.parametrize(
    "figi",
    [
        " bbg000blnq16 ",
        "BBG000BLNA16",
        "#REF!",
    ],
)
def test_validate_figi_rejects_noncanonical_or_invalid_values(figi: str) -> None:
    assert validate_figi(figi) is not None


def test_validate_figi_reports_checksum_mismatch() -> None:
    assert validate_figi("BBG000BLNQ15") == "checksum mismatch"


def test_validate_isin_cusip_consistency() -> None:
    assert validate_isin_cusip_consistency("US0378331005", "037833100") is None
    assert validate_isin_cusip_consistency("GB0002634946", "594918104") is None
    assert validate_isin_cusip_consistency("US0378331005", "594918104") == (
        "ISIN national identifier does not match CUSIP"
    )


def test_repair_identifier_requires_deterministic_evidence() -> None:
    assert repair_identifier("isin", " us0378331005 ", {}) == "US0378331005"
    assert repair_identifier("figi", " bbg000blnq16 ", {}) == "BBG000BLNQ16"
    assert repair_identifier("isin", "US0378331005.0", {}) == "US0378331005"
    assert repair_identifier("figi", "BBG000BLNQ16.0", {}) == "BBG000BLNQ16"
    assert repair_identifier("cusip", "962166104.0", {}) == "962166104"
    assert (
        repair_identifier("cusip", "4434205.0", {"isin": "US0044342055"}) == "004434205"
    )
    assert repair_identifier("cusip", "2824100", {"isin": "IT0005445280"}) is None


def test_audit_and_apply_invalid_identifiers(tmp_path: Path) -> None:
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
    assert sum(issue.actionable for issue in result.issues) == 2
    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=0, cleared=2)
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip,figi,composite_figi,shareclass_figi,delisted\n"
        "AAPL,US0378331005,037833100,BBG000BLNQ16,BBG000BLNQ16,BBG000BLNQ16,False\n"
        "BAD,,037833101,,,,False\n"
        "MISMATCH,US0378331005,594918104,,,,False\n"
    )


def test_apply_repairs_corroborated_cusip_and_preserves_ambiguous_value(
    tmp_path: Path,
) -> None:
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
    assert not issues["ABITARE"].actionable
    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=1, cleared=0)
    assert csv_path.read_text(encoding="utf-8") == (
        "symbol,isin,cusip\n"
        "ACER,US0044342055,004434205\n"
        "ABITARE,IT0005445280,2824100\n"
    )


def test_apply_preserves_quoting_and_line_endings(tmp_path: Path) -> None:
    csv_path = tmp_path / "equities.csv"
    csv_path.write_bytes(
        b'symbol,name,isin,cusip\r\nBAD,"Unnecessarily quoted",US0378331004,037833101\r\n'
    )

    assert apply_identifier_cleanup(csv_path) == CleanupResult(repaired=0, cleared=1)
    assert csv_path.read_bytes() == (
        b'symbol,name,isin,cusip\r\nBAD,"Unnecessarily quoted",,037833101\r\n'
    )


def test_compare_audits_reports_only_new_and_resolved_findings(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()
    (baseline / "equities.csv").write_text(
        "symbol,isin\nOLD,US0378331004\nFIXED,US0378331004\n",
        encoding="utf-8",
    )
    (current / "equities.csv").write_text(
        "symbol,isin\nNEW,US0378331004\nOLD,US0378331004\nFIXED,US0378331005\n",
        encoding="utf-8",
    )

    current_audit = audit_identifiers([current])
    baseline_audit = audit_identifiers([baseline])
    comparison = compare_audits(current_audit, baseline_audit, current, baseline)

    assert comparison == AuditComparison(
        new_issues=(current_audit.issues[0],),
        resolved_issues=(baseline_audit.issues[1],),
    )


def test_main_is_a_dry_run_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "equities.csv"
    original = "symbol,isin,cusip\nBAD,US0378331004,037833101\n"
    csv_path.write_text(original, encoding="utf-8")

    assert main([str(tmp_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == original
    assert "Report only: no files changed" in capsys.readouterr().out


def test_main_apply_repairs_or_clears_invalid_identifiers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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


def test_main_apply_leaves_consistency_issues_for_manual_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "equities.csv"
    original = "symbol,isin,cusip\nMISMATCH,US0378331005,594918104\n"
    csv_path.write_text(original, encoding="utf-8")

    assert main(["--apply", str(csv_path)]) == 0
    assert csv_path.read_text(encoding="utf-8") == original
    assert "consistency issues" in capsys.readouterr().out


def test_main_baseline_emits_github_warning_only_for_new_issue(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()
    (baseline / "equities.csv").write_text(
        "symbol,isin\nOLD,US0378331004\n",
        encoding="utf-8",
    )
    (current / "equities.csv").write_text(
        "symbol,isin\nOLD,US0378331004\nNEW,US0378331004\n",
        encoding="utf-8",
    )

    assert (
        main(
            [
                "--baseline",
                str(baseline),
                "--github-annotations",
                str(current),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "::warning " in output
    assert "NEW" in output
    assert "OLD" not in output
    assert "found 1 new and 0 resolved identifier findings" in output


def test_main_writes_post_cleanup_findings_to_csv_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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
