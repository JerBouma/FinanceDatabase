"""Coercion Model Tests"""

from financedatabase.mcp_server.coercion_model import resolve_values


def test_resolve_values_accepts_a_unique_prefix() -> None:
    """Test that the start of one option, word for word, stands for that option."""
    options = {"vanguard asset management", "blackrock funds", "blackrock funds iii"}
    assert resolve_values("Vanguard", options) == (["vanguard asset management"], [])
    assert resolve_values("BlackRock", options)[1] == ["BlackRock"]
    assert resolve_values("BlackRock", options, expand_prefix=True) == (
        ["blackrock funds", "blackrock funds iii"],
        [],
    )
    assert resolve_values("Van", options)[1] == ["Van"]


def test_resolve_values_ignores_accents() -> None:
    """Test that 'curacao' finds 'Curaçao' and an accent in the value is no obstacle."""
    options = {"curaçao", "netherlands", "hotels, restaurants & leisure"}
    assert resolve_values("curacao", options) == (["curaçao"], [])
    assert resolve_values("Curacao, Netherlands", options) == (
        ["curaçao", "Netherlands"],
        [],
    )
    assert resolve_values("Nethèrlands", options) == (["netherlands"], [])
    assert resolve_values("Hotels, Restaurants & Leisure", options)[1] == []


def test_resolve_values_accepts_synonyms() -> None:
    """Test that another name for a value finds it, but never hides a real option."""
    options = {"ivory coast", "united states", "us"}
    synonyms = {
        "Ivory Coast": ["Côte d'Ivoire"],
        "United States": ["USA", "US"],
        "Missing": ["Elsewhere"],
    }
    assert resolve_values("cote d'ivoire", options, synonyms=synonyms) == (
        ["ivory coast"],
        [],
    )
    assert resolve_values("USA", options, synonyms=synonyms) == (["united states"], [])
    assert resolve_values("US", options, synonyms=synonyms) == (["US"], [])
    assert resolve_values("Elsewhere", options, synonyms=synonyms)[1] == ["Elsewhere"]
