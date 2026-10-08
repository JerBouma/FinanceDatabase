"""DataFrame Model Tests"""

import pandas as pd
import polars as pl

from financedatabase.utilities import dataframe_model

CSV = "symbol,name,sector,delisted\nAAA,Alpha,Energy,False\nNA,Nano Labs,,False\nOLD,Old Co,Energy,True\n"


def test_convert_to_pandas_matches_the_csv_reader() -> None:
    """Test that convert_to_pandas matches pandas' CSV reader."""
    frame = pl.read_csv(CSV.encode(), infer_schema=False).with_columns(
        pl.col("delisted").eq("True")
    )
    result = dataframe_model.convert_to_pandas(frame)
    expected = pd.read_csv(
        pd.io.common.StringIO(CSV), index_col=0, keep_default_na=False, na_values=[""]
    )
    pd.testing.assert_frame_equal(result, expected)
    assert dataframe_model.convert_from_pandas(result).equals(frame)
