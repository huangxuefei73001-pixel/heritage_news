# Heritage News Skill

Heritage News Skill is a first-hand cultural and natural heritage news retrieval skill.

It is designed for heritage researchers, world heritage observers, museum and conservation professionals, and policy analysts who need a reliable multilingual evidence stream rather than another generic RSS reader.

## Why It Matters

Heritage news is scattered across official institutions, advisory bodies, national agencies, regional media, specialist publications, and multilingual local outlets. Important signals often appear outside the usual “heritage news” category: climate adaptation, biodiversity finance, land rights, tourism pressure, disaster recovery, museum ethics, illicit trafficking, community participation, and World Heritage monitoring.

This skill turns those scattered updates into a research-ready workflow:

- first-hand source discovery and verification
- multilingual heritage news collection
- local SQLite evidence cache
- source health monitoring
- issue framing: event -> issue -> mechanism -> comparison -> research/work lead

## Core Value

The goal is to become the most comprehensive first-hand heritage news source map for cultural heritage, natural heritage, living heritage, museums, archaeology, conservation, and World Heritage governance.

It does not cite WeChat or secondary digests as news sources. User-facing outputs should show original publishers only: UNESCO, IUCN, ICOMOS, ICOM, ICCROM, national agencies, wire services, regional media, specialist heritage sources, and other first-hand institutions.

## Current Capabilities

- 115-source legacy metadata map
- 56 v0.3 multilingual candidate sources
- 28 verified fetchable v0.3 sources
- RSS, web extraction, RSS discovery, and RSSHub fallback handling
- SQLite storage with article and source health tables
- Chinese digest generation with high-value commentary
- Source gap audit against curated local benchmark archives

## Example Questions


- `let me knwo what happened in the past week`
- `推送过去7天的世界遗产新闻周报`


## Main Commands

```bash
python3 scripts/fetch.py --all --update-db --force
python3 scripts/digest.py --days 7 --limit 20 --insight
python3 scripts/prepare.py --query "World Heritage Committee" --limit 5
python3 scripts/monitor.py --check-health
python3 scripts/radar_gap_audit.py --month 2026-06
```

## Data Policy

The repository ships source metadata, scripts, schema, and skill instructions. It intentionally does not commit the local SQLite cache or downloaded dependencies.

To initialize a local database:

```bash
sqlite3 data/heritage_news.db < database/schema.sql
python3 scripts/fetch.py --all --update-db --force
```

## Project Direction

This is not only a news feed. It is an AI-enabled heritage research system: a way to convert dispersed daily news into evidence trails, mechanism analysis, comparative cases, portfolio-ready research workflows, and reusable knowledge infrastructure for Heritage + AI + Knowledge Systems.
