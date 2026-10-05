"""FinanceFrame Model"""

__docformat__ = "google"

from typing import Any

import pandas as pd

from financedatabase.utilities import logger_model

logger = logger_model.get_logger()


class FinanceFrame(pd.DataFrame):
    """
    Enhanced DataFrame with financial data integration capabilities.

    Extends the pandas DataFrame with additional functionality for
    financial analysis, particularly for connecting with the Finance
    Toolkit using tickers obtained from the Finance Database.
    """

    def to_toolkit(
        self,
        api_key: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        quarterly: bool = False,
        use_cached_data: bool | str = False,
        risk_free_rate: str = "10y",
        benchmark_ticker: str | None = "SPY",
        enforce_source: str | None = None,
        convert_currency: bool | None = None,
        intraday_period: str | None = None,
        rounding: int | None = 4,
        remove_invalid_tickers: bool = False,
        sleep_timer: bool | None = None,
        progress_bar: bool = True,
    ) -> Any:
        """
        Convert the FinanceFrame to a Finance Toolkit object.

        Creates a Finance Toolkit object using the tickers in this DataFrame,
        providing access to fundamental and historical data, ratios, metrics,
        models, and technical indicators.

        Args:
            api_key (str | None, optional): API key from FinancialModelingPrep.
                Obtain one at: https://www.jeroenbouma.com/fmp. Defaults to None.
            start_date (str | None, optional): Start date for data collection (YYYY-MM-DD).
                Defaults to 10 years before the current date.
            end_date (str | None, optional): End date for data collection (YYYY-MM-DD).
                Defaults to the current date.
            quarterly (bool, optional): Whether to collect quarterly financial statements.
                Defaults to False (yearly statements).
            use_cached_data (bool | str, optional): Whether to use previously cached data.
                Can be a boolean or a string path. Defaults to False.
            risk_free_rate (str, optional): Risk-free rate to use (13w, 5y, 10y, 30y).
                Based on US Treasury Yields. Defaults to "10y".
            benchmark_ticker (str | None, optional): Ticker for benchmark comparisons.
                Defaults to "SPY" (S&P 500).
            enforce_source (str | None, optional): Source for the data ("FinancialModelingPrep"
                or "YahooFinance"). Defaults to None (both are used).
            convert_currency (bool | None, optional): Whether to convert financial statement
                currencies to match historical data. Defaults to None (auto-determined).
            intraday_period (str | None, optional): Time period for intraday data (1min, 5min,
                15min, 30min, 1hour). Defaults to None.
            rounding (int | None, optional): Number of decimal places for results. Defaults to 4.
            remove_invalid_tickers (bool, optional): Whether to remove invalid tickers.
                Defaults to False.
            sleep_timer (bool | None, optional): Whether to use a sleep timer when the rate
                limit is reached. Defaults to None (auto-determined).
            progress_bar (bool, optional): Whether to show a progress bar for 10+ tickers.
                Defaults to True.

        Returns:
            Toolkit: Finance Toolkit object with data for the tickers in this DataFrame.

        Raises:
            ImportError: If the Finance Toolkit is not installed.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()

        toolkit = equities.select(country="Netherlands", sector="Financials").to_toolkit(
            api_key="FINANCIAL_MODELING_PREP_KEY"
        )

        toolkit.ratios.get_profitability_ratios()
        ```
        """
        try:
            from financetoolkit import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
                Toolkit,
            )
        except ImportError as exc:
            raise ImportError(
                "To use the 'to_toolkit' functionality, it requires installation of the FinanceToolkit "
                "Please use: \033[1m pip install financetoolkit -U \033[0m"
            ) from exc
        if api_key is None:
            logger.info(
                "The parameter api_key is not set. Therefore, using Yahoo Finance as the source which "
                "is limited to 5 years of fundamental data. Consider obtaining a key with the following "
                "link: https://www.jeroenbouma.com/fmp"
                "\nYou can get 15% off by using the above affiliate link to "
                "get access to 30+ years of (quarterly) data which also supports the project."
            )

        symbols = self[self.index.notna()].index.to_list()

        toolkit = Toolkit(
            tickers=symbols,
            api_key=api_key or "",
            start_date=start_date,
            end_date=end_date,
            quarterly=quarterly,
            use_cached_data=use_cached_data,
            risk_free_rate=risk_free_rate,
            benchmark_ticker=benchmark_ticker,
            enforce_source=enforce_source,
            convert_currency=convert_currency,
            intraday_period=intraday_period,
            rounding=rounding,
            remove_invalid_tickers=remove_invalid_tickers,
            sleep_timer=sleep_timer,
            progress_bar=progress_bar,
        )

        return toolkit
