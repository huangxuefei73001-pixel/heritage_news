#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from format_output import parse_date, rows_for

TIER_LABELS = {
    "core_official": "official",
    "wire_media": "wire/media",
    "regional_media": "regional media",
    "specialist_media": "specialist source",
}


def why(title: str) -> str:
    text = title.lower()
    if "creative products" in text or "apec" in text:
        return "Why it matters: museum retail and cultural products are becoming part of heritage communication, tourism diplomacy and public interpretation."
    if "angkor" in text or "siem reap" in text or "tourism" in text:
        return "Why it matters: Angkor shows how visitor management, hotel investment, transport access and conservation pressure now have to be governed together."
    if "geopark" in text:
        return "Why it matters: geoparks are useful cases for linking natural heritage, local culture, education and community benefit in one governance frame."
    if "ukraine" in text:
        return "Why it matters: wartime heritage protection is moving from emergency response toward tools for risk mapping, prioritisation and institutional coordination."
    if "toltec" in text or "archaeolog" in text or "burial" in text:
        return "Why it matters: archaeological discoveries can reshape regional narratives, comparative research and future protection boundaries."
    if "museum" in text or "bell" in text:
        return "Why it matters: museum objects become more valuable when they are connected to interpretation, public knowledge and comparative research."
    return "Why it matters: this is a useful signal for tracking how heritage protection is shaped by policy, institutions, finance, tourism and local governance."


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a manual English LinkedIn heritage news post")
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat())
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    grouped = rows_for(args.date, args.days)
    rows = (grouped.get("各国动态") or []) + (grouped.get("国内动态") or [])
    rows = rows[: args.limit]

    label = "Daily" if args.days == 0 else f"{args.days}-day"
    print(f"Heritage News {label} Brief | {args.date}\n")
    print("A few first-hand heritage news signals I am tracking today:\n")
    for index, row in enumerate(rows, 1):
        date = parse_date(row["pub_date"]).date().isoformat()
        print(f"{index}. {row['title_original']}")
        print(f"Source: {row['source_name']} | {TIER_LABELS.get(row['source_tier'], row['source_tier'])} | {row['language']} | {date}")
        print(why(row["title_original"]))
        print(row["url"])
        print()
    print("These items are selected from a multilingual first-hand heritage news monitoring workflow.")
    print("#WorldHeritage #CulturalHeritage #HeritageManagement #UNESCO #HeritageNews")


if __name__ == "__main__":
    main()
