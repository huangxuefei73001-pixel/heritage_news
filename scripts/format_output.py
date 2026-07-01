#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analysis_engine import generate_deep_analysis
from common import DB_PATH, has_heritage_term, init_db

TIER_LABELS = {
    "core_official": "官方",
    "wire_media": "通讯社",
    "regional_media": "地区媒体",
    "specialist_media": "专业媒体",
}

CHINA_REGIONS = {"china", "cn", "hong_kong", "macau", "taiwan"}


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def zh_title(title: str) -> str:
    replacements = {
        "UNESCO hands over strategic tools to strengthen the protection of World Heritage in Ukraine": "UNESCO向乌克兰移交战略工具，加强世界遗产保护",
        "UNESCO remet des outils stratégiques pour renforcer la protection du patrimoine mondial en Ukraine": "UNESCO向乌克兰移交战略工具，加强世界遗产保护",
        "Archaeologists Find Toltec Reliefs and Ancient Human Burials in Mexico": "墨西哥发现托尔特克浮雕和古代人类墓葬",
        "Museum creative products: A new bridge for APEC tourism": "博物馆文创成为APEC旅游交流的新桥梁",
        "Angkor Archaeological Park Introduces New Visitor Management Measures to Protect Heritage": "吴哥考古公园推出新的游客管理措施保护遗产",
        "Cambodia Expands Heritage Protection Measures at Angkor Archaeological Park": "柬埔寨扩大吴哥考古公园遗产保护措施",
        "Siem Reap Introduces New Heritage Management Standards for Angkor Visitors": "暹粒为吴哥游客引入新的遗产管理标准",
        "National Museum of Cambodia Launches Digital Heritage Preservation Partnership": "柬埔寨国家博物馆启动数字遗产保护合作",
        "[Treasures from National Museum of Korea] Buddhist Bell from Cheonheungsa": "韩国国立中央博物馆介绍天兴寺佛钟",
    }
    return replacements.get(title, title.replace("&#x2019;", "’").replace("&#8217;", "’"))


def lead(item: sqlite3.Row) -> str:
    title = zh_title(item["title_original"])
    return f"这条动态聚焦“{title}”，可作为遗产保护、展示或治理机制的今日观察样本。"


def key_points(item: sqlite3.Row) -> list[str]:
    points = [
        f"来源层级：{TIER_LABELS.get(item['source_tier'], item['source_tier'])}；语种：{item['language']}。",
        f"地区/范围：{item['country_region'] or '未标注'}。",
        f"原文链接：{item['url']}",
    ]
    if item["summary_zh"]:
        points.insert(0, item["summary_zh"][:120])
    return points[:5]


def section_name(item: sqlite3.Row) -> str:
    return "国内动态" if (item["country_region"] or "").lower() in CHINA_REGIONS else "各国动态"


def format_item(item: sqlite3.Row) -> str:
    dt = parse_date(item["pub_date"])
    body = [
        f"🗓️ {dt.month}月{dt.day}日  |  📰 {item['source_name']}",
        f"**{zh_title(item['title_original'])}**",
        "",
        lead(item),
        "",
    ]
    body += [f"🔹 {point}" for point in key_points(item)]
    body += ["", "⭐ 值得关注", generate_deep_analysis(dict(item))]
    return "\n".join(body)


def canonical_key(row: sqlite3.Row) -> str:
    url = row["url"]
    if "whc.unesco.org" in url:
        import re

        if match := re.search(r"/(?:en/news|fr/actualites)/(\d+)", url):
            return f"unesco-whc:{match.group(1)}"
    return url


def displayable(row: sqlite3.Row) -> bool:
    title = row["title_original"].strip()
    if "..." in title or len(title) > 180:
        return False
    if row["source_tier"] in {"regional_media", "wire_media", "specialist_media"}:
        haystack = f"{title} {row['summary_zh'] or ''} {row['url']}".lower()
        return has_heritage_term(haystack)
    return True


def rows_for(date: str, days: int = 0, per_source_limit: int = 3) -> dict[str, list[sqlite3.Row]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    if days:
        start = (datetime.fromisoformat(date).replace(tzinfo=timezone.utc) - timedelta(days=days - 1)).date().isoformat()
    else:
        start = date
    rows = conn.execute(
        """SELECT * FROM heritage_news
           WHERE date(pub_date) >= ? AND date(pub_date) <= ?
           AND lower(title_original) NOT LIKE '%job%'
           AND lower(title_original) NOT LIKE '%vacancy%'
           ORDER BY pub_date DESC, source_tier ASC""",
        (start, date),
    ).fetchall()
    conn.close()
    grouped = {"各国动态": [], "国内动态": []}
    seen_events: set[str] = set()
    source_counts: dict[str, int] = {}
    for row in rows:
        if not displayable(row):
            continue
        key = canonical_key(row)
        if key in seen_events:
            continue
        if source_counts.get(row["source_name"], 0) >= per_source_limit:
            continue
        seen_events.add(key)
        source_counts[row["source_name"]] = source_counts.get(row["source_name"], 0) + 1
        grouped[section_name(row)].append(row)
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser(description="Format heritage news as structured Chinese push output")
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--per-source-limit", type=int, default=3)
    args = parser.parse_args()

    grouped = rows_for(args.date, args.days, args.per_source_limit)
    print(f"# Heritage News 推送｜{args.date}\n")
    count = 0
    for section, rows in grouped.items():
        if not rows:
            continue
        print(f"## {section}\n")
        for row in rows:
            if count >= args.limit:
                return
            print(format_item(row))
            print()
            count += 1


if __name__ == "__main__":
    main()
