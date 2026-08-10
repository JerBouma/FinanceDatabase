"""Tests for the conservative US equity import tooling."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from financedatabase.validation.update_us_equities import (
    EQUITY_COLUMNS,
    InstrumentOverride,
    classify_instrument,
    load_overrides,
    run_backfill,
    run_import,
)


@pytest.mark.parametrize(
    ("name", "status", "instrument_type"),
    [
        ("Example Inc. Common Stock", "accepted", "Common Stock"),
        ("Example plc Ordinary Shares", "accepted", "Common Stock"),
        (
            "Example Ltd. American Depositary Shares",
            "accepted",
            "Depositary Receipt",
        ),
        (
            "Example L.P. Common Units representing limited partner interests",
            "accepted",
            "Partnership Interest",
        ),
        ("Example Acquisition Corp. Warrants", "rejected", "Warrant"),
        ("ADS-TEC ENERGY PLC Warrant", "rejected", "Warrant"),
        (
            "Example warrant exercisable for one share of common stock",
            "rejected",
            "Warrant",
        ),
        ("Example Acquisition Corp. Units", "rejected", "Unit"),
        ("Example Acquisition Corp. Rights", "rejected", "Right"),
        ("Example 7.25% Senior Notes due 2031", "rejected", "Debt Security"),
        ("Example Preferred Stock", "accepted", "Preferred Stock"),
        (
            "Example Depositary Shares representing Preferred Stock",
            "accepted",
            "Preferred Stock",
        ),
        (
            "Example L.P. Series B Preferred Units representing limited partner interests",
            "accepted",
            "Preferred Stock",
        ),
        (
            "Example Sponsored ADR Representing Perpetual Preferred Series G",
            "accepted",
            "Preferred Stock",
        ),
        ("Example Corp. 6.50% Pfd Ser A", "accepted", "Preferred Stock"),
        ("Example Corp. Preference Shares", "accepted", "Preferred Stock"),
        ("Example Trust Preferred Securities", "rejected", "Hybrid Security"),
        (
            "Example Capital Trust II PFD TR 7.20%",
            "rejected",
            "Hybrid Security",
        ),
        ("Example ETF", "rejected", "Exchange-Traded Product"),
        ("Example Income Fund Common Shares", "rejected", "Fund"),
        ("Example Municipal Target Term Trust", "rejected", "Fund"),
        ("Example Holdings Ltd.", "quarantined", ""),
        ("Preferred Bank Common Stock", "accepted", "Common Stock"),
    ],
)
def test_classify_instrument(name: str, status: str, instrument_type: str) -> None:
    decision = classify_instrument(name)
    assert (decision.status, decision.instrument_type) == (status, instrument_type)


def test_reviewed_override_is_authoritative() -> None:
    override = InstrumentOverride(
        decision="allow",
        instrument_type="Common Stock",
        evidence_url="https://example.test/evidence",
        notes="Reviewed false positive",
    )
    decision = classify_instrument("Example Warrants", override)
    assert decision.status == "accepted"
    assert decision.reason == "reviewed_override"


def test_load_overrides_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "overrides.csv"
    path.write_text(
        "source_exchange,symbol,decision,instrument_type,evidence_url,notes\n"
        "NASDAQ,TEST,allow,Common Stock,https://example.test/1,first\n"
        "NASDAQ,TEST,reject,Warrant,https://example.test/2,second\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate override"):
        load_overrides(path)


def _empty_equity_frame() -> pd.DataFrame:
    frame = pd.DataFrame(columns=EQUITY_COLUMNS)
    frame.index.name = "symbol"
    return frame


def _write_exchange(
    path: Path, rows: dict[str, dict[str, object]] | None = None
) -> None:
    frame = _empty_equity_frame()
    if rows:
        frame = pd.DataFrame.from_dict(rows, orient="index").reindex(
            columns=EQUITY_COLUMNS
        )
        frame.index.name = "symbol"
    frame.to_csv(path, lineterminator="\n")


def _source(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows).set_index("symbol")


def test_run_import_dry_run_does_not_modify_equities(tmp_path: Path) -> None:
    equities_dir = tmp_path / "equities"
    equities_dir.mkdir()
    equities_path = equities_dir / "NMS.csv"
    _write_exchange(equities_path)
    before = equities_path.read_bytes()
    overrides = tmp_path / "overrides.csv"
    overrides.write_text(
        "source_exchange,symbol,decision,instrument_type,evidence_url,notes\n",
        encoding="utf-8",
    )

    counts = run_import(
        apply=False,
        report_path=tmp_path / "report.csv",
        equities_dir=equities_dir,
        overrides_path=overrides,
        source_frames={
            "NASDAQ": _source(
                [
                    {
                        "symbol": "DRYRUN",
                        "name": "Dry Run Example Common Stock",
                        "industry": "Software",
                        "country": "United States",
                        "marketCap": 1_000_000,
                    }
                ]
            )
        },
        industries=pd.DataFrame({"mapped": ["Software"]}, index=["Software"]),
    )

    assert counts["accepted"] == 1
    assert equities_path.read_bytes() == before


def test_run_import_routes_accepts_and_reports_candidates(tmp_path: Path) -> None:
    equities_dir = tmp_path / "equities"
    equities_dir.mkdir()
    for exchange in ("NMS", "NYQ", "ASE"):
        _write_exchange(equities_dir / f"{exchange}.csv")
    overrides = tmp_path / "overrides.csv"
    overrides.write_text(
        "source_exchange,symbol,decision,instrument_type,evidence_url,notes\n",
        encoding="utf-8",
    )
    report = tmp_path / "report.csv"
    sources = {
        "NASDAQ": _source(
            [
                {
                    "symbol": "NDAQ",
                    "name": "Nasdaq Example Common Stock",
                    "industry": "Software",
                    "country": "United States",
                    "marketCap": 1_000_000,
                },
                {
                    "symbol": "NDAQW",
                    "name": "Nasdaq Example Warrant",
                    "industry": "",
                    "country": "United States",
                    "marketCap": 0,
                },
                {
                    "symbol": "PLAIN",
                    "name": "Plain Holdings Ltd.",
                    "industry": "",
                    "country": "United States",
                    "marketCap": 0,
                },
            ]
        ),
        "NYSE": _source(
            [
                {
                    "symbol": "NYSEX",
                    "name": "NYSE Example Common Shares",
                    "industry": "Software",
                    "country": "United States",
                    "marketCap": 1_000_000,
                }
            ]
        ),
        "AMEX": _source(
            [
                {
                    "symbol": "AMEXX",
                    "name": "AMEX Example Ordinary Shares",
                    "industry": "Software",
                    "country": "United States",
                    "marketCap": 1_000_000,
                }
            ]
        ),
    }
    industries = pd.DataFrame({"mapped": ["Software"]}, index=["Software"])

    counts = run_import(
        apply=True,
        report_path=report,
        equities_dir=equities_dir,
        overrides_path=overrides,
        source_frames=sources,
        industries=industries,
    )

    assert counts == {
        "accepted": 3,
        "rejected": 1,
        "quarantined": 1,
        "already_present": 0,
    }
    expected_routes = {
        "NMS": ("NDAQ", "XNAS", "NASDAQ Global Select"),
        "NYQ": ("NYSEX", "XNYS", "New York Stock Exchange"),
        "ASE": ("AMEXX", "XASE", "NYSE MKT"),
    }
    for exchange, (symbol, mic, market) in expected_routes.items():
        frame = pd.read_csv(equities_dir / f"{exchange}.csv", index_col=0)
        assert frame.loc[symbol, "mic"] == mic
        assert frame.loc[symbol, "market"] == market
        assert frame.loc[symbol, "instrument_type"] == "Common Stock"
    with report.open(encoding="utf-8", newline="") as handle:
        reported = list(csv.DictReader(handle))
    assert {row["symbol"] for row in reported} == {
        "NDAQ",
        "NDAQW",
        "PLAIN",
        "NYSEX",
        "AMEXX",
    }


def test_run_backfill_populates_removes_and_retains_ambiguous(tmp_path: Path) -> None:
    equities_dir = tmp_path / "equities"
    equities_dir.mkdir()

    def row(name: str) -> dict[str, object]:
        values = {column: "" for column in EQUITY_COLUMNS}
        values.update(
            {
                "name": name,
                "exchange": "NMS",
                "mic": "XNAS",
                "market": "NASDAQ Global Select",
                "delisted": "False",
            }
        )
        return values

    _write_exchange(
        equities_dir / "NMS.csv",
        {
            "COMMON": row("Example Common Stock"),
            "PARTNER": row(
                "Example L.P. Common Units representing limited partner interests"
            ),
            "WARRANT": row("Example Warrants"),
            "PREFERRED": row("Example Preferred Stock"),
            "PLAIN": row("Example Holdings Ltd."),
        },
    )
    overrides = tmp_path / "overrides.csv"
    overrides.write_text(
        "source_exchange,symbol,decision,instrument_type,evidence_url,notes\n",
        encoding="utf-8",
    )
    report = tmp_path / "report.csv"

    counts = run_backfill(
        apply=True,
        report_path=report,
        equities_dir=equities_dir,
        overrides_path=overrides,
    )

    frame = pd.read_csv(
        equities_dir / "NMS.csv", index_col=0, dtype=str, keep_default_na=False
    )
    assert set(frame.index) == {"COMMON", "PARTNER", "PREFERRED", "PLAIN"}
    assert frame.loc["COMMON", "instrument_type"] == "Common Stock"
    assert frame.loc["PARTNER", "instrument_type"] == "Partnership Interest"
    assert frame.loc["PREFERRED", "instrument_type"] == "Preferred Stock"
    assert frame.loc["PLAIN", "instrument_type"] == ""
    assert counts["removed"] == 1
    assert counts["updated"] == 3
