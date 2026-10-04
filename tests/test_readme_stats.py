"""Tests for scripts/update_readme_stats.py (README statistics section)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_readme_stats.py"
spec = importlib.util.spec_from_file_location("update_readme_stats", SCRIPT)
rs = importlib.util.module_from_spec(spec)
sys.modules["update_readme_stats"] = rs
spec.loader.exec_module(rs)


def make_db(root: Path) -> Path:
    db = root / "database"
    for sub in ("equities", "etfs", "funds"):
        (db / sub).mkdir(parents=True)
    (db / "equities" / "NMS.csv").write_text(
        "symbol,name,sector,industry,country,exchange,delisted\n"
        "AAA,A Inc,Information Technology,Software,United States,NMS,False\n"
        "NA,Nano Labs,Information Technology,Semiconductors,China,NMS,False\n"
        "OLD,Old Co,Energy,Oil & Gas,United States,NMS,True\n"
    )
    (db / "etfs" / "PCX.csv").write_text(
        "symbol,name,family,category_group,category,exchange,delisted\n"
        "SPY,SPDR,State Street,Equities,Large Cap,PCX,False\n"
        "XYZ,Gone,State Street,Equities,Large Cap,PCX,True\n"
    )
    (db / "funds" / "NAS.csv").write_text(
        "symbol,name,family,category_group,category,exchange\nF1,Fund,Acme,Equities,Blend,NAS\n"
    )
    (db / "indices.csv").write_text(
        "symbol,name,category,exchange\n^X,Index,Equities,NIM\n"
    )
    (db / "currencies.csv").write_text(
        "symbol,name,base_currency,quote_currency\nEUR=X,USD/EUR,USD,EUR\n"
    )
    (db / "cryptos.csv").write_text(
        "symbol,name,cryptocurrency,currency\nBTC-USD,BTC,BTC,USD\n"
    )
    (db / "moneymarkets.csv").write_text(
        "symbol,name,family,exchange\nM1,MM,Acme,NAS\n"
    )
    return db


README = "# Title\n\nIntro.\n\n<!-- STATISTICS:START -->\nold\n<!-- STATISTICS:END -->\n\n# Installation\n"


def test_section_is_regenerated_between_markers(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    assert rs.update(readme, str(db), dt.date(2026, 10, 4))
    text = readme.read_text()
    assert text.startswith("# Title\n\nIntro.\n\n<!-- STATISTICS:START")
    assert text.endswith("<!-- STATISTICS:END -->\n\n# Installation\n")
    assert "old" not in text
    # 3 equities incl. the ticker 'NA' (must not be read as missing), 2 actively listed
    assert (
        "| 🏢 | **Equities** | 3 | 2 | 1 | 2 sectors · 3 industries · 2 countries |"
        in text
    )
    assert "| 📦 | **ETFs** | 2 | 1 | 1 | 1 issuers · 1 categories |" in text
    assert "| | **Total** | **10** | | | |" in text
    assert "badge/updated-2026--10--04-" in text
    assert '    "Equities" : 3' in text and "```mermaid" in text


def test_regeneration_is_idempotent(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    rs.update(readme, str(db), dt.date(2026, 10, 4))
    once = readme.read_text()
    rs.update(readme, str(db), dt.date(2026, 10, 4))
    assert readme.read_text() == once


def test_missing_markers_change_nothing(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# No markers here\n")
    assert rs.update(readme, str(make_db(tmp_path)), dt.date(2026, 10, 4)) is False
    assert readme.read_text() == "# No markers here\n"


def test_bars_scale_to_the_largest_value() -> None:
    assert rs.bar(100, 100) == "█" * rs.BAR_WIDTH
    assert rs.bar(0, 100) == ""
    assert rs.bar(50, 100) == "█" * (rs.BAR_WIDTH // 2)


def test_main_never_raises(tmp_path: Path, monkeypatch, capsys) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(README)
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--readme", str(readme), "--database", str(tmp_path / "nope")],
    )
    rs.main()
    assert "README statistics not refreshed" in capsys.readouterr().out
