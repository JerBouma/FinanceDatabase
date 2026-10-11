"""FinanceFrame Model"""

__docformat__ = "google"

from typing import Any

import pandas as pd

from financedatabase.utilities import logger_model

logger = logger_model.get_logger()


class FinanceFrame(pd.DataFrame):
    """
    A pandas DataFrame that converts its tickers to a Finance Toolkit object.
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
        Convert the FinanceFrame to a Finance Toolkit object for its tickers.

        Args:
            api_key (str | None, optional): API key, see https://www.jeroenbouma.com/fmp.
            start_date (str | None, optional): Start date (YYYY-MM-DD), 10 years ago if None.
            end_date (str | None, optional): End date (YYYY-MM-DD), today if None.
            quarterly (bool, optional): Quarterly statements. Defaults to False.
            use_cached_data (bool | str, optional): Cached data, or its path. Defaults to False.
            risk_free_rate (str, optional): 13w, 5y, 10y or 30y. Defaults to "10y".
            benchmark_ticker (str | None, optional): Benchmark ticker. Defaults to "SPY".
            enforce_source (str | None, optional): Data source, None for both.
            convert_currency (bool | None, optional): Convert statement currencies.
            intraday_period (str | None, optional): Intraday period such as 1min or 1hour.
            rounding (int | None, optional): Decimal places. Defaults to 4.
            remove_invalid_tickers (bool, optional): Remove invalid tickers. Defaults to False.
            sleep_timer (bool | None, optional): Sleep when the rate limit is reached.
            progress_bar (bool, optional): Show a progress bar. Defaults to True.

        Returns:
            Toolkit: Finance Toolkit object with data for the tickers in this DataFrame.

        Raises:
            ImportError: If the Finance Toolkit is not installed.
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
