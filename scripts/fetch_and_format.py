#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch verified sources and print enhanced heritage digest")
    parser.add_argument("--date", required=True)
    parser.add_argument("--format", default="enhanced")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    subprocess.run([sys.executable, "scripts/fetch.py", "--all", "--update-db", "--force"], cwd=ROOT, check=False)
    subprocess.run([sys.executable, "scripts/format_output.py", "--date", args.date, "--limit", str(args.limit)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
