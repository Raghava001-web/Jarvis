"""
jarvis/tools/dispatcher.py
Flexible intent dispatcher — keyword groups + partial matching + clean query extraction.
No ML. No strict equality. Works on natural language variations.

Usage:
    from jarvis.tools.dispatcher import dispatch
    response = dispatch(user_input, fallback=my_llm_function)
"""

import re
import jarvis.tools.web_tools  # activates web_search, get_news, fetch_url
from jarvis.tools import registry

# ── Dynamic Tool Registration (Adhering to strict file constraints) ────────
from jarvis.core.world_monitor import get_news_summary, monitor_topic, get_monitored_updates
from jarvis.tools.tool_registry import Tool
from jarvis.core import memory
from jarvis.core import cache

def _do_monitor_topic(args):
    topic = args.get("topic", "")
    memory.add_monitored_topic(topic)
    return monitor_topic(topic)

registry.register(Tool(
    "get_news_summary", "Categories: health, tech, general",
    lambda args: get_news_summary(args.get("category", "general"))
))
registry.register(Tool(
    "monitor_topic", "Track repeated queries",
    _do_monitor_topic
))
registry.register(Tool(
    "get_monitored_updates", "Fetch all tracked topic updates",
    lambda args: get_monitored_updates()
))


# ── Query extractor ─────────────────────────────────────────────────────────

# Ordered longest-first so "search for" is stripped before "search"
_SEARCH_STRIP = sorted([
    "jarvis", "please", "can you", "could you", "i want to know",
    "tell me about", "tell me", "find out about", "find out",
    "find information about", "find information on", "find information",
    "look up information on", "look up information about", "look up",
    "search for information on", "search for information about",
    "search for", "search about", "search",
    "what is a", "what are", "what is",
    "who are", "who is",
    "how does", "how do", "how is",
    "where is", "when is", "why is",
    "give me info on", "give me information on",
    "get me info on", "get me information on",
    "research on", "research about", "research",
    "monitor", "track", "keep track of", "keep an eye on", "follow",
    "google", "bing",
    "explain", "describe", "define",
    "information on", "info on",
    "news about", "news on",
], key=len, reverse=True)


def _extract_category(text: str) -> str:
    """Detect specific news categories for the world monitor."""
    text_words = set(text.split())
    if text_words & {"health", "medical", "medicine", "doctor"}:
        return "health"
    if text_words & {"tech", "technology", "ai", "artificial intelligence", "software"}:
        return "tech"
    return "general"


def _clean_query(text: str) -> str:
    """Strip intent words and punctuation to isolate the actual topic/query."""
    q = text
    for phrase in _SEARCH_STRIP:
        # Only strip from the start or as a standalone word/phrase
        q = re.sub(rf'\b{re.escape(phrase)}\b', '', q, flags=re.IGNORECASE)
    # Remove leftover punctuation/whitespace
    q = re.sub(r'[?.,!]+', '', q).strip()
    return q or text.strip()   # fallback to raw text if everything was stripped


def _extract_url(text: str) -> str:
    """Pull the first http(s) URL from text."""
    match = re.search(r'https?://\S+', text)
    return match.group(0) if match else ""


# ── Intent definitions ──────────────────────────────────────────────────────
# Each intent has:
#   "groups"  : list of keyword groups — ANY word from ANY group must appear
#               (groups are AND-ed: all groups must have at least one hit)
#               Use a single group for OR-only matching.
#   "tool"    : registry tool name
#   "args"    : callable(text) -> dict
#
# Intents are checked top-to-bottom; first match wins.
# More specific intents (more groups) should appear first.

INTENTS = [

    # ── URL fetch — most specific, must have a real URL ───────────────────
    {
        "groups": [
            {"read", "fetch", "open", "load", "get"},
            {"link", "url", "page", "site", "website", "this"},
        ],
        "requires_url": True,
        "tool": "fetch_url",
        "args": lambda text: {"url": _extract_url(text)},
    },

    # ── Monitored Updates ───────────────────────────────────────────────────
    {
        "groups": [
            {"updates on my", "my topics", "monitored topics", "tracking updates", "saved topics"},
        ],
        "tool": "get_monitored_updates",
        "args": lambda text: {},
    },

    # ── Monitor Topic ───────────────────────────────────────────────────────
    {
        "groups": [
            {"monitor", "track", "keep track of", "follow"},
        ],
        "tool": "monitor_topic",
        "args": lambda text: {"topic": _clean_query(text)},
    },

    # ── Current events / news ─────────────────────────────────────────────
    {
        "groups": [
            {
                "news", "headlines", "happening", "current events",
                "latest updates", "breaking", "today's events",
                "whats going on", "what's going on", "updates",
                "world events", "briefing",
            }
        ],
        "tool": "get_news_summary",
        "args": lambda text: {"category": _extract_category(text)},
    },

    # ── Time ──────────────────────────────────────────────────────────────
    {
        "groups": [
            {"time", "clock"},
            {"current", "what", "tell", "now", "is"},
        ],
        "tool": "get_time",
        "args": lambda text: {},
    },

    # ── Greeting ──────────────────────────────────────────────────────────
    {
        "groups": [
            {"hello", "hey", "hi", "greet", "howdy"},
            {"jarvis",},
        ],
        "tool": "say_hello",
        "args": lambda text: {"name": "sir"},
    },

    # ── Web search — broad, catches "what is X", "who is X", etc. ─────────
    {
        "groups": [
            {
                "search", "look up", "lookup", "google", "bing",
                "find", "research", "explain", "define", "describe",
                "what is", "what are", "who is", "who are",
                "how does", "how do", "where is", "when is",
                "tell me about", "tell me", "give me info",
                "information about", "info about",
                "learn about",
            }
        ],
        "tool": "web_search",
        "args": lambda text: {"query": _clean_query(text)},
    },
]


# ── Matching engine ─────────────────────────────────────────────────────────

def _matches(text: str, intent: dict) -> bool:
    """
    Returns True if text satisfies all keyword groups in the intent.
    Each group is OR-ed internally; groups are AND-ed together.
    """
    if intent.get("requires_url") and not _extract_url(text):
        return False
    for group in intent["groups"]:
        # At least one keyword from this group must appear in text
        if not any(kw in text for kw in group):
            return False
    return True


# ── Caching rules ──────────────────────────────────────────────────────────
_TTL_RULES = {
    "get_news_summary": 300,  # 5 minutes
    "web_search": 600,        # 10 minutes
    "fetch_url": 900          # 15 minutes
}

# ── Public API ──────────────────────────────────────────────────────────────

def dispatch(user_input: str, fallback=None) -> str:
    raise DeprecationWarning("Please use async def dispatch() instead.")

async def dispatch(user_input: str, fallback=None) -> str:
    """
    Route user_input to a tool or the fallback callable asynchronously.

    Args:
        user_input: Raw text from user (voice or typed).
        fallback:   callable(str) -> str  (e.g. your LLM call).

    Returns:
        Response string.
    """
    text = user_input.lower().strip()
    memory.add_query(text)

    # ── Pre-routing decision layer ───────────────────────────────────────────
    # 1. Explicitly allow tools for real-time requests and direct actions
    is_realtime_or_action = any(w in text for w in [
        "latest", "news", "update", "current", "happening",
        "search", "find", "look up", "monitor", "track"
    ])

    # 2. Block basic knowledge queries from hitting web search unnecessarily
    if not is_realtime_or_action:
        is_definition = any(text.startswith(p) or p in text for p in [
            "what is a ", "what is an ", "what is ", "what are ",
            "who is ", "who are ", "explain ", "describe ", 
            "define ", "tell me about "
        ])
        if is_definition:
            print("[DISPATCH] Basic knowledge/definition detected -> LLM fallback")
            if callable(fallback):
                return fallback(user_input)
            return "Getting definition, sir."

    # ── Immediate follow-up handling ─────────────────────────────────────────
    if text in ["any updates", "updates"]:
        result = await registry.execute_async("get_monitored_updates", {})
        memory.set_last_tool("get_monitored_updates", {})
        return result

    if text in ["what about that", "tell me more", "more on that"]:
        last_tool = memory.get_last_tool()
        if last_tool:
            name, args = last_tool
            print(f"[DISPATCH] Memory context reuse -> tool={name} args={args}")
            return await registry.execute_async(name, args)
        return "I'm not sure what we were just talking about, sir."

    for intent in INTENTS:
        if _matches(text, intent):
            tool_name = intent["tool"]
            args = intent["args"](text)

            # Guard: if query extraction produced empty string, skip
            if tool_name == "web_search" and not args.get("query"):
                break

            cache_key = f"{tool_name}:{sorted(args.items())}"
            ttl = _TTL_RULES.get(tool_name, 0)

            if ttl > 0 and cache.is_valid(cache_key, ttl):
                print(f"[DISPATCH] CACHE HIT -> {tool_name!r}")
                result = cache.get(cache_key)
            else:
                print(f"[DISPATCH] matched={tool_name!r}  args={args}")
                result = await registry.execute_async(tool_name, args)
                if ttl > 0 and result:
                    cache.set(cache_key, result)

            memory.set_last_tool(tool_name, args)
            return result

    print("[DISPATCH] No intent matched -> fallback")
    if callable(fallback):
        return fallback(user_input)
    return "I'm not sure how to help with that. Can you rephrase, sir?"
