"""
Apply pending database migrations.
"""

import os
import sys
from pathlib import Path

# Add etl/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "etl" / "src"))

from infrastructure.database.setup import get_engine
from sqlalchemy import text

MIGRATIONS_DIR = Path(__file__).resolve().parent / "backend" / "migrations"


def run_migrations():
    engine = get_engine()
    migration_files = sorted(MIGRATIONS_DIR.glob("migrate_*.sql"))

    print(f"Found {len(migration_files)} migration files.")
    applied = 0

    with engine.begin() as conn:
        for mig_file in migration_files:
            sql = mig_file.read_text()
            try:
                conn.execute(text(sql))
                print(f" Applied: {mig_file.name}")
                applied += 1
            except Exception as e:
                print(f" Failed: {mig_file.name} — {e}")

    print(f"\nDone. {applied}/{len(migration_files)} migrations applied.")


if __name__ == "__main__":
    run_migrations()
