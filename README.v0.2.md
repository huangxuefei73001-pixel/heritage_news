# Heritage News Skill v0.2 Overlay

This directory is a non-destructive v0.2 overlay for the original project at:

`/Users/pauline/Documents/heritage-news-skill/`

The original project is read-only for this v0.2 pass. All new files live under:

`/Users/pauline/Documents/UNESCO/heritage-news-skill-v0.2/`

## What v0.2 Does

v0.2 turns the existing cultural heritage news project into a more reliable skill-ready research retrieval layer.

- Normalizes source status into `active`, `active_no_feed`, `needs_verification`, and `broken`.
- Adds lightweight research metadata: `priority` and `scope`.
- Keeps a copied SQLite database for local verification.
- Adds `scripts/prepare.py`, which outputs deterministic JSON for AI skill use.
- Adds `scripts/search_v0_2.py`, which provides human-readable search and source stats.

## Current Coverage

The v0.2 source list is generated from the current original `sources.yaml`.

- Total sources: 115
- Fetchable RSS sources in the v0.2 source list: 18
- Active but not currently fetchable by RSS: 90
- Broken: 7

The number differs from earlier notes that mentioned 20 fetchable sources because the current full source list already uses additional statuses such as `rsshub` and `skip`; v0.2 normalizes those statuses.

## Commands

Human-readable stats:

```bash
cd /Users/pauline/Documents/UNESCO/heritage-news-skill-v0.2
python3 scripts/search_v0_2.py --stats
```

List all sources:

```bash
python3 scripts/search_v0_2.py --list-sources
```

List only currently fetchable RSS sources:

```bash
python3 scripts/search_v0_2.py --list-sources --source-mode fetchable
```

Prepare skill-consumable JSON:

```bash
python3 scripts/prepare.py --stats
python3 scripts/prepare.py --query "World Heritage Committee" --limit 5
python3 scripts/prepare.py --query "ICOMOS" --limit 5
python3 scripts/prepare.py --query "intangible cultural heritage" --limit 5
```

Parse JSON:

```bash
python3 scripts/prepare.py --query "ICOMOS" --limit 5 | python3 -m json.tool
```

## v0.2 Scope

This version does not deploy RSSHub, create a central public feed, or write AI summaries into the database.

The first retrieval priority is cultural heritage policy and institutional dynamics: UNESCO, ICOMOS, ICCROM, national heritage agencies, regional organizations, conservation foundations, academic/specialist sources, and clearly heritage-related professional media.

Broad art and culture media sources remain available as supporting context, but they are marked `priority: low` and `scope: media_general`.
