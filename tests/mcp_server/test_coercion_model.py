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
