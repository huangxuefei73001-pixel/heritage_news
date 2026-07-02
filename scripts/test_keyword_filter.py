#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import re

from common import HERITAGE_TERMS, UNESCO_DATA_TERMS, has_heritage_term


def main() -> None:
    parser = argparse.ArgumentParser(description="Test heritage keyword filter")
    parser.add_argument("--sample", required=True)
    args = parser.parse_args()
    text = args.sample.lower()
    hits = []
    for term in HERITAGE_TERMS + UNESCO_DATA_TERMS:
        needle = term.lower()
        if needle.isascii():
            matched = re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text)
        else:
            matched = needle in text
        if matched:
            hits.append(term)
    print(json.dumps({"sample": args.sample, "is_heritage": has_heritage_term(args.sample), "hits": hits}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
