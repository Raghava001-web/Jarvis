"""
World Monitor — JARVIS World Awareness Module
==============================================
Three capabilities:
  1. get_world_news()     - parallel fetch from BBC, Reuters, NYT, Al Jazeera
  2. search_web(query)    - DuckDuckGo HTML scrape (replaces broken DDG Instant Answers)
  3. fetch_url(url)       - raw page text (first 4000 chars, HTML stripped)

All results are returned as strings ready for the LLM to summarise.
TTL cache: 60 min for news, 10 min for search.
"""

import re
import time
import threading
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError
from xml.etree import ElementTree as ET

# ── Cache ──────────────────────────────────────────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()

NEWS_TTL = 3600   # 60 minutes
SEARCH_TTL = 600  # 10 minutes

def _cache_get(key: str) -> Optional[str]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < entry["ttl"]:
            return entry["data"]
    return None

def _cache_set(key: str, data: str, ttl: int):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}


# ── HTTP helper ────────────────────────────────────────────────────────────
_HEADERS = {"User-Agent": "JARVIS-WorldMonitor/2.0"}

def _http_get(url: str, timeout: int = 8) -> Optional[bytes]:
    try:
        req = Request(url, headers=_HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"[WORLD] HTTP error {url[:60]}: {e}")
        return None


# ── HTML strip ─────────────────────────────────────────────────────────────
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

def _strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 1. WORLD NEWS — parallel RSS from 4 major outlets
# ═══════════════════════════════════════════════════════════════════════════

RSS_FEEDS = {
    "global": {
        "BBC":       "https://feeds.bbci.co.uk/news/world/rss.xml",
        "REUTERS":   "https://feeds.reuters.com/reuters/topNews",
        "ALJAZEERA": "https://www.aljazeera.com/xml/rss/all.xml",
    },
    "health": {
        "BBC_HEALTH": "https://feeds.bbci.co.uk/news/health/rss.xml",
        "NYT_HEALTH": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    },
    "tech": {
        "TECHCRUNCH": "https://techcrunch.com/feed/",
        "WIRED":      "https://www.wired.com/feed/rss",
        "NYT_TECH":   "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    }
}


def _fetch_feed(source: str, url: str) -> list[dict]:
    """Fetch one RSS feed synchronously — called from threads."""
    raw = _http_get(url, timeout=6)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        items = root.findall(".//item")[:5]
        results = []
        for item in items:
            title = (item.findtext("title") or "").strip()
            desc  = _strip_html(item.findtext("description") or "")[:200]
            link  = (item.findtext("link") or "").strip()
            if title:
                results.append({"source": source, "title": title, "summary": desc, "link": link})
        return results
    except Exception as e:
        print(f"[WORLD] Feed parse error {source}: {e}")
        return []


def get_world_news(category: str = "global", max_items: int = 12) -> str:
    """
    Fetch top headlines for a specific category in parallel.
    Categories: global, health, tech.
    Returns a formatted string suitable for direct LLM ingestion.
    """
    category = category.lower()
    feeds = RSS_FEEDS.get(category, RSS_FEEDS["global"])

    cache_key = f"news_{category}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Parallel fetch using threads (no asyncio — keeps integration simple)
    results: list[dict] = []
    results_lock = threading.Lock()

    def _worker(source, url):
        items = _fetch_feed(source, url)
        with results_lock:
            results.extend(items)

    threads = [
        threading.Thread(target=_worker, args=(src, url), daemon=True)
        for src, url in feeds.items()
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=8)

    if not results:
        return f"{category.capitalize()} news feeds are currently unreachable, sir."

    lines = [f"=== {category.upper()} NEWS BRIEFING (LIVE) ===\n"]
    for item in results[:max_items]:
        lines.append(f"[{item['source']}] {item['title']}")
        if item["summary"]:
            lines.append(f"  {item['summary']}")
        lines.append("")

    briefing = "\n".join(lines)
    _cache_set(cache_key, briefing, NEWS_TTL)
    return briefing


def get_news_summary(category: str = "global") -> str:
    """
    Returns top 5 headlines with short summaries (2-3 lines each).
    """
    return get_world_news(category=category, max_items=5)


# ── Topic Monitoring ───────────────────────────────────────────────────────

_monitored_topics = set()

def monitor_topic(topic: str) -> str:
    """Add a topic to track repeated queries."""
    topic = topic.strip().lower()
    if not topic:
        return "Please specify a topic to monitor."
    _monitored_topics.add(topic)
    return f"Successfully added '{topic}' to monitored topics."

def get_monitored_updates() -> str:
    """Fetch recent headlines for all monitored topics."""
    if not _monitored_topics:
        return "No topics are currently being monitored."

    lines = ["=== MONITORED TOPICS UPDATE ===\n"]
    for topic in _monitored_topics:
        res = _search_news_rss(topic, max_results=3)
        lines.append(f"[Monitoring: {topic.upper()}]")
        if res:
            # Skip the '=== NEWS SEARCH...' header from _search_news_rss
            clean_res = "\n".join(res.split("\n")[2:])
            lines.append(clean_res)
        else:
            lines.append("  No new updates found.")
        lines.append("")
    return "\n".join(lines).strip()


# ═══════════════════════════════════════════════════════════════════════════
# 2. WEB SEARCH — DuckDuckGo HTML scrape (works for any query)
# ═══════════════════════════════════════════════════════════════════════════

def search_web(query: str, max_results: int = 5) -> str:
    """
    Scrape DuckDuckGo search results for any query.
    Returns titles + snippets as a string.
    Falls back to Google News RSS search if DDG fails.
    """
    cache_key = f"search:{query.lower()}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _search_ddg(query, max_results) or _search_news_rss(query, max_results)
    if result:
        _cache_set(cache_key, result, SEARCH_TTL)
        return result

    return f"No results found for '{query}', sir."


def _search_ddg(query: str, max_results: int) -> Optional[str]:
    """DuckDuckGo HTML scrape — extracts result titles and snippets."""
    from urllib.parse import quote_plus
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    raw = _http_get(url, timeout=8)
    if not raw:
        return None

    try:
        text = raw.decode("utf-8", errors="ignore")
        # Extract result blocks
        # DDG HTML has: <a class="result__a" ...>Title</a> and <a class="result__snippet">Snippet</a>
        title_pat = re.compile(
            r'class="result__a"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
        )
        snippet_pat = re.compile(
            r'class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
        )
        titles   = [_strip_html(m.group(1)) for m in title_pat.finditer(text)][:max_results]
        snippets = [_strip_html(m.group(1)) for m in snippet_pat.finditer(text)][:max_results]

        if not titles:
            return None

        lines = [f"=== WEB SEARCH: {query} ===\n"]
        for i, title in enumerate(titles):
            snippet = snippets[i] if i < len(snippets) else ""
            lines.append(f"{i+1}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
        return "\n".join(lines)

    except Exception as e:
        print(f"[WORLD] DDG parse error: {e}")
        return None


def _search_news_rss(query: str, max_results: int) -> Optional[str]:
    """Fallback: Google News RSS keyword search."""
    from urllib.parse import quote_plus
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}"
    raw = _http_get(url, timeout=6)
    if not raw:
        return None
    try:
        root = ET.fromstring(raw)
        items = root.findall(".//item")[:max_results]
        if not items:
            return None
        lines = [f"=== NEWS SEARCH: {query} ===\n"]
        for item in items:
            title = (item.findtext("title") or "").strip()
            if title:
                lines.append(f"• {title}")
        return "\n".join(lines)
    except Exception as e:
        print(f"[WORLD] News RSS search error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. URL FETCH — read raw page content
# ═══════════════════════════════════════════════════════════════════════════

def fetch_url(url: str, max_chars: int = 4000) -> str:
    """
    Fetch and return the text content of any URL.
    HTML tags are stripped. Returns first max_chars characters.
    """
    raw = _http_get(url, timeout=10)
    if not raw:
        return f"Unable to fetch {url}, sir."
    try:
        text = raw.decode("utf-8", errors="ignore")
        text = _strip_html(text)
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"
        return text
    except Exception as e:
        return f"Failed to parse content from {url}: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. WORLD BRIEFING — summarised daily status (uses Gemini if available)
# ═══════════════════════════════════════════════════════════════════════════

def get_world_briefing(knowledge=None) -> str:
    """
    Fetch world news then use Gemini to produce a 3-sentence spoken summary.
    If no LLM is available, returns the raw multi-source headlines.
    """
    raw = get_world_news(max_items=10)

    if knowledge and hasattr(knowledge, "answer_question"):
        try:
            prompt = (
                "You are JARVIS. Based on these live world headlines, give a 2-3 sentence "
                "spoken summary of what is happening in the world right now. "
                "Be concise, sharp, and informative. No bullet points — speak in sentences.\n\n"
                f"{raw}"
            )
            summary = knowledge.answer_question(prompt)
            if summary and len(summary) > 20:
                return summary
        except Exception as e:
            print(f"[WORLD] Briefing summarise error: {e}")

    # Fallback: first 5 headlines formatted as spoken text
    lines = [l for l in raw.split("\n") if l.startswith("[") or l.startswith("•")]
    if lines:
        return "Here are the latest world headlines, sir. " + " | ".join(lines[:5])
    return raw


# ═══════════════════════════════════════════════════════════════════════════
# Singleton accessor
# ═══════════════════════════════════════════════════════════════════════════

class WorldMonitor:
    """Thin class wrapper so the server can hold an instance."""

    def __init__(self, knowledge=None):
        self.knowledge = knowledge
        print("[WORLD] World Monitor ready.")

    def get_news(self, category: str = "global") -> str:
        return get_world_news(category=category)

    def get_news_summary(self, category: str = "global") -> str:
        return get_news_summary(category=category)
        
    def monitor(self, topic: str) -> str:
        return monitor_topic(topic)
        
    def get_updates(self) -> str:
        return get_monitored_updates()

    def search(self, query: str) -> str:
        return search_web(query)

    def fetch(self, url: str) -> str:
        return fetch_url(url)

    def briefing(self) -> str:
        return get_world_briefing(self.knowledge)


_instance: Optional[WorldMonitor] = None

def get_world_monitor(knowledge=None) -> WorldMonitor:
    global _instance
    if _instance is None:
        _instance = WorldMonitor(knowledge)
    return _instance
