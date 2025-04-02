"ETFs Module"

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


class ETFs(FinanceDatabase):
    """
    An exchange-traded fund (ETF) is a type of pooled investment
    security that operates much like a mutual fund. Typically, ETFs
    will track a particular index, sector, commodity, or other assets,
    but unlike mutual funds, ETFs can be purchased or sold on a stock
    exchange the same way that a regular stock can. An ETF can be structured
    to track anything from the price of an individual commodity to a large
    and diverse collection of securities. ETFs can even be structured to
    track specific investment strategies.

    This class provides information about the ETFs available as well as the
    ability to select specific ETFs based on the category and/or family.
    """

    FILE_NAME = "etfs.bz2"

    def select(
        self,
        category_group: str | None = None,
        category: str | None = None,
        family: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        only_primary_listing: bool = False,
    ) -> pd.DataFrame:
        """
        Retrieve ETF data based on specified criteria.

        This method allows you to retrieve data for specific ETFs based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all ETFs.

        Args:
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.
                Indicates whether category group, category, and family names should be capitalized for matching.
            currency (str, optional):
                Specific currency to retrieve data for. If not provided, returns data for all currencies.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.
            only_primary_listing (bool, optional):
                Whether to only include the primary listing. If False, you will receive
                data for equities from different exchanges. Default is False.

        Returns:
            pd.DataFrame:
                A DataFrame containing ETF data matching the specified input criteria.
        """
        etfs = self.data.copy(deep=True)

        if category_group:
            category_group_lower = category_group.lower()
            options_lower = [
                option.lower()
                for option in self.show_options(selection="category_group")
            ]
            if category_group_lower not in options_lower:
                raise ValueError(
                    f"The category group '{category_group}' is not available in the database. "
                    "Please check the available category groups using the 'show_options' method."
                )
            etfs = etfs[etfs["category_group"].str.lower() == category_group_lower]
        if category:
            category_lower = category.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="category")
            ]
            if category_lower not in options_lower:
                raise ValueError(
                    f"The category '{category}' is not available in the database. "
                    "Please check the available categories using the 'show_options' method."
                )
            etfs = etfs[etfs["category"].str.lower() == category_lower]
        if family:
            family_lower = family.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="family")
            ]
            if family_lower not in options_lower:
                raise ValueError(
                    f"The family '{family}' is not available in the database. "
                    "Please check the available families using the 'show_options' method."
                )
            etfs = etfs[etfs["family"].str.lower() == family_lower]
        if currency:
            currency_lower = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency_lower not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'show_options' method."
                )
            etfs = etfs[etfs["currency"].str.lower() == currency_lower]
        if exchange:
            exchange_lower = exchange.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            if exchange_lower not in options_lower:
                raise ValueError(
                    f"The exchange '{exchange}' is not available in the database. "
                    "Please check the available exchanges using the 'show_options' method."
                )
            etfs = etfs[etfs["exchange"].str.lower() == exchange_lower]
        if only_primary_listing:
            only_primary_listings_etfs = etfs[~etfs.index.str.contains(r"\.", na=False)]
            if only_primary_listings_etfs.empty:
                # If no primary listings are found, return all equities
                print(
                    "No primary listings found. Returning all etfs matching your criteria."
                )
            else:
                # If primary listings are found, filter the equities DataFrame.
                etfs = only_primary_listings_etfs

        return FinanceFrame(etfs)

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | None = None,
        category: str | None = None,
        family: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
    ) -> pd.Series:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange", "market".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                "currency", "category_group", "category", "family", "exchange", "market".
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.
            currency (str, optional):
                Specific currency to retrieve data for. If not provided, returns data for all currencies.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.

        Returns:
            pd.Series:
                A series with all options for the specified selection, sorted and without duplicates.
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
        ]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        etfs = self.select(
            category_group=category_group,
            category=category,
            family=family,
            currency=currency,
            exchange=exchange,
            only_primary_listing=False,
        )

        return (
            {
                column: etfs[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else etfs[selection].dropna().sort_values().unique()
        )
