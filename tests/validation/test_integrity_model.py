"""Integrity Model Tests"""

from scripts.validation import integrity_model


def test_database_check_finds_new_problems_only() -> None:
    """Test that the pre-commit check reports what an update broke, not old issues."""
    header = "symbol,name"
    reference = {
        "equities/NMS.csv": (header, ["AAPL", "MSFT", "CHAD"]),
        "etfs/PCX.csv": (header, ["SPY", "CHAD"]),
        "cryptos.csv": (header, [f"C{i}-USD" for i in range(20)]),
    }
    assert integrity_model.find_problems(reference, reference) == []
    broken = {
        "equities/NMS.csv": ("symbol,name,extra", ["AAPL", "AAPL", "MSFT", "CHAD"]),
        "etfs/PCX.csv": (header, ["SPY", "CHAD", "MSFT"]),
        "cryptos.csv": (header, [f"C{i}-USD" for i in range(10)]),
        "etfs/ZZZ.csv": ("bogus", ["X"]),
        "etfs/NEW.csv": (header, ["QQQ"]),
    }
    problems = integrity_model.find_problems(broken, reference)
    assert "equities/NMS.csv: header changed" in problems
    assert "equities: symbol 'AAPL' appears more than once" in problems
    assert "cryptos: 20 rows dropped to 10" in problems
    assert "symbol 'MSFT' is in both equities and etfs" in problems
    assert "etfs/ZZZ.csv: new file with other columns than its asset class" in problems
    assert not any("CHAD" in problem or "NEW.csv" in problem for problem in problems)
