"""
AI Search Handler - Production Grade
=====================================
- Better result ranking with BM25-like scoring
- Proper deduplication
- Retry logic and timeouts
- Source weighting
- Citation discipline
"""

import requests
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re
import time


class SearchMode(Enum):
    """Search modes inspired by Perplexica"""
    SPEED = "speed"        # Quick answers, single source
    BALANCED = "balanced"  # Web + AI summary
    QUALITY = "quality"    # Deep research, multiple sources
    ACADEMIC = "academic"  # Research focus


class SearchSource(Enum):
    """Search sources"""
    WEB = "web"
    REDDIT = "reddit"
    NEWS = "news"
    ACADEMIC = "academic"


@dataclass
class SearchResult:
    """Search result with ranking"""
    title: str
    snippet: str
    url: str = ""
    source: str = "web"
    score: float = 0.0  # Ranking score
    timestamp: Optional[datetime] = None
    
    def __hash__(self):
        return hash(self.url or self.title)


@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    results: List[SearchResult]
    summary: str = ""
    sources_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "balanced"
    
    @property
    def citations(self) -> List[str]:
        """Get unique citations"""
        return list(set(r.url for r in self.results if r.url))


class RequestManager:
    """Handles HTTP requests with retry and rate limiting"""
    
    DEFAULT_HEADERS = {
        "User-Agent": "JARVIS/2.0 (AI Assistant)",
        "Accept": "application/json, text/html",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.last_request: Dict[str, float] = {}
        self.min_interval = 0.5  # Minimum seconds between requests to same domain
        
    def get(
        self,
        url: str,
        params: Dict = None,
        timeout: float = 5.0,
        retries: int = 2,
    ) -> Optional[requests.Response]:
        """Make GET request with retry logic"""
        domain = url.split("/")[2] if "/" in url else url
        
        # Rate limiting
        if domain in self.last_request:
            elapsed = time.time() - self.last_request[domain]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
                
        for attempt in range(retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                self.last_request[domain] = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                else:
                    break
                    
            except requests.RequestException as e:
                if attempt < retries:
                    time.sleep((attempt + 1) * 0.5)
                else:
                    print(f"[AI-SEARCH] Request failed: {e}")
                    
        return None


class ResultRanker:
    """BM25-inspired result ranking"""
    
    def __init__(self):
        self.k1 = 1.5
        self.b = 0.75
        
    def score(self, result: SearchResult, query: str, source_weight: float = 1.0) -> float:
        """Score a result based on query relevance"""
        query_terms = set(query.lower().split())
        
        # Combine title and snippet for matching
        text = f"{result.title} {result.snippet}".lower()
        text_terms = text.split()
        
        # Term frequency score
        tf_score = 0
        for term in query_terms:
            count = text.count(term)
            if count > 0:
                # BM25-like term frequency
                tf_score += (count * (self.k1 + 1)) / (count + self.k1)
                
        # Title bonus (terms in title are more important)
        title_lower = result.title.lower()
        title_bonus = sum(1 for term in query_terms if term in title_lower) * 0.5
        
        # Length normalization
        avg_len = 100
        length_norm = 1 - self.b + self.b * (len(text) / avg_len)
        
        # Freshness bonus (if timestamp available)
        freshness = 0
        if result.timestamp:
            days_old = (datetime.now() - result.timestamp).days
            if days_old < 7:
                freshness = 0.3
            elif days_old < 30:
                freshness = 0.1
                
        # Final score
        score = (tf_score + title_bonus) / length_norm + freshness
        score *= source_weight
        
        return score
        
    def rank(self, results: List[SearchResult], query: str, 
             source_weights: Dict[str, float] = None) -> List[SearchResult]:
        """Rank and sort results"""
        if source_weights is None:
            source_weights = {"duckduckgo": 1.0, "news": 1.1, "reddit": 0.8}
            
        for result in results:
            weight = source_weights.get(result.source, 1.0)
            result.score = self.score(result, query, weight)
            
        return sorted(results, key=lambda r: -r.score)


class ResultDeduplicator:
    """Removes duplicate results"""
    
    @staticmethod
    def deduplicate(results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results by URL or similar title"""
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        unique = []
        
        for result in results:
            # Check URL uniqueness
            url_key = result.url.split("?")[0].lower() if result.url else ""
            if url_key and url_key in seen_urls:
                continue
                
            # Check title similarity (simple)
            title_key = re.sub(r'[^a-z0-9]', '', result.title.lower())[:50]
            if title_key and title_key in seen_titles:
                continue
                
            if url_key:
                seen_urls.add(url_key)
            if title_key:
                seen_titles.add(title_key)
                
            unique.append(result)
            
        return unique


class AISearchHandler:
    """
    Production-grade AI search handler.
    Multi-source, ranked, deduplicated.
    """
    
    SOURCE_WEIGHTS = {
        "duckduckgo": 1.0,
        "news": 1.2,  # News often more relevant
        "reddit": 0.8,  # Reddit slightly lower
    }
    
    def __init__(self, perception=None, ai_brain=None):
        print("[AI-SEARCH] Initializing AI Search Handler...")
        self.perception = perception
        self.ai_brain = ai_brain
        
        # Data directory
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.request_manager = RequestManager()
        self.ranker = ResultRanker()
        self.deduplicator = ResultDeduplicator()
        
        # History and memory
        self.history_path = self.data_dir / "search_history.json"
        self.memory_path = self.data_dir / "search_memory.json"
        self.history: List[Dict] = []
        self.memory: List[Dict] = []
        self._load_data()
        
        print("[AI-SEARCH] Handler Ready")
        
    def _load_data(self):
        """Load history and memory"""
        try:
            if self.history_path.exists():
                with open(self.history_path, 'r') as f:
                    self.history = json.load(f)
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    self.memory = json.load(f)
        except:
            pass
            
    def _save_history(self):
        """Save search history"""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)
        except:
            pass
            
    def _save_memory(self):
        """Save memory"""
        try:
            with open(self.memory_path, 'w') as f:
                json.dump(self.memory[-500:], f, indent=2)
        except:
            pass
            
    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.BALANCED,
        sources: List[SearchSource] = None,
    ) -> SearchResponse:
        """
        Main search function.
        Returns ranked, deduplicated results with optional AI summary.
        """
        if sources is None:
            if mode == SearchMode.SPEED:
                sources = [SearchSource.WEB]
            elif mode == SearchMode.QUALITY:
                sources = [SearchSource.WEB, SearchSource.NEWS, SearchSource.REDDIT]
            else:
                sources = [SearchSource.WEB, SearchSource.NEWS]
                
        # Collect results from sources
        all_results: List[SearchResult] = []
        sources_used = []
        
        for source in sources:
            results = self._fetch_source(source, query)
            if results:
                all_results.extend(results)
                sources_used.append(source.value)
                
        # Deduplicate
        unique_results = self.deduplicator.deduplicate(all_results)
        
        # Rank
        ranked_results = self.ranker.rank(
            unique_results, query, self.SOURCE_WEIGHTS
        )
        
        # Limit results
        limit = 3 if mode == SearchMode.SPEED else 10
        top_results = ranked_results[:limit]
        
        # Generate summary
        summary = ""
        if mode != SearchMode.SPEED and self.ai_brain and top_results:
            summary = self._generate_summary(query, top_results)
            
        # Build response
        response = SearchResponse(
            query=query,
            results=top_results,
            summary=summary,
            sources_used=sources_used,
            mode=mode.value,
        )
        
        # Log to history
        self.history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(top_results),
            "sources": sources_used,
        })
        self._save_history()
        
        return response
        
    def _fetch_source(self, source: SearchSource, query: str) -> List[SearchResult]:
        """Fetch from a specific source"""
        if source == SearchSource.WEB:
            return self._search_duckduckgo(query)
        elif source == SearchSource.NEWS:
            return self._search_news(query)
        elif source == SearchSource.REDDIT:
            return self._search_reddit(query)
        return []
        
    def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """DuckDuckGo Instant Answers"""
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        response = self.request_manager.get(
            "https://api.duckduckgo.com/",
            params=params,
            timeout=5.0,
        )
        
        if not response:
            return []
            
        try:
            data = response.json()
            results = []
            
            # Abstract (main answer)
            if data.get("Abstract"):
                results.append(SearchResult(
                    title=data.get("Heading", query),
                    snippet=data["Abstract"],
                    url=data.get("AbstractURL", ""),
                    source="duckduckgo",
                ))
                
            # Related topics
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(SearchResult(
                        title=topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        snippet=topic["Text"],
                        url=topic.get("FirstURL", ""),
                        source="duckduckgo",
                    ))
                    
            return results
            
        except Exception as e:
            print(f"[AI-SEARCH] DDG parse error: {e}")
            return []
            
    def _search_news(self, query: str) -> List[SearchResult]:
        """Google News RSS"""
        response = self.request_manager.get(
            f"https://news.google.com/rss/search?q={query}",
            timeout=5.0,
        )
        
        if not response:
            return []
            
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "xml")
            
            results = []
            for item in soup.find_all("item")[:5]:
                pub_date = None
                if item.pubDate:
                    try:
                        pub_date = datetime.strptime(
                            item.pubDate.text.strip()[:25],
                            "%a, %d %b %Y %H:%M:%S"
                        )
                    except:
                        pass
                        
                results.append(SearchResult(
                    title=item.title.text.strip() if item.title else "",
                    snippet=item.title.text.strip() if item.title else "",
                    url=item.link.text.strip() if item.link else "",
                    source="news",
                    timestamp=pub_date,
                ))
                
            return results
            
        except ImportError:
            print("[AI-SEARCH] BeautifulSoup not installed: pip install beautifulsoup4 lxml")
            return []
        except Exception as e:
            print(f"[AI-SEARCH] News parse error: {e}")
            return []
            
    def _search_reddit(self, query: str) -> List[SearchResult]:
        """Reddit JSON API"""
        response = self.request_manager.get(
            f"https://www.reddit.com/search.json?q={query}&limit=5",
            timeout=5.0,
        )
        
        if not response:
            return []
            
        try:
            data = response.json()
            results = []
            
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                
                # Parse timestamp
                created = None
                if post_data.get("created_utc"):
                    created = datetime.fromtimestamp(post_data["created_utc"])
                    
                snippet = post_data.get("selftext", "")[:200] or post_data.get("title", "")
                
                results.append(SearchResult(
                    title=post_data.get("title", ""),
                    snippet=snippet,
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    source="reddit",
                    timestamp=created,
                ))
                
            return results
            
        except Exception as e:
            print(f"[AI-SEARCH] Reddit parse error: {e}")
            return []
            
    def _generate_summary(self, query: str, results: List[SearchResult]) -> str:
        """Generate AI summary with citations"""
        if not self.ai_brain:
            return results[0].snippet if results else ""
            
        try:
            # Build context with citations
            context_parts = []
            for i, r in enumerate(results[:5], 1):
                context_parts.append(f"[{i}] {r.title}: {r.snippet}")
                
            context = "\n".join(context_parts)
            
            prompt = f"""Based on these search results for '{query}', provide a concise 2-3 sentence summary.
Include citation numbers in brackets like [1] when referencing specific sources.

Results:
{context}

Summary:"""
            
            if hasattr(self.ai_brain, 'quick_answer'):
                return self.ai_brain.quick_answer(prompt)
            elif hasattr(self.ai_brain, 'chat'):
                return self.ai_brain.chat(prompt)
                
        except Exception as e:
            print(f"[AI-SEARCH] Summary error: {e}")
            
        return results[0].snippet if results else ""
        
    def quick_answer(self, question: str) -> str:
        """Get a quick answer"""
        response = self.search(question, mode=SearchMode.SPEED)
        return response.summary or (response.results[0].snippet if response.results else "I couldn't find an answer.")
        
    def deep_research(self, topic: str) -> SearchResponse:
        """Deep research with all sources"""
        return self.search(
            topic,
            mode=SearchMode.QUALITY,
            sources=[SearchSource.WEB, SearchSource.NEWS, SearchSource.REDDIT]
        )
        
    def remember(self, fact: str, category: str = "general") -> bool:
        """Store a fact in memory"""
        self.memory.append({
            "fact": fact,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "keywords": list(set(re.findall(r'\b\w{4,}\b', fact.lower())))[:10],
        })
        self._save_memory()
        return True
        
    def recall(self, query: str, limit: int = 5) -> List[str]:
        """Recall facts from memory"""
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        
        scored = []
        for mem in self.memory:
            keywords = set(mem.get("keywords", []))
            overlap = len(query_words & keywords)
            if overlap > 0:
                scored.append((overlap, mem["fact"]))
                
        scored.sort(reverse=True, key=lambda x: x[0])
        return [f for _, f in scored[:limit]]
        
    def speak_result(self, query: str):
        """Search and speak result"""
        answer = self.quick_answer(query)
        
        if self.perception:
            self.perception.speak(answer)
        else:
            print(f"[AI-SEARCH] {answer}")
            
        return answer


# Singleton
_handler = None

def get_ai_search(perception=None, ai_brain=None) -> AISearchHandler:
    global _handler
    if _handler is None:
        _handler = AISearchHandler(perception, ai_brain)
    return _handler
