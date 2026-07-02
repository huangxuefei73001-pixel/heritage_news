# Heritage News Skill Project State

## 1. 当前目标
- 建成一个抓取文化与自然遗产一手新闻源的 v0.3 skill/service。
- 默认生成中文日报/周报，保留原文链接、来源层级、语种和新闻解读。
- 优先补齐真实来源覆盖、抓取稳定性、日期归档和专业筛选逻辑。
- 参考公众号样本只用于校准漏抓，不作为新闻来源展示。

## 2. 已确认根因
- 2026-07-01 与标杆样本零重合的主因不是没有新闻，而是来源覆盖和匹配边界过窄。
- 原匹配偏向 `heritage/UNESCO/World Heritage` 直词，漏掉现场保护、文档化、展览交流、地方守护和气候研究。
- 中国新闻网原配置 `/cul/` 实际跳转到 `/wy/`，导致抓到刷新页而非文章列表。
- MDN 首页过泛，应抓英文 `Culture & Travel` 栏目。
- 中文媒体 URL 日期格式未覆盖，部分文章被按抓取时间归档。

## 3. 不允许做的事
- 不把公众号名称当作新闻来源展示。
- 不把未验证来源标成稳定 fetchable。
- 不使用 Claude API 做日报/周报解读。
- 不提交 `.env`、企业微信 webhook、数据库临时文件或参考样本目录。
- 不碰旧项目 `/home/ubuntu/cultural-news`，不在本地 Codex 自动化里建定时任务。

## 4. 已修改文件
- `sources/candidate_sources_from_wechat.yaml`
- `scripts/common.py`
- `scripts/test_keyword_filter.py`
- `scripts/analysis_engine.py`

## 5. 尚未验证内容
- 服务器 `/home/ubuntu/heritage_news` 是否已同步最新代码。
- 服务器 cron 下一次实际推送是否使用了新版 `push_wecom.py` 和新版来源配置。
- MDN/PSM 的文章页日期解析仍可能不稳定，部分页面缺少明确日期。
- Xinhua、国家林草局仍在健康统计里显示失败。
- RSSHub 路由仍未系统性验证。

## 6. 下一步
- 已完成本地最小验证：关键词样本、脚本编译、统计均通过。
- 已完成新增来源 dry-run 和 2026-07-01 日报格式化回看。
- 把 `docs/PROJECT_STATE.md` 纳入提交并同步 GitHub。
- 之后优先处理服务器同步和 Xinhua/国家林草局失败源。

## 阶段记录
- 2026-07-02 11:03 CST：`Bagan Clearance` 与 `敦煌大型特展` 均通过新关键词过滤；核心脚本 `py_compile` 通过；`prepare.py --stats` 正常，v0.3 来源 68 个，语种 en/zh/es/fr。
- 2026-07-02 11:05 CST：`MDN, Chinanews, PSMNews, YouthCN, ChinaJilin, YCWB` dry-run 全部 `ok`；2026-07-01 回看包含中国吉林网高句丽、羊城晚报敦煌特展等原先漏项。
