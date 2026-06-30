#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path("/Users/pauline/Desktop/国际遗产观察/0630世遗雷达文章内容抓取")

ALIASES = {
    "新华社": "Xinhua",
    "新华网": "Xinhua",
    "新华社英文版": "Xinhua",
    "路透社": "Reuters Heritage",
    "Reuters": "Reuters Heritage",
    "AFP": "AFP",
    "EFE": "EFE",
    "UNESCO世界遗产中心": "UNESCO World Heritage Centre",
    "UNESCO WHC": "UNESCO World Heritage Centre",
    "ICOM官网": "ICOM",
    "IUCN官网": "IUCN",
    "韩联社": "Yonhap",
    "共同社": "Kyodo",
    "越通社": "VietnamPlus",
    "中国日报": "China Daily",
    "中国新闻网": "中国新闻网",
    "中新网": "中国新闻网",
    "国家文物局官网": "国家文物局",
    "国家文物局": "国家文物局",
    "国家林草局": "国家林草局",
    "国家林业和草原局": "国家林草局",
}

SKIP = {"多来源", "综合报道", "今日信息来源", "本期信息来源", "由AI根据信息来源整理"}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def canonical(value: str) -> str:
    value = value.strip(" \t\u00a0-—")
    return ALIASES.get(value, value)


def source_bits(line: str) -> list[str]:
    if "📰" not in line:
        return []
    line = line.split("📰", 1)[1]
    line = re.sub(r"[（(].*?[）)]", "", line)
    out = []
    for bit in re.split(r"·|/|、|，|,|｜|\||;", line):
        bit = bit.strip(" \t\u00a0-—")
        if bit and bit not in SKIP and len(bit) < 60:
            out.append(canonical(bit))
    return out


def archive_sources(path: Path, month: str) -> tuple[Counter, dict[str, set[str]]]:
    month_zh = f"{int(month[-2:])}月"
    counts: Counter[str] = Counter()
    examples: dict[str, set[str]] = {}
    for file in path.glob("*.md"):
        name = file.name
        if month_zh not in name and month not in name:
            continue
        for line in file.read_text(errors="ignore").splitlines():
            for source in source_bits(line):
                counts[source] += 1
                examples.setdefault(source, set()).add(name)
    return counts, examples


def configured_sources() -> dict[str, dict]:
    data = yaml.safe_load((ROOT / "sources" / "candidate_sources_from_wechat.yaml").read_text()) or {}
    out = {}
    for source in data.get("sources", []):
        out[norm(source["name"])] = source
    return out


def db_sources() -> set[str]:
    conn = sqlite3.connect(ROOT / "data" / "heritage_news.db")
    try:
        return {norm(row[0]) for row in conn.execute("select distinct source_name from heritage_news")}
    finally:
        conn.close()


def audit(path: Path, month: str) -> dict:
    counts, examples = archive_sources(path, month)
    configured = configured_sources()
    fetched = db_sources()
    rows = []
    for name, mentions in counts.most_common():
        key = norm(name)
        cfg = configured.get(key)
        status = "fetched" if key in fetched else "configured_not_fetched" if cfg else "not_configured"
        rows.append({
            "source": name,
            "mentions": mentions,
            "status": status,
            "integration_status": cfg.get("integration_status") if cfg else None,
            "fetch_method": cfg.get("fetch_method") if cfg else None,
            "examples": sorted(examples.get(name, []))[:3],
        })
    return {"archive": str(path), "month": month, "total_sources": len(rows), "sources": rows}


def print_markdown(data: dict, limit: int) -> None:
    print(f"# 来源缺口审计（{data['month']}）\n")
    print(f"校准目录：{data['archive']}")
    print("说明：这里统计的是校准稿件中提到的一手来源；公众号名称不作为新闻来源。\n")
    for status, title in [
        ("fetched", "已在本地库出现"),
        ("configured_not_fetched", "已配置但未稳定抓取"),
        ("not_configured", "尚未配置"),
    ]:
        rows = [x for x in data["sources"] if x["status"] == status][:limit]
        print(f"## {title}\n")
        if not rows:
            print("无\n")
            continue
        for row in rows:
            detail = ""
            if row["integration_status"]:
                detail = f"｜{row['integration_status']}｜{row['fetch_method']}"
            print(f"- {row['source']}：{row['mentions']} 次{detail}")
            if row["examples"]:
                print(f"  例：{row['examples'][0]}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit first-hand source gaps against the June radar archive")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--month", default="2026-06")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = audit(args.archive, args.month)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_markdown(data, args.limit)


if __name__ == "__main__":
    main()
