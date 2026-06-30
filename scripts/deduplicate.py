#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re

from common import connect, init_db


def norm(title: str) -> str:
    return re.sub(r"\W+", "", title.lower())


def cluster_id(title: str, date: str) -> str:
    return "evt_" + hashlib.sha1(f"{date}:{norm(title)}".encode()).hexdigest()[:12]


def update(days: int) -> int:
    conn = connect()
    init_db(conn)
    rows = conn.execute(
        "SELECT id,title_original,date(pub_date) AS d FROM heritage_news WHERE pub_date >= datetime('now', ?) ORDER BY pub_date DESC",
        (f"-{days} days",),
    ).fetchall()
    for row in rows:
        conn.execute("UPDATE heritage_news SET event_cluster_id=? WHERE id=?", (cluster_id(row["title_original"], row["d"]), row["id"]))
    conn.commit()
    conn.close()
    return len(rows)


def test_cluster(term: str, date: str) -> dict:
    conn = connect()
    init_db(conn)
    rows = conn.execute(
        "SELECT id,title_original,source_name,url FROM heritage_news WHERE date(pub_date)=? AND title_original LIKE ?",
        (date, f"%{term}%"),
    ).fetchall()
    conn.close()
    groups = {}
    for row in rows:
        groups.setdefault(cluster_id(row["title_original"], date), []).append(dict(row))
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple v0.3 title deduplication")
    parser.add_argument("--update-db", action="store_true")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--test-cluster", default="")
    parser.add_argument("--date", default="")
    args = parser.parse_args()
    if args.test_cluster:
        print(json.dumps({"clusters": test_cluster(args.test_cluster, args.date)}, ensure_ascii=False, indent=2))
    elif args.update_db:
        print(json.dumps({"updated": update(args.days)}, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
