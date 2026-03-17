"""
Extract and normalize O&M complaint data from 6 CSV files.
"""

import polars as pl
from config import OM_FILES
from utils.date_parser import parse_om_dates
from utils.logger import get_logger

log = get_logger("extract.om_complaints")


def _prep_file(file_path: str, category: str, is_closed: bool) -> pl.LazyFrame:
    """Load a single O&M CSV, normalize columns, and tag with category."""
    df = pl.scan_csv(str(file_path), infer_schema_length=10000, ignore_errors=True)

    # Normalize column names
    rename_map = {}
    schema_names = df.collect_schema().names()
    if "FeederName" in schema_names:
        rename_map["FeederName"] = "Feeder"
    if "DTRName" in schema_names:
        rename_map["DTRName"] = "DTR"
    if "complaintBy" in schema_names:
        rename_map["complaintBy"] = "ComplaintBy"

    if rename_map:
        df = df.rename(rename_map)

    # Add missing columns for non-closed files
    if not is_closed:
        df = df.with_columns(
            pl.lit(None).cast(pl.Utf8).alias("ClosedDate"),
            pl.lit(None).cast(pl.Utf8).alias("NewSmartMeterNumber"),
            pl.lit(None).cast(pl.Utf8).alias("ComplaintCategory"),
        )

    # Parse dates and add category tag
    df = df.with_columns(
        Parsed_CreatedDate=parse_om_dates("CreatedDate"),
        Parsed_ClosedDate=parse_om_dates("ClosedDate") if is_closed else pl.lit(None).cast(pl.Datetime),
        OM_Category=pl.lit(category),
    )

    return df


def extract_om_complaints() -> pl.LazyFrame:
    """Load, normalize, and concatenate all 6 O&M complaint CSVs."""
    log.info("Loading O&M complaint files …")

    frames = []
    for category, paths in OM_FILES.items():
        frames.append(_prep_file(paths["closed"], category, is_closed=True))
        frames.append(_prep_file(paths["open"], category, is_closed=False))

    # Find common columns, then concatenate
    common_cols: set[str] | None = None
    for f in frames:
        cols = set(f.collect_schema().names())
        common_cols = cols if common_cols is None else common_cols.intersection(cols)

    col_list = list(common_cols or [])
    df_master = pl.concat([f.select(col_list) for f in frames])

    # Add time-dimension columns
    df_master = df_master.with_columns(
        Created_Day=pl.col("Parsed_CreatedDate").dt.date(),
        Created_Week=pl.col("Parsed_CreatedDate").dt.truncate("1w").dt.date(),
        Created_Month=pl.col("Parsed_CreatedDate").dt.to_string("%b %Y"),
        Closed_Day=pl.col("Parsed_ClosedDate").dt.date(),
        Closed_Week=pl.col("Parsed_ClosedDate").dt.truncate("1w").dt.date(),
        Closed_Month=pl.col("Parsed_ClosedDate").dt.to_string("%b %Y"),
    )

    log.info("O&M LazyFrame ready (%d sources)", len(frames))
    return df_master
