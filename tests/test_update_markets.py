"""Update Markets Tests"""

import pandas as pd

from scripts.markets import markets_model


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows).set_index("symbol").astype(str)


def test_update_cryptos_adds_top_coins_and_drops_dead_ones() -> None:
    """Test that top coins get the usual quotes and coins no longer listed go."""
    rows = []
    for coin, name in [("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("DEAD", "Deadcoin")]:
        for quote in ("USD", "EUR"):
            rows.append(
                {
                    "symbol": f"{coin}-{quote}",
                    "name": f"{name} {quote}",
                    "cryptocurrency": coin,
                    "currency": quote,
                    "summary": "",
                    "exchange": "CCC",
                    "website": "",
                }
            )
    rows.append({**rows[0], "symbol": "BTC-JPY", "currency": "JPY"})
    coins = pd.DataFrame(
        [
            ("bitcoin", "BTC", "Bitcoin", 1),
            ("sui", "SUI", "Sui", 2),
            ("sui-bridged", "SUI", "Bridged Sui", 2),
            ("other-eth", "ETH", "Other Ether", 3),
            ("fund", "BUIDL", "Some Liquidity Fund", 4),
            ("odd", "A_B", "Odd", 5),
        ],
        columns=["id", "symbol", "name", "rank"],
    )
    frame, added, gone = markets_model.update_cryptos(
        _frame(rows),
        coins,
        {"BTC", "ETH", "SUI", "BUIDL"},
        lambda coin_id: f"https://{coin_id}.org",
        set(),
    )
    assert added == ["SUI"]
    assert gone == ["DEAD"]
    assert {"SUI-USD", "SUI-EUR"} <= set(frame.index)
    assert "SUI-JPY" not in frame.index  # only quotes most coins trade in
    assert frame.loc["SUI-USD", "name"] == "Sui USD"
    assert frame.loc["SUI-USD", "website"] == "https://sui.org"
    assert frame.loc["BTC-USD", "website"] == "https://bitcoin.org"
    assert not frame.index.str.startswith("DEAD").any()


def test_update_currencies_follows_iso() -> None:
    """Test that a new currency gets the usual pairs and a withdrawn one is removed."""
    rows = []
    for code in ("TND", "KES", "PEN", "GHS", "HRK"):
        for base, quote in (("USD", code), (code, "USD"), ("EUR", code)):
            symbol = f"{quote}=X" if base == "USD" else f"{base}{quote}=X"
            rows.append(
                {
                    "symbol": symbol,
                    "name": f"{base}/{quote}",
                    "base_currency": base,
                    "quote_currency": quote,
                    "summary": "",
                    "exchange": "CCY",
                }
            )
    active = {
        "USD": "US Dollar",
        "EUR": "Euro",
        "TND": "Tunisian Dinar",
        "KES": "Kenyan Shilling",
        "SLE": "Leone",
        "XSU": "Sucre",
    }
    frame, added, gone = markets_model.update_currencies(
        _frame(rows), active, {"HRK", "SLL"}, set(), used={"SLE", "TND", "KES"}
    )
    assert added == ["SLE"] and gone == ["HRK"]
    assert {"SLE=X", "SLEUSD=X", "EURSLE=X"} <= set(frame.index)
    assert not frame.index.str.contains("HRK|XSU").any()
    assert "Leone (SLE)" in frame.loc["SLE=X", "summary"]


def test_update_indices_adds_only_new_symbols() -> None:
    """Test that published indices are added once and never over another class."""
    columns = ["name", "currency", "summary", "category_group", "category"]
    frame = _frame(
        [
            {
                "symbol": "^AEX",
                **dict.fromkeys(columns, "x"),
                "exchange": "AMS",
                "mic": "",
            }
        ]
    )
    published = pd.DataFrame(
        {
            "symbol": ["^AEX", "AAX.AS", "TAKEN.PA"],
            "name": ["AEX", "AEX ALL-SHARE", "Taken"],
            "currency": ["EUR"] * 3,
            "isin": ["", "NL0000249100", ""],
            "exchange": ["AMS", "AMS", "PAR"],
            "mic": ["XAMS", "XAMS", "XPAR"],
        }
    )
    frame, added = markets_model.update_indices(frame, published, {"TAKEN.PA"})
    assert added == ["AAX.AS"]
    assert frame.loc["AAX.AS", "currency"] == "EUR"


def test_inav_categories_follow_their_index() -> None:
    """Test that an iNAV takes its headline index's categories, but not a variant's."""
    columns = ["name", "currency", "summary", "category_group", "category"]
    rows = [
        ("^990100-USD-STRD", "MSCI World", "Equities", "Developed Markets"),
        ("^GSPC", "S&P 500", "Equities", "Large Cap"),
        ("0JHG.DE", "IN.ISH.FS MSCI WORLD USD", "Equities", "Equities"),
        ("0WVA.DE", "IN.ISH.ED.S+P 500 MV EUR", "Equities", "Factors"),
    ]
    rows += [
        (f"X{i}.DE", f"INAV FILLER {i} {cur}", "", "")
        for i, cur in enumerate(["USD", "EUR"] * 200)
    ]
    frame = pd.DataFrame(
        [
            {
                "symbol": s,
                "name": n,
                "currency": "",
                "summary": "",
                "category_group": g,
                "category": c,
                "exchange": "GER",
                "mic": "",
            }
            for s, n, g, c in rows
        ]
    ).set_index("symbol")
    frame, changed = markets_model.align_inav_categories(frame)
    assert changed == ["0JHG.DE"]
    assert frame.loc["0JHG.DE", "category"] == "Developed Markets"
    assert frame.loc["0WVA.DE", "category"] == "Factors"
