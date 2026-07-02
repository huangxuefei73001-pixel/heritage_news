#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import (
    HERITAGE_ACTION_TERMS,
    HERITAGE_SITE_TERMS,
    HERITAGE_TERMS,
    HERITAGE_TYPE_TERMS,
    UNESCO_DATA_TERMS,
    has_heritage_term,
    term_matches,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test heritage keyword filter")
    parser.add_argument("--sample", required=True)
    args = parser.parse_args()
    text = args.sample.lower()
    groups = {
        "direct": HERITAGE_TERMS,
        "unesco_data": UNESCO_DATA_TERMS,
        "site": HERITAGE_SITE_TERMS,
        "type": HERITAGE_TYPE_TERMS,
        "action": HERITAGE_ACTION_TERMS,
    }
    hits = {
        name: [term for term in terms if term_matches(text, term)]
        for name, terms in groups.items()
    }
    print(json.dumps({"sample": args.sample, "is_heritage": has_heritage_term(args.sample), "hits": hits}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
