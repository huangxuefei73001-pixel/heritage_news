#!/usr/bin/env python3
"""Human-readable search and source stats for Heritage News v0.2."""

from __future__ import annotations

import argparse
import os
import sqlite3
from collections import Counter
from pathlib import Path

import yaml

from prepare import PROJECT_ROOT, DB_PATH, SOURCES_PATH, build_payload, load_sources


REGION_LABELS = {
    "international": "国际",
    "europe": "欧洲",
    "asia_pacific": "亚太",
    "africa": "非洲",
    "arab_states": "阿拉伯国家",
    "latin_america_caribbean": "拉美和加勒比",
    "north_america": "北美",
}

CATEGORY_LABELS = {
    "international_org": "国际组织",
    "regional_org": "区域组织",
    "national_body": "国家机构",
    "foundation": "基金会",
    "academic": "学术期刊",
    "media": "专业媒体",
    "blog": "独立博客",
}


def connect_readonly(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def source_stats() -> dict:
    with SOURCES_PATH.open("r") as f:
        data = yaml.safe_load(f) or {}
    sources = data.get("sources", [])
    conn = connect_readonly()
    article_counts = dict(
        conn.execute(
            "SELECT source_id, COUNT(*) AS cnt FROM articles GROUP BY source_id"
        ).fetchall()
    )
    total_articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()

    return {
        "total_sources": len(sources),
        "fetchable_sources": sum(
            1 for source in sources if source.get("status") == "active" and source.get("feed_url")
        ),
        "total_articles": total_articles,
        "by_status": Counter(source.get("status", "unknown") for source in sources),
        "by_priority": Counter(source.get("priority", "medium") for source in sources),
        "by_scope": Counter(source.get("scope", "other") for source in sources),
        "article_counts": article_counts,
        "sources": sources,
    }


def print_stats() -> None:
    stats = source_stats()
    print("Heritage News v0.2 stats")
    print("=" * 72)
    print(f"Sources:          {stats['total_sources']}")
    print(f"Fetchable RSS:    {stats['fetchable_sources']}")
    print(f"Articles in DB:   {stats['total_articles']}")
    print("\nBy status:")
    for status, count in stats["by_status"].most_common():
        print(f"  {status:18s} {count:>5d}")
    print("\nBy priority:")
    for priority, count in stats["by_priority"].most_common():
        print(f"  {priority:18s} {count:>5d}")
    print("\nBy scope:")
    for scope, count in stats["by_scope"].most_common():
        print(f"  {scope:18s} {count:>5d}")


def print_sources(mode: str) -> None:
    stats = source_stats()
    sources = stats["sources"]
    if mode == "fetchable":
        sources = [
            source
            for source in sources
            if source.get("status") == "active" and source.get("feed_url")
        ]

    print(f"{'Source ID':38s} {'Status':15s} {'Pri':6s} {'Scope':20s} Articles")
    print("-" * 96)
    for source in sources:
        sid = source["id"]
        articles = stats["article_counts"].get(sid, 0)
        print(
            f"{sid:38s} {source.get('status','unknown'):15s} "
            f"{source.get('priority','-'):6s} {source.get('scope','-'):20s} {articles:>8d}"
        )


def print_results(args: argparse.Namespace) -> None:
    payload = build_payload(args)
    results = payload["results"]
    print(f"Search: {args.query!r} - {len(results)} result(s)")
    print("=" * 72)
    for index, item in enumerate(results, 1):
        region = REGION_LABELS.get(item.get("region"), item.get("region") or "-")
        category = CATEGORY_LABELS.get(item.get("category"), item.get("category") or "-")
        date = (item.get("published_date") or "?")[:30]
        print(f"[{index}] {item['title'][:120]}")
        print(
            f"    {item['source_id']} | {region} | {category} | "
            f"{item['priority']} | {item['scope']} | {date}"
        )
        if item.get("summary"):
            print(f"    {item['summary'][:260]}")
        print(f"    {item['url']}")
        print("-" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Heritage News v0.2 search")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--source-mode", choices=["all", "fetchable"], default="all")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--region", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--language", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--priority", choices=["high", "medium", "low"], default="")
    parser.add_argument("--scope", default="")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return
    if args.list_sources:
        print_sources(args.source_mode)
        return
    if not args.query:
        parser.print_help()
        return
    print_results(args)


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    main()
