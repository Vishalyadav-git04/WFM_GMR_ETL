"""
Canonical date parser – single source of truth for all mixed-format date columns.
"""

import polars as pl


def parse_mixed_dates(column_name: str) -> pl.Expr:
    """
    Parse a string column that may contain dates in several formats.
    Returns a Date (not Datetime) expression.

    Supported formats (in priority order):
        DD-MM-YY HH:MM      e.g. 17-12-25 18:09
        MM/DD/YYYY HH:MM    e.g. 6/1/2026 16:59
        MM/DD/YYYY           e.g. 4/18/2025
        DD/MM/YYYY HH:MM
        DD-MM-YYYY HH:MM
        YYYY-MM-DD HH:MM:SS
    """
    clean = pl.col(column_name).cast(pl.Utf8).str.strip_chars()

    return pl.coalesce(
        clean.str.strptime(pl.Datetime, "%d-%m-%y %H:%M", strict=False),
        clean.str.strptime(pl.Datetime, "%m/%d/%Y %H:%M", strict=False),
        clean.str.strptime(pl.Datetime, "%m/%d/%Y", strict=False),
        clean.str.strptime(pl.Datetime, "%d/%m/%Y %H:%M", strict=False),
        clean.str.strptime(pl.Datetime, "%d-%m-%Y %H:%M", strict=False),
        clean.str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
        clean.str.strptime(pl.Datetime, "%Y-%m-%d", strict=False),
    ).dt.date()


def parse_om_dates(column_name: str) -> pl.Expr:
    """
    Parse O&M complaint date columns (typically MM/DD/YYYY HH:MM:SS).
    Returns a Datetime expression (we need time precision for resolution calcs).
    """
    return pl.coalesce(
        pl.col(column_name).str.strptime(pl.Datetime, "%m/%d/%Y %H:%M:%S", strict=False),
        pl.col(column_name).str.strptime(pl.Datetime, "%m/%d/%Y %H:%M", strict=False),
        pl.col(column_name).str.strptime(pl.Datetime, "%m/%d/%Y", strict=False),
        pl.col(column_name).str.strptime(pl.Datetime, "%d/%m/%y %H:%M:%S", strict=False),
        pl.col(column_name).str.strptime(pl.Datetime, "%d-%m-%Y %H:%M:%S", strict=False),
        pl.col(column_name).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
    )
