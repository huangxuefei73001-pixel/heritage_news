#!/usr/bin/env python3
"""Prepare deterministic JSON for the Heritage News v0.2 skill workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "heritage_news.db"
SOURCES_PATH = PROJECT_ROOT / "sources" / "sources.v0.2.yaml"
V03_SOURCES_PATH = PROJECT_ROOT / "sources" / "candidate_sources_from_wechat.yaml"

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def load_sources(path: Path = SOURCES_PATH) -> dict[str, dict]:
    with path.open("r") as f:
        data = yaml.safe_load(f) or {}
    return {source["id"]: source for source in data.get("sources", [])}


def connect_readonly(path: Path = DB_PATH) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def fts_query(text: str) -> str:
    tokens = re.findall(r"[\w']+", text)
    return " AND ".join(tokens)


def search_articles(args: argparse.Namespace, sources: dict[str, dict]) -> list[dict]:
    conn = connect_readonly()
    conditions = []
    params: list[object] = []

    if args.query:
        match = fts_query(args.query)
        if match:
            conditions.append(
                "a.id IN (SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?)"
            )
            params.append(match)

    if args.source:
        conditions.append("a.source_id = ?")
        params.append(args.source)
    if args.region:
        conditions.append("a.region = ?")
        params.append(args.region)
    if args.category:
        conditions.append("a.category = ?")
        params.append(args.category)
    if args.language:
        conditions.append("a.language = ?")
        params.append(args.language)
    if args.days:
        conditions.append("a.fetched_at >= datetime('now', ?)")
        params.append(f"-{args.days} days")

    where = " AND ".join(conditions) if conditions else "1=1"
    query_limit = max(args.limit * 10, 100)
    rows = conn.execute(
        f"""
        SELECT a.source_id, a.title, a.url, a.published_date, a.summary,
               a.language, a.region, a.category, a.fetched_at
        FROM articles a
        WHERE {where}
        ORDER BY a.fetched_at DESC, a.published_date DESC
        LIMIT ?
        """,
        [*params, query_limit],
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        source = sources.get(row["source_id"], {})
        priority = source.get("priority", "medium")
        if args.priority and priority != args.priority:
            continue
        scope = source.get("scope", "other")
        if args.scope and scope != args.scope:
            continue
        results.append(
            {
                "title": row["title"],
                "url": row["url"],
                "source_id": row["source_id"],
                "source_name": source.get("name", row["source_id"]),
                "published_date": row["published_date"],
                "summary": row["summary"],
                "language": row["language"],
                "region": row["region"],
                "category": row["category"],
                "priority": priority,
                "scope": scope,
                "source_status": source.get("status", "unknown"),
                "relevance_note": source.get("notes", ""),
                "fetched_at": row["fetched_at"],
            }
        )

    results.sort(key=lambda item: item.get("fetched_at") or "", reverse=True)
    results.sort(key=lambda item: PRIORITY_RANK.get(item["priority"], 1))
    return results[: args.limit]


def source_summary(results: list[dict]) -> dict:
    represented = sorted({item["source_id"] for item in results})
    priorities = {}
    scopes = {}
    for item in results:
        priorities[item["priority"]] = priorities.get(item["priority"], 0) + 1
        scopes[item["scope"]] = scopes.get(item["scope"], 0) + 1
    return {
        "sources_represented": represented,
        "source_count": len(represented),
        "by_priority": priorities,
        "by_scope": scopes,
    }


def build_payload(args: argparse.Namespace) -> dict:
    sources = load_sources()
    results = search_articles(args, sources)
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project": "heritage-news-skill",
            "version": "0.3",
            "database": str(DB_PATH),
            "sources": str(SOURCES_PATH),
            "filters": {
                "query": args.query,
                "days": args.days,
                "region": args.region,
                "category": args.category,
                "language": args.language,
                "source": args.source,
                "priority": args.priority,
                "scope": args.scope,
                "limit": args.limit,
            },
            "result_count": len(results),
            **source_summary(results),
        },
        "results": results,
    }


def build_stats_payload() -> dict:
    sources = load_sources()
    conn = connect_readonly()
    total_articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    by_source = {
        row["source_id"]: row["cnt"]
        for row in conn.execute(
            "SELECT source_id, COUNT(*) AS cnt FROM articles GROUP BY source_id"
        ).fetchall()
    }
    v03_articles = 0
    recent_7d = 0
    recent_30d = 0
    health_rows = []
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "heritage_news" in tables:
        v03_articles = conn.execute("SELECT COUNT(*) FROM heritage_news").fetchone()[0]
        recent_7d = conn.execute("SELECT COUNT(*) FROM heritage_news WHERE pub_date >= datetime('now','-7 days')").fetchone()[0]
        recent_30d = conn.execute("SELECT COUNT(*) FROM heritage_news WHERE pub_date >= datetime('now','-30 days')").fetchone()[0]
    if "source_health" in tables:
        health_rows = [dict(row) for row in conn.execute("SELECT * FROM source_health").fetchall()]
    conn.close()

    source_rows = list(sources.values())
    v03_rows = []
    if V03_SOURCES_PATH.exists():
        with V03_SOURCES_PATH.open() as f:
            v03_rows = (yaml.safe_load(f) or {}).get("sources", [])
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project": "heritage-news-skill",
            "version": "0.3",
            "database": str(DB_PATH),
            "sources": str(SOURCES_PATH),
        },
        "stats": {
            "total_sources": len(source_rows),
            "fetchable_sources": sum(
                1
                for source in source_rows
                if source.get("status") == "active" and source.get("feed_url")
            ),
            "total_articles": total_articles,
            "by_status": dict(Counter(source.get("status", "unknown") for source in source_rows)),
            "by_priority": dict(Counter(source.get("priority", "medium") for source in source_rows)),
            "by_scope": dict(Counter(source.get("scope", "other") for source in source_rows)),
            "articles_by_source": by_source,
            "v03_total_articles": v03_articles,
            "v03_articles_last_7d": recent_7d,
            "v03_articles_last_30d": recent_30d,
            "v03_candidate_sources": len(v03_rows),
            "v03_by_source_tier": dict(Counter(source.get("source_tier", "unknown") for source in v03_rows)),
            "v03_by_language": dict(Counter(source.get("language", "unknown") for source in v03_rows)),
            "v03_by_integration_status": dict(Counter(source.get("integration_status", "unknown") for source in v03_rows)),
            "v03_by_rss_status": dict(Counter(source.get("rss_status", "unknown") for source in v03_rows)),
            "v03_health_by_status": dict(Counter(row.get("status", "unknown") for row in health_rows)),
            "v03_failed_sources": [
                row["source_name"] for row in health_rows if row.get("status") in {"unstable", "rejected"}
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Heritage News v0.2 JSON")
    parser.add_argument("--stats", action="store_true", help="Output JSON source/database stats")
    parser.add_argument("--query", default="", help="Keyword query")
    parser.add_argument("--days", type=int, default=0, help="Limit to recently fetched articles")
    parser.add_argument("--region", default="", help="Filter by region")
    parser.add_argument("--category", default="", help="Filter by category")
    parser.add_argument("--language", default="", help="Filter by language")
    parser.add_argument("--source", default="", help="Filter by source_id")
    parser.add_argument("--priority", choices=["high", "medium", "low"], default="")
    parser.add_argument("--scope", default="", help="Filter by v0.2 scope")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    payload = build_stats_payload() if args.stats else build_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    main()
