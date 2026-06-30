#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import connect, init_db

TERMS = {
    "World Heritage": "世界遗产",
    "Intangible Cultural Heritage": "非物质文化遗产",
    "UNESCO": "联合国教科文组织",
    "ICOMOS": "国际古迹遗址理事会",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark v0.3 translation status without paid API")
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--pending", action="store_true")
    args = parser.parse_args()
    conn = connect()
    init_db(conn)
    conn.execute("UPDATE heritage_news SET translation_status='done' WHERE language='zh'")
    conn.execute("UPDATE heritage_news SET translation_status='pending' WHERE language!='zh' AND title_zh IS NULL")
    conn.commit()
    limit = args.sample or 20
    rows = conn.execute(
        """SELECT id,title_original,language,translation_status FROM heritage_news
           WHERE (? OR translation_status='pending') ORDER BY pub_date DESC LIMIT ?""",
        (0 if args.pending else 1, limit),
    ).fetchall()
    conn.close()
    print(json.dumps({"terms": TERMS, "rows": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
