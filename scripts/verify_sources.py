#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import HERITAGE_TERMS, fetch_text, has_heritage_term, load_candidates, parse_rss, parse_web, source_key


def check(source: dict, keyword: str = "") -> dict:
    result = {
        "name": source["name"],
        "tier": source["source_tier"],
        "url_accessible": False,
        "has_heritage_content": False,
        "wechat_evidence": source.get("wechat_evidence_count", 0) >= 3,
        "rss_parsable": False,
        "manual_review_required": True,
    }
    try:
        text = fetch_text(source["url"], retries=1)
        result["url_accessible"] = True
        result["has_heritage_content"] = has_heritage_term(text) or (bool(keyword) and keyword.lower() in text.lower())
        result["web_articles"] = len(parse_web(text, source))
    except Exception as exc:
        result["url_error"] = str(exc)[:160]
    if source.get("rss_url"):
        try:
            result["rss_parsable"] = bool(parse_rss(fetch_text(source["rss_url"], retries=1), source))
        except Exception as exc:
            result["rss_error"] = str(exc)[:160]
    result["candidate_verified"] = result["url_accessible"] and result["has_heritage_content"] and result["wechat_evidence"]
    result["fetchable_verified"] = result["rss_parsable"] and result["manual_review_required"] is False
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify candidate heritage news sources")
    parser.add_argument("--sources", default="", help="Comma-separated source names or ids")
    parser.add_argument("--date-range", default="", help="Accepted for audit compatibility; filtering is fetch-time only")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--tier", default="")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    sources = load_candidates()
    if args.sources:
        wanted = {x.strip().lower() for x in args.sources.split(",") if x.strip()}
        sources = [s for s in sources if s["name"].lower() in wanted or source_key(s).lower() in wanted]
    if args.tier:
        sources = [s for s in sources if s.get("source_tier") == args.tier]
    if args.limit:
        sources = sources[: args.limit]
    print(json.dumps({"date_range": args.date_range, "results": [check(s, args.keyword) for s in sources]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
