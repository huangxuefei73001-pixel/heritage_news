#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import connect, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Heritage News source health monitor")
    parser.add_argument("--check-health", action="store_true")
    parser.add_argument("--check-last-fetch", action="store_true")
    args = parser.parse_args()
    if not args.check_health and not args.check_last_fetch:
        parser.print_help()
        return
    conn = connect()
    init_db(conn)
    rows = conn.execute("SELECT * FROM source_health ORDER BY status, source_name").fetchall()
    if not rows:
        print("No source health rows yet. Run fetch.py --update-db first.")
    for row in rows:
        icon = "✓" if row["status"] == "active" else "⚠"
        last = row["last_successful_fetch"] or "never"
        print(f"{row['source_name']}: {icon} {row['status']} (last fetch: {last}, articles: {row['total_articles']})")
    conn.close()


if __name__ == "__main__":
    main()
