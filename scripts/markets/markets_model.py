"""Markets Model"""

__docformat__ = "google"

import re
from collections.abc import Callable

import pandas as pd

# A quote currency at least this share of the coins trade in is used for new coins.
COIN_QUOTE_SHARE = 0.9
# A pair at least this share of the currencies have is added for a new currency.
CURRENCY_PAIR_SHARE = 0.8
# New coins whose homepage is looked up per run (CoinGecko's free rate limit).
MAX_WEBSITE_LOOKUPS = 40
# A removal touching more than this share of a file is treated as a source problem.
MAX_REMOVED_SHARE = 0.4
COIN_TICKER = re.compile(r"^[A-Z0-9]{1,12}$")
# Names of ETF iNAVs (indicative net asset values), as Xetra and other venues publish them.
INAV_NAME = r"^(?:INAV|IN\.|I\.)|\bINAV\b"
# A last word of at least this share of iNAV names is a generic ending (currency, class).
INAV_ENDING_SHARE = 0.003
# A headline index's rows must agree on categories for at least this share.
CATEGORY_AGREEMENT = 0.8


def update_cryptos(
    frame: pd.DataFrame,
    coins: pd.DataFrame,
    tickers: set[str],
    website: Callable[[str], str],
    taken: set[str],
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """
    Add the pairs of coins with a top market cap and drop coins no longer listed anywhere.

    Args:
        frame (pd.DataFrame): The cryptos file.
        coins (pd.DataFrame): CoinGecko's coins by market cap.
        tickers (set[str]): The tickers of every coin CoinGecko lists.
        website (Callable[[str], str]): CoinGecko id -> homepage.
        taken (set[str]): Symbols of the other asset classes.

    Returns:
        tuple[pd.DataFrame, list[str], list[str]]: The file, added and removed coins.
    """
    pairs = frame.groupby("cryptocurrency")["currency"].apply(set)
    shares = pd.Series([q for quotes in pairs for q in quotes]).value_counts() / len(
        pairs
    )
    quotes = sorted(shares[shares >= COIN_QUOTE_SHARE].index)
    names = frame.groupby("cryptocurrency")["name"].first().str.rsplit(" ", n=1).str[0]

    added, rows, lookups = [], [], 0
    for coin in coins.itertuples():
        ticker = coin.symbol
        # Tokenized funds and tickers outside the symbol convention are left out.
        if not COIN_TICKER.match(ticker) or re.search(r"\bfund\b", coin.name, re.I):
            continue
        # A ticker belongs to one coin: the one already in the file, else the largest.
        if ticker in added or (
            ticker in names.index and names[ticker].lower() != coin.name.lower()
        ):
            continue
        missing = [
            q for q in quotes if f"{ticker}-{q}" not in frame.index and q != ticker
        ]
        missing = [q for q in missing if f"{ticker}-{q}" not in taken]
        if not missing:
            continue
        known = frame[frame.cryptocurrency == ticker]
        if len(known):
            site, summary = known.website.iloc[0], known.summary.iloc[0]
        else:
            site = website(coin.id) if lookups < MAX_WEBSITE_LOOKUPS else ""
            lookups += 1
            summary = f"{coin.name} ({ticker}) is a cryptocurrency."
        for quote in missing:
            rows.append(
                pd.Series(
                    {
                        "name": f"{coin.name} {quote}",
                        "cryptocurrency": ticker,
                        "currency": quote,
                        "summary": summary,
                        "exchange": "CCC",
                        "website": site,
                    },
                    name=f"{ticker}-{quote}",
                )
            )
        added.append(ticker)

    # Coins added before without a homepage get one, within the same lookup budget.
    ids = dict(zip(coins.symbol, coins.id))
    frame = frame.copy()
    for ticker in sorted(set(frame.cryptocurrency[frame.website == ""])):
        if ticker in ids and lookups < MAX_WEBSITE_LOOKUPS:
            lookups += 1
            site = website(ids[ticker])
            if site:
                frame.loc[frame.cryptocurrency == ticker, "website"] = site

    # A coin whose ticker CoinGecko no longer lists at all has stopped trading.
    base = frame.cryptocurrency.str.replace(r"\d+$", "", regex=True)
    gone = sorted(set(frame.cryptocurrency[~base.isin(tickers)]))
    if len(gone) > MAX_REMOVED_SHARE * len(pairs):
        print(f"  ! {len(gone)} coins to remove looks implausible; removing none")
        gone = []
    frame = frame[~frame.cryptocurrency.isin(gone)]
    if rows:
        frame = pd.concat([frame, pd.DataFrame(rows)[frame.columns]])
    return frame, added, gone


def describe_pair(base: str, quote: str, names: dict[str, str]) -> str:
    """
    A factual summary of a currency pair.

    Args:
        base (str): The base currency code.
        quote (str): The quote currency code.
        names (dict[str, str]): Code -> currency name.

    Returns:
        str: The summary.
    """
    return (
        f"The exchange rate between the {names.get(base, base)} ({base}) and the "
        f"{names.get(quote, quote)} ({quote}). It reflects how many {quote} can be "
        f"purchased with one {base}."
    )


def update_currencies(
    frame: pd.DataFrame,
    active: dict[str, str],
    withdrawn: set[str],
    taken: set[str],
    used: set[str] | None = None,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """
    Add the pairs of new ISO 4217 currencies and drop those of withdrawn currencies.

    Args:
        frame (pd.DataFrame): The currencies file.
        active (dict[str, str]): Active ISO currency code -> name.
        withdrawn (set[str]): Withdrawn ISO currency codes.
        taken (set[str]): Symbols of the other asset classes.
        used (set[str] | None): Codes countries use as their currency; None allows all.

    Returns:
        tuple[pd.DataFrame, list[str], list[str]]: The file, added and removed currencies.
    """
    codes = (set(frame.base_currency) | set(frame.quote_currency)) - {"USD"}
    # Which pairs a currency usually has: against which currencies, in which direction.
    shares: dict[tuple[str, str], int] = {}
    for base, quote in zip(frame.base_currency, frame.quote_currency):
        if quote in codes and base in active:
            shares[(base, "C")] = shares.get((base, "C"), 0) + 1
        if base in codes and quote in active:
            shares[("C", quote)] = shares.get(("C", quote), 0) + 1
    usual = [
        pair for pair, n in shares.items() if n >= CURRENCY_PAIR_SHARE * len(codes)
    ]

    gone = sorted(code for code in codes & withdrawn)
    if len(gone) > 10:
        print(f"  ! {len(gone)} withdrawn currencies looks implausible; removing none")
        gone = []
    frame = frame[~frame.base_currency.isin(gone) & ~frame.quote_currency.isin(gone)]

    names = {**active, "USD": active.get("USD", "US Dollar")}
    added, rows = [], []
    for code in sorted(set(active) - codes - {"USD"} - withdrawn):
        if used is not None and code not in used:
            continue
        for pattern in usual:
            base, quote = (code if part == "C" else part for part in pattern)
            symbol = f"{quote}=X" if base == "USD" else f"{base}{quote}=X"
            if symbol in frame.index or symbol in taken:
                continue
            rows.append(
                pd.Series(
                    {
                        "name": f"{base}/{quote}",
                        "base_currency": base,
                        "quote_currency": quote,
                        "summary": describe_pair(base, quote, names),
                        "exchange": "CCY",
                    },
                    name=symbol,
                )
            )
        added.append(code)
    if rows:
        frame = pd.concat([frame, pd.DataFrame(rows)[frame.columns]])
    return frame, added, gone


def update_indices(
    frame: pd.DataFrame, published: pd.DataFrame, taken: set[str]
) -> tuple[pd.DataFrame, list[str]]:
    """
    Add the indices an exchange publishes that the file does not have yet.

    Args:
        frame (pd.DataFrame): The indices file.
        published (pd.DataFrame): symbol, name, currency, exchange and mic per index.
        taken (set[str]): Symbols of the other asset classes.

    Returns:
        tuple[pd.DataFrame, list[str]]: The file and the added symbols.
    """
    new = published[
        ~published.symbol.isin(frame.index) & ~published.symbol.isin(taken)
    ].drop_duplicates("symbol")
    if new.empty:
        return frame, []
    rows = pd.DataFrame(
        {
            "name": new.name.to_numpy(),
            "currency": new.currency.to_numpy(),
            "summary": [
                f"{name} is an index published by Euronext ({mic}), calculated in "
                f"{currency}."
                for name, mic, currency in zip(new.name, new.mic, new.currency)
            ],
            "category_group": "",
            "category": "",
            "exchange": new.exchange.to_numpy(),
            "mic": new.mic.to_numpy(),
        },
        index=new.symbol.to_numpy(),
    )
    return pd.concat([frame, rows[frame.columns]]), list(new.symbol)


def align_inav_categories(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Give an ETF iNAV the categories of the headline index it tracks: its name, without
    the endings many iNAV names share (currencies, share classes), ends with that index's
    name ('IN.ISH.FS MSCI WORLD EUR' takes MSCI World's), and the index's rows agree.

    Args:
        frame (pd.DataFrame): The indices file.

    Returns:
        tuple[pd.DataFrame, list[str]]: The file and the changed symbols.
    """
    words = lambda name: re.findall(r"[a-z0-9]+", name.lower())  # noqa: E731
    inav = frame["name"].str.contains(INAV_NAME, case=False, regex=True)
    inav &= ~frame.index.str.startswith("^")
    endings = pd.Series([w[-1] for w in map(words, frame["name"][inav]) if w])
    shares = endings.value_counts() / max(int(inav.sum()), 1)
    generic = set(shares[shares >= INAV_ENDING_SHARE].index)
    headline = frame[
        frame.index.str.startswith("^")
        & (frame["category"] != "")
        & (frame["category_group"] != "")
    ]
    categories: dict[str, list[tuple[str, str]]] = {}
    for name, group, category in zip(
        headline["name"], headline["category_group"], headline["category"], strict=True
    ):
        key = " ".join(words(name))
        if len(key.split()) >= 2:
            categories.setdefault(key, []).append((group, category))
    frame, changed = frame.copy(), []
    for symbol in frame.index[inav]:
        name = words(frame.loc[symbol, "name"])
        while name and name[-1] in generic:
            name = name[:-1]
        for start in range(len(name)):
            options = categories.get(" ".join(name[start:]))
            if not options:
                continue
            best = max(set(options), key=options.count)
            agree = options.count(best) >= CATEGORY_AGREEMENT * len(options)
            current = (
                frame.loc[symbol, "category_group"],
                frame.loc[symbol, "category"],
            )
            if agree and current != best:
                frame.loc[symbol, ["category_group", "category"]] = list(best)
                changed.append(symbol)
            break
    return frame, changed
