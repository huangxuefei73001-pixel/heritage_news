#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3

from common import DB_PATH, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Show sources with failed or empty recent fetches")
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    rows = conn.execute(
        "SELECT * FROM source_health WHERE status != 'active' OR date(last_check)=? AND total_articles=0 ORDER BY source_name",
        (args.date,),
    ).fetchall()
    for row in rows:
        print(f"{row['source_name']}: {row['status']} last_check={row['last_check']} failures={row['failure_count_24h']}")
    conn.close()


if __name__ == "__main__":
    main()
