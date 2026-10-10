"""README Statistics Tests"""

import sys
from pathlib import Path

from scripts.readme import readme_controller


def create_database(root: Path) -> Path:
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
    """Test that the statistics section is regenerated between the markers."""
    db = create_database(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    assert readme_controller.update(readme, str(db))
    text = readme.read_text()
    assert text.startswith("# Title\n\nIntro.\n\n<!-- STATISTICS:START")
    assert text.endswith("<!-- STATISTICS:END -->\n\n# Installation\n")
    assert "old" not in text
    # 3 equities incl. the ticker 'NA' (must not be read as missing)
    assert (
        "| 🏢 | **Equities** | 3 | 1 | 2 sectors · 3 industries · 2 countries |" in text
    )
    assert "| 📦 | **ETFs** | 2 | 1 | 1 issuers · 1 categories |" in text
    assert "| | **Total** | **10** | | |" in text
    assert "shields.io" not in text
    assert "<details>" not in text


def test_regeneration_is_idempotent(tmp_path: Path) -> None:
    """Test that regenerating the statistics twice gives the same README."""
    db = create_database(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(README)
    readme_controller.update(readme, str(db))
    once = readme.read_text()
    readme_controller.update(readme, str(db))
    assert readme.read_text() == once


def test_missing_markers_change_nothing(tmp_path: Path) -> None:
    """Test that a README without the markers is left unchanged."""
    readme = tmp_path / "README.md"
    readme.write_text("# No markers here\n")
    assert readme_controller.update(readme, str(create_database(tmp_path))) is False
    assert readme.read_text() == "# No markers here\n"


def test_main_never_raises(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that main reports a failure instead of raising."""
    readme = tmp_path / "README.md"
    readme.write_text(README)
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--readme", str(readme), "--database", str(tmp_path / "nope")],
    )
    readme_controller.main()
    assert "README statistics not refreshed" in capsys.readouterr().out
