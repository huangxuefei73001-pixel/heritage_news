# CLAUDE.md - Heritage News Skill v0.2 Overlay

This is a non-destructive v0.2 overlay. The original project remains at:

`/Users/pauline/Documents/heritage-news-skill/`

All v0.2 files live at:

`/Users/pauline/Documents/UNESCO/heritage-news-skill-v0.2/`

## Architecture

```text
sources/sources.v0.2.yaml     normalized source list with status, priority, scope
data/heritage_news.db         copied SQLite database for local v0.2 verification
scripts/prepare.py            deterministic JSON output for skill use
scripts/search_v0_2.py        human-readable stats, source listing, and search
skill.v0.2.md                 skill workflow and answer rules
README.v0.2.md                user-facing project notes
```

## Status Rules

- `active`: fetchable now; must have a working `feed_url`.
- `active_no_feed`: reachable but not fetchable by the current RSS pipeline.
- `needs_verification`: access or feed state is unresolved.
- `broken`: confirmed unusable for now.

## Priority Rules

- `high`: policy, institutional, funding, listing, or professional heritage sources.
- `medium`: academic or specialist sources useful for research context.
- `low`: broad art/culture media used only as supporting context by default.

## Commands

```bash
cd /Users/pauline/Documents/UNESCO/heritage-news-skill-v0.2
python3 scripts/search_v0_2.py --stats
python3 scripts/search_v0_2.py --list-sources
python3 scripts/search_v0_2.py --list-sources --source-mode fetchable
python3 scripts/prepare.py --stats
python3 scripts/prepare.py --query "World Heritage Committee" --limit 5
python3 scripts/prepare.py --query "ICOMOS" --limit 5
python3 scripts/prepare.py --query "intangible cultural heritage" --limit 5
```

## Implementation Notes

v0.2 intentionally avoids RSSHub deployment, live crawling, central feed publishing, and AI summary persistence. It focuses on making the current project easier for an agent skill to call safely and consistently.
