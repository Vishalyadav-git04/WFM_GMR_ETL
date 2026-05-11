"""
Backfill geo-hierarchy columns (discom, zone, circle, division, subdivision)
on unified_installation_inventory_data using a remediation CSV.

The CSV is produced by report_mi_meters_missing_geo_mapping.py and may then
be enriched externally with the correct mapping values.  Only rows whose
five geo columns are ALL populated in the CSV will be applied.

Safety:
  - Runs in **dry-run** mode by default (no data is written).
  - The UPDATE WHERE clause ensures only DB rows that currently have
    missing geo data are touched.
  - The whole operation runs inside a single transaction; any error
    triggers a full rollback.

Usage (from repo root, with DATABASE_URL in .env):

    # Dry run – shows count of rows that would be updated
    python etl/backfill_geo_mapping.py

    # Execute the backfill
    python etl/backfill_geo_mapping.py --execute

    # Custom CSV path
    python etl/backfill_geo_mapping.py --csv path/to/file.csv --execute
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

# etl/src on path (same pattern as other etl scripts)
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from infrastructure.config.settings import DATABASE_URL, MI_SOURCE_TABLE
from infrastructure.database.setup import get_engine

# ── Constants ────────────────────────────────────────────────────────────

DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "output",
    "MI_meters_missing_geo_mapping .csv",
)

GEO_COLUMNS = ["discom", "zone", "circle", "division", "subdivision"]
TEMP_TABLE = "_tmp_geo_backfill"


# ── Helpers ──────────────────────────────────────────────────────────────

def _missing_geo_predicate(alias: str) -> str:
    """SQL fragment: true when any of the five hierarchy columns is missing."""
    clauses = [
        f"({alias}.{col} IS NULL OR TRIM({alias}.{col}) = '')"
        for col in GEO_COLUMNS
    ]
    return " OR ".join(clauses)


def _load_csv(csv_path: str) -> pd.DataFrame:
    """Read the CSV file and return only rows with complete geo mapping."""
    df = pd.read_csv(csv_path, dtype=str)

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Strip whitespace from meter_serial_number
    df["meter_serial_number"] = df["meter_serial_number"].str.strip()

    # Fill NaN with empty string for geo columns
    for col in GEO_COLUMNS:
        df[col] = df[col].fillna("").str.strip()

    # Keep only rows where ALL five geo columns are non-empty
    mask = pd.Series(True, index=df.index)
    for col in GEO_COLUMNS:
        mask = mask & (df[col] != "")

    df_filtered = df.loc[mask, ["meter_serial_number"] + GEO_COLUMNS].copy()
    return df_filtered


def _count_missing_geo(conn) -> int:
    """Count distinct meters with missing geo mapping in the source table."""
    sql = text(f"""
        SELECT COUNT(DISTINCT TRIM(meterserialnumber))::bigint
        FROM {MI_SOURCE_TABLE}
        WHERE meterserialnumber IS NOT NULL
          AND TRIM(meterserialnumber) <> ''
          AND ({_missing_geo_predicate(MI_SOURCE_TABLE)})
    """)
    return int(conn.execute(sql).scalar_one())


# ── Main logic ───────────────────────────────────────────────────────────

def run(csv_path: str, execute: bool) -> dict:
    """
    Perform the backfill.

    Returns a dict with stats:
        loaded, filtered, would_update, updated,
        missing_before, missing_after
    """
    engine = get_engine()
    stats: dict = {}

    # ── 1. Load CSV ──────────────────────────────────────────────────────
    raw_df = pd.read_csv(csv_path, dtype=str)
    stats["loaded"] = len(raw_df)

    df = _load_csv(csv_path)
    stats["filtered"] = len(df)

    if df.empty:
        print("[WARN] No rows with complete geo mapping found in CSV. Nothing to do.")
        return stats

    print(f"  CSV loaded : {stats['loaded']:,} rows total")
    print(f"  With mapping: {stats['filtered']:,} rows (will be used for backfill)")

    # ── 2. Upload to temp table ──────────────────────────────────────────
    with engine.begin() as conn:
        stats["missing_before"] = _count_missing_geo(conn)
        print(f"  Missing geo in DB (before): {stats['missing_before']:,}")

        # Upload filtered data to temp table
        df.to_sql(TEMP_TABLE, conn, if_exists="replace", index=False, method="multi")
        print(f"  Temp table '{TEMP_TABLE}' created with {len(df):,} rows")

        # ── 3. Count how many would be updated ───────────────────────────
        count_sql = text(f"""
            SELECT COUNT(*)::bigint
            FROM {MI_SOURCE_TABLE} AS t
            INNER JOIN {TEMP_TABLE} AS s
                ON TRIM(t.meterserialnumber) = s.meter_serial_number
            WHERE ({_missing_geo_predicate('t')})
        """)
        would_update = int(conn.execute(count_sql).scalar_one())
        stats["would_update"] = would_update
        print(f"  Rows that would be updated: {would_update:,}")

        if not execute:
            # Dry run – drop temp table and rollback
            conn.execute(text(f"DROP TABLE IF EXISTS {TEMP_TABLE}"))
            stats["updated"] = 0
            print("\n  [DRY RUN] No changes committed.")
            print("  Re-run with --execute to apply.\n")
            return stats

        # ── 4. Execute UPDATE ────────────────────────────────────────────
        update_sql = text(f"""
            UPDATE {MI_SOURCE_TABLE} AS t
            SET discom      = s.discom,
                zone        = s.zone,
                circle      = s.circle,
                division    = s.division,
                subdivision = s.subdivision
            FROM {TEMP_TABLE} AS s
            WHERE TRIM(t.meterserialnumber) = s.meter_serial_number
              AND ({_missing_geo_predicate('t')})
        """)
        result = conn.execute(update_sql)
        stats["updated"] = result.rowcount
        print(f"  [OK] Rows updated: {result.rowcount:,}")

        # ── 5. Drop temp table ───────────────────────────────────────────
        conn.execute(text(f"DROP TABLE IF EXISTS {TEMP_TABLE}"))

        # ── 6. Post-update validation ────────────────────────────────────
        stats["missing_after"] = _count_missing_geo(conn)
        print(f"  Missing geo in DB (after) : {stats['missing_after']:,}")
        print(
            f"  Reduction: {stats['missing_before']:,} -> {stats['missing_after']:,} "
            f"({stats['missing_before'] - stats['missing_after']:,} fixed)"
        )

    return stats


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill geo-hierarchy columns on "
            f"{MI_SOURCE_TABLE} from a remediation CSV."
        )
    )
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV,
        help="Path to the CSV with corrected geo mapping (default: data/output/MI_meters_missing_geo_mapping .csv)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually apply the updates. Without this flag the script runs in dry-run mode.",
    )
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    if not os.path.isfile(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  Geo Mapping Backfill – {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"  CSV   : {csv_path}")
    print(f"  Table : {MI_SOURCE_TABLE}")
    print(f"{'=' * 60}\n")

    run(csv_path, execute=args.execute)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
