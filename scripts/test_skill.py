#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import connect, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiny skill interface smoke test")
    parser.add_argument("--query", required=True)
    parser.add_argument("--sources", default="")
    parser.add_argument("--tier", default="")
    args = parser.parse_args()
    conn = connect()
    init_db(conn)
    where = ["(title_original LIKE ? OR COALESCE(summary_zh,'') LIKE ?)"]
    params = [f"%{args.query}%", f"%{args.query}%"]
    if args.sources:
        where.append("source_tier=?")
        params.append(args.sources)
    if args.tier:
        where.append("source_tier=?")
        params.append(args.tier)
    rows = conn.execute(
        f"""SELECT title_original,title_zh,language,source_name,source_tier,pub_date,url,summary_zh,event_cluster_id
            FROM heritage_news WHERE {' AND '.join(where)}
            ORDER BY pub_date DESC, source_tier ASC LIMIT 10""",
        params,
    ).fetchall()
    conn.close()
    print(f"查询：{args.query}")
    if not rows:
        print("暂无 v0.3 入库结果。请先运行 fetch.py --update-db。")
        return
    for row in rows:
        title = row["title_zh"] or f"{row['title_original']} [{row['language']}]"
        print(f"- {title}｜{row['source_name']}｜{row['source_tier']}｜{row['pub_date']}")
        print(f"  {row['url']}")


if __name__ == "__main__":
    main()
