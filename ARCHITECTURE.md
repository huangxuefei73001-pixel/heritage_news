# Heritage News v0.3 Architecture

```text
candidate_sources_from_wechat.yaml
        |
        v
scripts/verify_sources.py  -> candidate / verified 判断
        |
        v
scripts/fetch.py           -> heritage_news + source_health
        |
        v
scripts/translate.py       -> translation_status, title_zh 可为空
        |
        v
scripts/deduplicate.py     -> event_cluster_id
        |
        v
SKILL.md / scripts/test_skill.py -> 中文输出
```

SQLite 是唯一存储。v0.3 只抓标题、摘要、日期、来源、URL 和 raw feed/web 数据。
