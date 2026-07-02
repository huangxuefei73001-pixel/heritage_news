#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import urllib3
import yaml
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "heritage_news.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
CANDIDATES_PATH = PROJECT_ROOT / "sources" / "candidate_sources_from_wechat.yaml"

HERITAGE_TERMS = (
    "heritage", "unesco", "icomos", "iccrom", "iucn", "museum", "archaeology", "archaeologist", "archaeologists",
    "world heritage", "patrimoine", "patrimonio", "monument",
    "restitution", "looted", "artifact", "artefact", "hia", "buffer zone",
    "outstanding universal value", "ouv", "reactive monitoring", "danger list",
    "tentative list", "nomination", "inscription", "jongmyo", "banaue", "angkor",
    "sebastia", "文化遗产", "世界遗产", "文物", "考古", "博物馆", "遗产", "申遗",
    "濒危名录", "缓冲区", "突出普遍价值", "宗庙", "巴纳韦", "吴哥", "塞巴斯蒂亚",
)

UNESCO_DATA_TERMS = (
    "cultural and natural heritage", "intangible cultural heritage", "underwater cultural heritage",
    "memory of the world", "unesco global geopark", "biosphere reserve", "cultural statistics",
    "cultural participation", "cultural employment", "creative economy", "cultural goods",
    "cultural industries", "heritage expenditure", "sdg 11.4.1",
    "文化和自然遗产", "非物质文化遗产", "水下文化遗产", "世界记忆", "联合国教科文组织世界地质公园",
    "生物圈保护区", "文化统计", "文化参与", "文化就业", "创意经济", "文化产品", "文化产业",
    "遗产支出",
)

HERITAGE_SITE_TERMS = (
    "bagan", "pagan", "angkor", "jongmyo", "dunhuang", "goguryeo", "koguryo",
    "beijing central axis", "central axis of beijing", "banaue", "dak nong", "sebastia",
    "petra", "samaipata", "notre-dame", "pic du midi", "jodrell bank",
    "蒲甘", "吴哥", "宗庙", "敦煌", "莫高窟", "高句丽", "北京中轴线",
    "巴纳韦", "塞巴斯蒂亚", "萨迈帕塔", "佩特拉",
)

HERITAGE_TYPE_TERMS = (
    "archaeological", "archaeology", "cultural heritage", "natural heritage",
    "intangible heritage", "underwater heritage", "heritage site", "historic site",
    "monument", "museum", "artifact", "artefact", "relic", "geopark", "biosphere reserve",
    "考古", "文物", "非遗", "文化遗产", "自然遗产", "古迹", "遗址", "遗产地",
    "博物馆", "馆藏", "地质公园", "生物圈保护区",
)

HERITAGE_ACTION_TERMS = (
    "restoration", "preservation", "conservation", "cleanup", "clean-up", "clearance",
    "vegetation cleanup", "stabilization", "documentation", "documenting", "documented",
    "digitization", "digital preservation", "3d scanning", "exhibition", "expo",
    "cultural exchange", "stewardship", "community", "climate change", "global warming",
    "sea level rise", "funding", "budget", "investment", "protection", "safeguarding",
    "修复", "保护", "清理", "植被清理", "加固", "文档化", "记录", "数字化",
    "展览", "特展", "开幕", "文化交流", "守护", "传承", "社区", "气候变化",
    "全球变暖", "海平面上升", "资金", "投入", "拨款",
)


def term_matches(text: str, term: str) -> bool:
    needle = term.lower()
    if needle.isascii():
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text))
    return needle in text


def has_heritage_term(text: str) -> bool:
    haystack = text.lower()
    for term in HERITAGE_TERMS + UNESCO_DATA_TERMS:
        if term_matches(haystack, term):
            return True
    if any(term_matches(haystack, term) for term in HERITAGE_SITE_TERMS):
        return True
    has_type = any(term_matches(haystack, term) for term in HERITAGE_TYPE_TERMS)
    has_action = any(term_matches(haystack, term) for term in HERITAGE_ACTION_TERMS)
    if has_type and has_action:
        return True
    for action in ("climate change", "global warming", "sea level rise", "气候变化", "全球变暖", "海平面上升"):
        if term_matches(haystack, action) and any(term_matches(haystack, t) for t in ("heritage", "site", "文化遗产", "遗产地")):
            return True
    return False


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_candidates(path: Path = CANDIDATES_PATH) -> list[dict]:
    with path.open() as f:
        return (yaml.safe_load(f) or {}).get("sources", [])


def source_key(source: dict) -> str:
    return source.get("id") or source["name"].replace(" ", "")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def fetch_text(url: str, timeout: int = 20, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or resp.encoding
            return resp.text
        except Exception as exc:
            last = exc
            time.sleep(2 ** attempt)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeritageNewsSkill/0.3"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc or last))


def strip_html(value: str) -> str:
    value = re.sub(r"<script.*?</script>|<style.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> str:
    if not value:
        return utcnow()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return value


def parse_rss(xml_text: str, source: dict) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    rows = []
    for item in items:
        def text(name: str) -> str:
            found = item.find(name)
            if found is None:
                found = item.find(f"{{http://www.w3.org/2005/Atom}}{name}")
            return "".join(found.itertext()).strip() if found is not None else ""

        title = text("title")
        link = text("link")
        if not link:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
        summary = text("description") or text("summary")
        pub_date = text("pubDate") or text("updated") or text("published")
        if title and link:
            haystack = f"{title} {summary} {link}".lower()
            if source.get("source_tier") in {"wire_media", "regional_media"} and not has_heritage_term(haystack):
                continue
            rows.append(article_from_source(source, title, link, pub_date, strip_html(summary), {"feed": True}))
    return rows


def discover_feed(source: dict) -> str | None:
    base = source.get("url")
    if not base:
        return None
    candidates = []
    try:
        html = fetch_text(base, timeout=10, retries=1)
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all("link", href=True):
            kind = " ".join([link.get("type", ""), link.get("rel", [""])[0] if isinstance(link.get("rel"), list) else str(link.get("rel", ""))]).lower()
            if "rss" in kind or "atom" in kind:
                candidates.append(absolute_url(base, link["href"]))
    except Exception:
        pass
    root = base.rstrip("/")
    candidates += [f"{root}/feed/", f"{root}/rss", f"{root}/rss.xml", f"{root}/feed.xml", f"{root}/atom.xml"]
    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        try:
            rows = parse_rss(fetch_text(url, timeout=10, retries=1), source)
            if rows:
                return url
        except Exception:
            continue
    return None


def article_date_from_url(url: str) -> str:
    if m := re.search(r"/a/(20\d{2})(\d{2})/(\d{2})/", url):
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00+00:00"
    if m := re.search(r"/(20\d{2})/(\d{1,2})-(\d{1,2})/", url):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00+00:00"
    if m := re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/", url):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00+00:00"
    if m := re.search(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", url):
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00+00:00"
    return utcnow()


def article_date_from_text(text: str, fallback_url: str) -> str:
    if m := re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", text):
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}T00:00:00+00:00"
    if m := re.search(r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})", text):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00+00:00"
    if m := re.search(r"\b([A-Z][a-z]{2,8})\s+(\d{1,2}),\s+(20\d{2})\b", text):
        try:
            dt = datetime.strptime(" ".join(m.groups()), "%B %d %Y").replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            try:
                dt = datetime.strptime(" ".join(m.groups()), "%b %d %Y").replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return article_date_from_url(fallback_url)


def absolute_url(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, href).split("#", 1)[0].rstrip("/")


def clean_anchor_title(text: str) -> str:
    text = strip_html(text)
    text = re.sub(r"^;\s*\d{1,2}/\d{1,2}/20\d{2}\s+", "", text)
    text = re.sub(r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}\s+", "", text)
    text = re.sub(r"^(?:statement|news|story|blog)\s+", "", text, flags=re.I)
    text = re.sub(r"\b(?:Network|Heritage Protection|Museum International|International Museum Day|ICOM Voices|statement)$", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip(" -|")


def parse_strict_web(html: str, source: dict, patterns: list[str], base_url: str, require_terms: bool = False, require_date_text: bool = False) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows, seen = [], set()
    compiled = [re.compile(p, re.I) for p in patterns]
    for anchor in soup.find_all("a", href=True):
        title = clean_anchor_title(anchor.get_text(" ", strip=True))
        anchor_text = anchor.get_text(" ", strip=True)
        if require_date_text and not re.search(r"\b\d{1,2}/\d{1,2}/20\d{2}\b|\b20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}\b|\b[A-Z][a-z]{2,8}\s+\d{1,2},\s+20\d{2}\b", anchor_text):
            continue
        if len(title) < 8:
            continue
        url = absolute_url(base_url, anchor["href"])
        if url in seen or not any(p.search(url) for p in compiled):
            continue
        haystack = f"{title} {url}".lower()
        if require_terms and not has_heritage_term(haystack):
            continue
        seen.add(url)
        pub_date = article_date_from_text(anchor_text, url)
        summary = ""
        if source_key(source) == "IUCN":
            try:
                article_html = fetch_text(url, timeout=10, retries=1)
                meta = BeautifulSoup(article_html, "html.parser")
                if found := meta.find("meta", attrs={"property": "og:updated_time"}):
                    pub_date = found.get("content") or pub_date
                if found := meta.find("meta", attrs={"property": "og:title"}):
                    title = clean_anchor_title(found.get("content") or title)
                if found := meta.find("meta", attrs={"property": "og:description"}):
                    summary = found.get("content") or ""
            except Exception:
                pass
        rows.append(article_from_source(source, title, url, pub_date, summary, {"web": True}))
    return rows[:20]


def parse_web(html: str, source: dict) -> list[dict]:
    sid = source_key(source)
    if sid == "IUCN":
        return parse_strict_web(html, source, [r"iucn\.org/(?:news|story|blog)/20\d{4}/"], "https://www.iucn.org", True)
    if sid == "ICOMOS":
        return parse_strict_web(html, source, [r"icomos\.org/news/[^/?#]+/$", r"icomos\.org/news/[^/?#]+$"], "https://www.icomos.org", False)
    if sid == "ICOM":
        return parse_strict_web(html, source, [r"icom\.museum/en/news/[^/?#]+/$", r"icom\.museum/en/news/[^/?#]+$"], "https://icom.museum", False)
    if sid == "NCHA":
        return parse_strict_web(html, source, [r"ncha\.gov\.cn/art/20\d{2}/\d{1,2}/\d{1,2}/art_\d+_\d+\.html$"], "http://www.ncha.gov.cn", True)
    if sid == "NFGA":
        return parse_strict_web(html, source, [r"forestry\.gov\.cn/(?:lyj/\d+/[a-z]+/20\d{6}/\d+\.html|c/www/[a-z]+/\d+\.jhtml)$"], "https://www.forestry.gov.cn", True)
    if sid == "Xinhua":
        return parse_strict_web(html, source, [r"(?:news\.cn|xinhuanet\.com)/culture/20\d{6}/[^/?#]+/c\.html$"], "https://www.news.cn", True)
    if sid == "EnglishHeritage":
        return parse_strict_web(html, source, [r"english-heritage\.org\.uk/about(?:-us)?/search-news/[^/?#]+$"], "https://www.english-heritage.org.uk", False, True)
    if sid == "ChinaDaily":
        return parse_strict_web(html, source, [r"chinadaily\.com\.cn/a/20\d{4}/\d{2}/WS[^/?#]+\.html$"], "https://www.chinadaily.com.cn", True)

    rows, seen = [], set()
    nav_words = {"home", "about", "contact", "privacy", "advertise", "subscribe", "newsletter"}
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href, title = m.group(1), clean_anchor_title(m.group(2))
        if not title or len(title) < 12:
            continue
        haystack = f"{title} {href}".lower()
        if title.strip().lower() in nav_words:
            continue
        specialist = source.get("source_tier") == "specialist_media"
        if not specialist and not has_heritage_term(haystack):
            continue
        if not href.startswith(("http://", "https://")):
            href = absolute_url(source["url"], href)
        if href in seen:
            continue
        seen.add(href)
        pub_date = article_date_from_url(href)
        if sid in {"ChinaJilin", "YCWB", "MDN", "PSMNews"}:
            try:
                article_html = fetch_text(href, timeout=10, retries=1)
                article_text = BeautifulSoup(article_html, "html.parser").get_text(" ", strip=True)
                pub_date = article_date_from_text(article_text, href)
            except Exception:
                pass
        rows.append(article_from_source(source, title, href, pub_date, "", {"web": True}))
    return rows[:20]


def article_from_source(source: dict, title: str, url: str, pub_date: str, summary: str, raw: dict) -> dict:
    return {
        "title_original": title,
        "title_zh": title if source.get("language") == "zh" else None,
        "source_name": source["name"],
        "source_tier": source["source_tier"],
        "trust_level": source["trust_level"],
        "language": source["language"],
        "country_region": source.get("country_or_region"),
        "pub_date": parse_date(pub_date),
        "url": url,
        "summary_zh": summary if source.get("language") == "zh" else None,
        "raw_content": json.dumps(raw | {"summary": summary}, ensure_ascii=False),
        "translation_status": "done" if source.get("language") == "zh" else "pending",
    }


def insert_articles(conn: sqlite3.Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    cols = list(rows[0].keys())
    sql = f"INSERT OR IGNORE INTO heritage_news ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})"
    before = conn.total_changes
    conn.executemany(sql, [[row.get(col) for col in cols] for row in rows])
    conn.commit()
    return conn.total_changes - before


def update_health(conn: sqlite3.Connection, source_name: str, ok: bool, count: int = 0) -> None:
    now = utcnow()
    row = conn.execute("SELECT * FROM source_health WHERE source_name=?", (source_name,)).fetchone()
    if row:
        failures = 0 if ok else row["failure_count_24h"] + 1
        total = row["total_articles"] + count
        status = "active" if ok else ("unstable" if failures >= 2 else "dormant")
        conn.execute(
            """UPDATE source_health SET last_successful_fetch=COALESCE(?, last_successful_fetch),
               failure_count_24h=?, total_articles=?, status=?, last_check=? WHERE source_name=?""",
            (now if ok else None, failures, total, status, now, source_name),
        )
    else:
        conn.execute(
            """INSERT INTO source_health
               (source_name,last_successful_fetch,failure_count_24h,total_articles,avg_articles_per_week,status,last_check)
               VALUES (?,?,?,?,?,?,?)""",
            (source_name, now if ok else None, 0 if ok else 1, count, None, "active" if ok else "dormant", now),
        )
    conn.commit()
