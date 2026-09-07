"""Restore backend/nigrani.db from backend/nigrani.db.gz.

Streams decompression via gzip and shutil.copyfileobj to stay well within
Render's 512 MB memory limit. Skips decompression if nigrani.db exists and is
newer than nigrani.db.gz. Verifies that the restored database contains cases.
"""

from __future__ import annotations

import gzip
import shutil
import sqlite3
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_GZ_PATH = BACKEND_DIR / "nigrani.db.gz"
DB_PATH = BACKEND_DIR / "nigrani.db"


def restore(source_gz: Path = DB_GZ_PATH, target_db: Path = DB_PATH) -> int:
    if not source_gz.exists():
        print(f"Error: Compressed database artifact not found at {source_gz}", file=sys.stderr)
        sys.exit(1)

    if target_db.exists() and target_db.stat().st_mtime >= source_gz.stat().st_mtime:
        print(f"Skipping restore: {target_db.name} exists and is newer than {source_gz.name}.")
    else:
        print(f"Restoring {target_db.name} from {source_gz.name}...")
        temp_target = target_db.with_suffix(".db.tmp")
        try:
            with gzip.open(source_gz, "rb") as gz_in, open(temp_target, "wb") as db_out:
                shutil.copyfileobj(gz_in, db_out, length=1024 * 1024)
            temp_target.replace(target_db)
            print(f"Successfully decompressed {source_gz.name} -> {target_db.name}")
        except Exception as err:
            if temp_target.exists():
                temp_target.unlink()
            print(f"Error during decompression: {err}", file=sys.stderr)
            sys.exit(1)

    # Verify restored database integrity
    try:
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM cases")
        case_count = cursor.fetchone()[0]
        conn.close()
    except Exception as err:
        print(f"Error verifying restored database: {err}", file=sys.stderr)
        sys.exit(1)

    if case_count == 0:
        print("Error: Restored database contains 0 cases (awaiting_build state).", file=sys.stderr)
        sys.exit(1)

    print(f"Database verification passed: {case_count:,} cases present.")
    return case_count


def main() -> None:
    restore()


if __name__ == "__main__":
    main()
