# Heritage News v0.2 - Evidence-Style Cultural Heritage News Retrieval

Use this skill when the user asks about recent or historical cultural heritage news, policy, institutional updates, World Heritage, intangible cultural heritage, conservation organizations, heritage agencies, heritage funding, or professional heritage discourse.

## Default Workflow

Always prepare deterministic JSON before writing a user-facing answer:

```bash
cd /Users/pauline/Documents/UNESCO/heritage-news-skill-v0.2
python3 scripts/prepare.py --query "<query>" --limit 10
```

Useful filters:

```bash
python3 scripts/prepare.py --query "<query>" --days 7
python3 scripts/prepare.py --query "<query>" --region international
python3 scripts/prepare.py --query "<query>" --priority high
python3 scripts/prepare.py --query "<query>" --scope heritage_policy
```

## Answer Style

Answer in Chinese by default unless the user requests another language.

Use an evidence-style structure:

1. Brief conclusion.
2. Key dated evidence from the local database.
3. Source links.
4. Relevance notes when the match is indirect or from a low-priority media source.
5. Coverage caveat when the local database does not have enough evidence.

Do not invent coverage beyond the local database. Do not imply that the result is exhaustive unless the JSON result supports that claim.

If the user explicitly asks for live web research, state that the local database is the skill baseline and then perform separate live research as requested.

## Source Priority

- `high`: policy, institutional, funding, listing, professional heritage organization, or government heritage agency sources.
- `medium`: academic or specialist sources useful for research context.
- `low`: broad art/culture media. Use as supporting context, not as the primary evidence for policy or institutional claims.

## Local Commands

Stats:

```bash
python3 scripts/search_v0_2.py --stats
```

List all sources:

```bash
python3 scripts/search_v0_2.py --list-sources
```

List fetchable sources:

```bash
python3 scripts/search_v0_2.py --list-sources --source-mode fetchable
```

Human-readable search:

```bash
python3 scripts/search_v0_2.py "<query>" --limit 10
```

Machine-readable preparation:

```bash
python3 scripts/prepare.py --stats
python3 scripts/prepare.py --query "<query>" --limit 10
```

## Current Limits

- v0.2 uses a copied SQLite database under this overlay directory.
- v0.2 has 115 normalized sources, of which 18 are currently fetchable RSS sources in the generated source list.
- v0.2 does not deploy RSSHub.
- v0.2 does not store AI summaries in SQLite.
