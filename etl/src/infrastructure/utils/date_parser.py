import polars as pl
from typing import List, Dict, Any

def parse_mixed_dates(col_name: str) -> pl.Expr:
    """
    Polars expression to parse dates that might be in different formats.
    """
    return pl.col(col_name).str.to_date(format="%Y-%m-%d", strict=False).fill_null(
        pl.col(col_name).str.to_date(format="%d-%m-%Y", strict=False)
    )
