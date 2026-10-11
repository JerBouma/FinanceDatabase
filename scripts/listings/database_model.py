"""Database Model"""

__docformat__ = "google"

import glob
import os
from collections.abc import Callable

import pandas as pd

from scripts.listings.helpers import (
    get_symbol_key,
    normalize_name,
    read_csv_text,
    write_csv,
)


class Database:
    """
    The per-exchange equities/ETF files plus the symbols of every asset class.
    """

    def __init__(self, root: str) -> None:
        """
        Hold the database files that are read, changed or added during the update.
        """
        self.root = root
        self.frames: dict[str, pd.DataFrame] = {}
        self.added: dict[str, list[pd.Series]] = {}
        self.cache: dict[tuple[str, str], dict] = {}
        self.symbols: set[str] = set()
        for path in glob.glob(f"{root}/*/*.csv") + glob.glob(f"{root}/*.csv"):
            self.symbols |= set(
                pd.read_csv(path, usecols=[0], dtype=str, keep_default_na=False).iloc[
                    :, 0
                ]
            )
        self.columns = {
            kind: read_csv_text(
                sorted(glob.glob(f"{root}/{kind}/*.csv"))[0]
            ).columns.tolist()
            for kind in ("equities", "etfs")
        }

    def get_frame(self, kind: str, file: str) -> pd.DataFrame:
        """
        Get an exchange file as a text DataFrame, read once and then kept.
        """
        path = self.get_path(kind, file)
        if path not in self.frames:
            columns = self.columns[kind]
            empty = pd.DataFrame(columns=columns, dtype=str).rename_axis("symbol")
            self.frames[path] = read_csv_text(path) if os.path.exists(path) else empty
            self.added[path] = []
        return self.frames[path]

    def get_path(self, kind: str, file: str) -> str:
        """
        Get the CSV path of an exchange file.
        """
        return f"{self.root}/{kind}/{file}.csv"

    def get_symbol_keys(self, kind: str, file: str) -> dict[str, str]:
        """
        Separator-free symbol -> symbol for an exchange file (cached).
        """
        if (kind + "keys", file) not in self.cache:
            frame = self.get_frame(kind, file)
            self.cache[(kind + "keys", file)] = {
                get_symbol_key(s): s for s in frame.index
            }
        return self.cache[(kind + "keys", file)]

    def get_live_by_name(self, kind: str, file: str) -> dict[str, list[str]]:
        """
        Normalised name -> live symbols for an exchange file (cached).
        """
        if (kind + "names", file) not in self.cache:
            frame = self.get_frame(kind, file)
            names: dict[str, list[str]] = {}
            for symbol, name in frame.loc[frame["delisted"] == "False", "name"].items():
                names.setdefault(normalize_name(name), []).append(symbol)
            self.cache[(kind + "names", file)] = names
        return self.cache[(kind + "names", file)]

    def get_defaults(self, kind: str, file: str) -> dict[str, str]:
        """
        mic / market of an exchange file, from its existing rows.
        """
        frame = self.get_frame(kind, file)
        mode = lambda col: (  # noqa: E731
            frame[col][frame[col] != ""].mode().iloc[0]
            if col in frame and (frame[col] != "").any()
            else ""
        )
        return {"mic": mode("mic"), "market": mode("market")}

    def get_etf_families(self) -> Callable[[str], str]:
        """
        Issuer family from the opening words of an ETF name.
        Uses the first two words, else the first, when nearly all existing ETFs agree.
        """
        frames = [
            read_csv_text(p)[["name", "family"]]
            for p in glob.glob(f"{self.root}/etfs/*.csv")
        ]
        etfs = pd.concat(frames)
        etfs = etfs[etfs.family != ""]
        tables = []
        for words, minimum in ((2, 5), (1, 10)):
            key = lambda name, n=words: " ".join(name.lower().split()[:n])  # noqa: E731
            table = {}
            for prefix, group in etfs.groupby(etfs.name.map(key)):
                counts = group.family.value_counts()
                share = counts.iloc[0] / len(group)
                unanimous = words == 1 and len(group) >= 3 and share == 1
                if (len(group) >= minimum and share >= 0.95) or unanimous:
                    table[prefix] = counts.index[0]
            tables.append((key, table))

        def get_family(name: str) -> str:
            for key, table in tables:
                if key(name) in table:
                    return table[key(name)]
            return ""

        return get_family

    def get_etfs_by_isin(self) -> dict[str, dict[str, str]]:
        """
        ISIN -> name, categories and family of its existing ETF listings.
        """
        if "etf_isins" not in self.cache:
            frames = [
                read_csv_text(p)[
                    ["name", "category_group", "category", "family", "isin"]
                ]
                for p in glob.glob(f"{self.root}/etfs/*.csv")
            ]
            etfs = pd.concat(frames)
            etfs = etfs[(etfs["isin"].str.len() == 12) & (etfs["name"] != "")]
            cased = etfs["name"].str.contains("[a-z]")
            known = {}
            for isin, group in etfs.groupby("isin"):
                pick = lambda column, rows=group: (  # noqa: E731
                    rows[column][rows[column] != ""].mode().iloc[0]
                    if (rows[column] != "").any()
                    else ""
                )
                names = (
                    group[cased.loc[group.index]]
                    if cased.loc[group.index].any()
                    else group
                )
                known[isin] = {
                    "name": pick("name", names),
                    "category_group": pick("category_group"),
                    "category": pick("category"),
                    "family": pick("family"),
                }
            self.cache["etf_isins"] = known
        return self.cache["etf_isins"]

    def get_merged_frames(self, kind: str) -> list[pd.DataFrame]:
        """
        Every file of an asset class with the rows added this run merged in, so rules over
        the whole class see them; the files are then written as changed.

        Args:
            kind (str): The asset class folder, e.g. "etfs".

        Returns:
            list[pd.DataFrame]: The files.
        """
        for path in sorted(glob.glob(f"{self.root}/{kind}/*.csv")):
            self.get_frame(kind, os.path.basename(path)[:-4])
        frames = []
        for path in [p for p in self.frames if f"/{kind}/" in p]:
            original = self.frames[path]
            if self.added[path]:
                merged = pd.concat(
                    [original, pd.DataFrame(self.added[path])[original.columns]]
                )
                if original.index.is_monotonic_increasing:
                    merged = merged.sort_index()
                merged.attrs["changed"] = True
                self.frames[path], self.added[path] = merged, []
            frames.append(self.frames[path])
        return frames

    def write(self) -> None:
        """
        Write back only the files that changed, keeping the rest byte-identical.
        """
        for path, original in self.frames.items():
            if not self.added[path] and not original.attrs.get("changed"):
                continue
            out = original
            if self.added[path]:
                new_rows = pd.DataFrame(self.added[path])[original.columns]
                out = pd.concat([original, new_rows])
            # Equities files are kept sorted; ETF files only when they already were.
            if "/equities/" in path or original.index.is_monotonic_increasing:
                out = out.sort_index()
            out.index.name = "symbol"
            write_csv(out, path)
