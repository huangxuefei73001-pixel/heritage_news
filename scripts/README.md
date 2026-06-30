# Scripts

```bash
python3 scripts/fetch.py --sources UNESCO,ICOMOS,Xinhua --dry-run
python3 scripts/fetch.py --tier core_official --limit 10
python3 scripts/fetch.py --all --update-db
python3 scripts/verify_sources.py --limit 20
python3 scripts/translate.py --sample 10
python3 scripts/deduplicate.py --test-cluster "Notre-Dame" --date 2026-06-25
python3 scripts/monitor.py --check-health
python3 scripts/digest.py --days 7 --limit 20
python3 scripts/test_db.py
python3 scripts/test_skill.py --query "最近世界遗产申报"
```

No paid translation API in v0.3. Non-Chinese rows remain `translation_status=pending`.
