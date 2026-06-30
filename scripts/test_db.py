#!/usr/bin/env python3
from __future__ import annotations

from common import connect, init_db


def main() -> None:
    conn = connect()
    init_db(conn)
    conn.execute(
        """INSERT OR IGNORE INTO heritage_news
           (title_original,source_name,source_tier,trust_level,language,country_region,pub_date,url,raw_content)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            "Test World Heritage item",
            "Test Source",
            "core_official",
            "high",
            "en",
            "global",
            "2026-06-30T00:00:00+00:00",
            "https://example.com/heritage-news-skill-test",
            "{}",
        ),
    )
    row = conn.execute("SELECT title_original FROM heritage_news WHERE url=?", ("https://example.com/heritage-news-skill-test",)).fetchone()
    assert row and row["title_original"] == "Test World Heritage item"
    conn.execute("UPDATE heritage_news SET title_zh=? WHERE url=?", ("测试世界遗产新闻", "https://example.com/heritage-news-skill-test"))
    row = conn.execute("SELECT title_zh FROM heritage_news WHERE url=?", ("https://example.com/heritage-news-skill-test",)).fetchone()
    assert row["title_zh"] == "测试世界遗产新闻"
    conn.commit()
    conn.close()
    print("db ok")


if __name__ == "__main__":
    main()
