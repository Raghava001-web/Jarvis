"""
jarvis/tools/web_tools.py
Registers 3 web-aware tools into the shared ToolRegistry.

Import this module once at startup to activate the tools:
    import jarvis.tools.web_tools
"""

from jarvis.tools.tool_registry import Tool, registry

# ── Implementations ────────────────────────────────────────────────────────
# Delegate to world_monitor.py (which handles caching, parallel fetch,
# HTML stripping, and fallback logic already).

def _web_search(args: dict) -> str:
    """Search the web for a query. Returns titles + snippets."""
    query = args.get("query", "").strip()
    if not query:
        return "Please provide a search query."
    from jarvis.core.world_monitor import search_web
    return search_web(query)


def _get_news(args: dict) -> str:
    """Fetch top global headlines from BBC, Al Jazeera, and Google News in parallel."""
    from jarvis.core.world_monitor import get_world_news
    return get_world_news(max_items=args.get("max_items", 8))


def _fetch_url(args: dict) -> str:
    """Fetch and return the plain-text content of a URL (first 4000 chars)."""
    url = args.get("url", "").strip()
    if not url:
        return "Please provide a URL."
    from jarvis.core.world_monitor import fetch_url
    return fetch_url(url)


# ── Register ───────────────────────────────────────────────────────────────

registry.register(Tool(
    name="web_search",
    description="Searches the web via DuckDuckGo and returns result titles and snippets.",
    function=_web_search,
))

registry.register(Tool(
    name="get_news",
    description="Fetches the latest global headlines from multiple sources in parallel.",
    function=_get_news,
))

registry.register(Tool(
    name="fetch_url",
    description="Fetches and returns the plain-text content of any URL.",
    function=_fetch_url,
))
