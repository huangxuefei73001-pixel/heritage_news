#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def env(name: str) -> str | None:
    if value := os.environ.get(name):
        return value
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == name:
            return value.strip().strip("\"'")
    return None


def report(kind: str, date: str, limit: int) -> str:
    days = "7" if kind == "weekly" else "0"
    subprocess.run([sys.executable, "scripts/fetch.py", "--all", "--update-db", "--force"], cwd=ROOT, check=False)
    return subprocess.check_output(
        [sys.executable, "scripts/format_output.py", "--date", date, "--days", days, "--limit", str(limit)],
        cwd=ROOT,
        text=True,
    )


def send_markdown(webhook: str, text: str) -> None:
    payload = json.dumps({"msgtype": "markdown", "markdown": {"content": text}}, ensure_ascii=False).encode()
    req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode()
    data = json.loads(body or "{}")
    if data.get("errcode") != 0:
        raise RuntimeError(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Push heritage news report to WeCom")
    parser.add_argument("--kind", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat())
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    text = report(args.kind, args.date, args.limit)
    if args.dry_run:
        print(text)
        return
    webhook = env("WECOM_WEBHOOK_URL")
    if not webhook:
        raise SystemExit("Missing WECOM_WEBHOOK_URL")
    send_markdown(webhook, text[:19000])


if __name__ == "__main__":
    main()
