#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from common import (
    connect,
    fetch_text,
    discover_feed,
    init_db,
    insert_articles,
    load_candidates,
    parse_rss,
    parse_web,
    source_key,
    update_health,
)


def due(conn, source: dict, force: bool) -> bool:
    if force:
        return True
    row = conn.execute("SELECT last_successful_fetch FROM source_health WHERE source_name=?", (source["name"],)).fetchone()
    if not row or not row["last_successful_fetch"]:
        return True
    hours = 1 if source["source_tier"] == "core_official" else 4
    last = datetime.fromisoformat(row["last_successful_fetch"])
    return datetime.now(timezone.utc) - last >= timedelta(hours=hours)


def fetch_source(source: dict) -> list[dict]:
    method = source.get("fetch_method")
    url = source.get("rss_url") if method in {"rss", "rsshub"} else source.get("url")
    if method in {"rss", "rsshub"} and not url and source.get("url"):
        method = "web"
        url = source.get("url")
    if not url:
        raise RuntimeError("missing fetch URL")
    try:
        text = fetch_text(url)
        rows = parse_rss(text, source) if method in {"rss", "rsshub"} else parse_web(text, source)
    except Exception:
        if method != "rsshub" or not source.get("url"):
            raise
        text = fetch_text(source["url"])
        rows = parse_web(text, source)
    if not rows and method == "web":
        if feed := discover_feed(source):
            rows = parse_rss(fetch_text(feed), source)
    if not rows:
        raise RuntimeError("no articles parsed")
    return rows


def select_sources(args: argparse.Namespace) -> list[dict]:
    sources = load_candidates()
    if args.sources:
        wanted = {x.strip().lower() for x in args.sources.split(",") if x.strip()}
        sources = [s for s in sources if s["name"].lower() in wanted or source_key(s).lower() in wanted]
    elif args.tier:
        sources = [s for s in sources if s.get("source_tier") == args.tier]
    elif args.all:
        sources = [
            s for s in sources
            if s.get("integration_status") in {"verified", "fetchable"}
            and (s.get("fetch_method") == "web" or bool(s.get("rss_url")))
        ]
    else:
        sources = [s for s in sources if source_key(s) in {"UNESCO", "ICOMOS", "Xinhua", "Reuters", "HeritageDaily"}]
    if args.stable:
        sources = [s for s in sources if s.get("fetch_method") == "rss" and s.get("rss_url") and s.get("integration_status") in {"verified", "fetchable"}]
    return sources[: args.limit] if args.limit else sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Heritage News v0.3 sources")
    parser.add_argument("--sources", default="", help="Comma-separated ids or names")
    parser.add_argument("--tier", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--stable", action="store_true", help="Only verified RSS sources")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-db", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    conn = connect()
    init_db(conn)
    payload = []
    for source in select_sources(args):
        if not args.dry_run and not due(conn, source, args.force):
            payload.append({"source": source["name"], "status": "skipped_rate_limit"})
            continue
        try:
            rows = fetch_source(source)
            inserted = insert_articles(conn, rows) if args.update_db else 0
            if args.update_db:
                update_health(conn, source["name"], True, inserted)
            payload.append({"source": source["name"], "status": "ok", "articles": len(rows), "inserted": inserted})
        except Exception as exc:
            if args.update_db:
                update_health(conn, source["name"], False, 0)
            payload.append({"source": source["name"], "status": "error", "error": str(exc)[:200]})
    conn.close()
    print(json.dumps({"results": payload}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
