"""
News Handler - Headlines & News
Voice-optimized RSS news delivery
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime, timedelta


class NewsHandler:
    """Handles news fetching and delivery - Enhanced with Hacker News"""

    MAX_HEADLINE_LENGTH = 140
    
    # Hacker News API endpoints (from Materialistic reference)
    HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, perception):
        print("[NEWS] Initializing Enhanced News Handler...")
        self.perception = perception

        self.data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        self.data_dir.mkdir(exist_ok=True)

        self.cache_file = self.data_dir / "news_cache.json"
        self.cache_duration = timedelta(hours=1)

        # Google News RSS categories
        self.categories = {
            "general": "https://news.google.com/rss",
            "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
            "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
            "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
            "entertainment": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB",
            "politics": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRE5qY285M0FtVnVLQUFQAQ",
            "economics": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
            "economy": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
            "world": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
            "global": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
            # NEW: Hacker News categories
            "tech": "hackernews_top",
            "hacker": "hackernews_top",
            "hackernews": "hackernews_top",
            "startups": "hackernews_top",
            "ask": "hackernews_ask",
            "show": "hackernews_show"
        }

        print("[NEWS] Enhanced Handler Ready (with Hacker News)")

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self, cache):
        with open(self.cache_file, "w") as f:
            json.dump(cache, f, indent=2)

    def _get_cached_news(self, category):
        cache = self._load_cache()
        if category in cache:
            ts = datetime.fromisoformat(cache[category]["timestamp"])
            if datetime.now() - ts < self.cache_duration:
                return cache[category]["items"]
        return None

    def get_headlines(self, count=5, category="general"):
        cached = self._get_cached_news(category)
        if cached:
            self._speak_headlines(cached[:count], category)
            return True

        # Check if Hacker News category
        url_or_type = self.categories.get(category, self.categories["general"])
        
        if url_or_type.startswith("hackernews_"):
            return self._get_hacker_news(count, url_or_type.replace("hackernews_", ""), category)
        
        # Regular Google News RSS
        try:
            response = requests.get(url_or_type, timeout=8)
            if response.status_code != 200:
                raise RuntimeError("Bad response")

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:count]

            headlines = []
            for item in items:
                title = item.title.text.strip()
                title = self._clean_title(title)
                headlines.append({"title": title})

            cache = self._load_cache()
            cache[category] = {
                "timestamp": datetime.now().isoformat(),
                "items": headlines
            }
            self._save_cache(cache)

            self._speak_headlines(headlines, category)
            return True

        except Exception as e:
            print(f"ERROR: News error: {e}")
            self.perception.speak("Unable to fetch news right now, sir.")
            return False

    def _get_hacker_news(self, count, hn_type, category):
        """Fetch news from Hacker News API (Materialistic style)"""
        try:
            # Get story IDs
            if hn_type == "top":
                url = f"{self.HN_API_BASE}/topstories.json"
            elif hn_type == "ask":
                url = f"{self.HN_API_BASE}/askstories.json"
            elif hn_type == "show":
                url = f"{self.HN_API_BASE}/showstories.json"
            else:
                url = f"{self.HN_API_BASE}/topstories.json"
            
            response = requests.get(url, timeout=8)
            story_ids = response.json()[:count]
            
            headlines = []
            for story_id in story_ids:
                item_url = f"{self.HN_API_BASE}/item/{story_id}.json"
                item_response = requests.get(item_url, timeout=5)
                item = item_response.json()
                
                if item and 'title' in item:
                    title = self._clean_title(item['title'])
                    score = item.get('score', 0)
                    headlines.append({
                        "title": title,
                        "score": score,
                        "url": item.get('url', '')
                    })
            
            # Cache results
            cache = self._load_cache()
            cache[category] = {
                "timestamp": datetime.now().isoformat(),
                "items": headlines
            }
            self._save_cache(cache)
            
            self._speak_headlines(headlines, f"Hacker News {hn_type}")
            return True
            
        except Exception as e:
            print(f"[NEWS] Hacker News error: {e}")
            self.perception.speak("Unable to fetch Hacker News right now, sir.")
            return False

    def search_news(self, keyword, count=5):
        """Search news by keyword (Flutter NewsApp style)"""
        try:
            # Use Google News search
            search_url = f"https://news.google.com/rss/search?q={keyword}"
            response = requests.get(search_url, timeout=8)
            
            if response.status_code != 200:
                raise RuntimeError("Search failed")
            
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:count]
            
            headlines = []
            for item in items:
                title = item.title.text.strip()
                title = self._clean_title(title)
                headlines.append({"title": title})
            
            if headlines:
                self.perception.speak(f"Here are {len(headlines)} results for {keyword}, sir.")
                for i, h in enumerate(headlines, 1):
                    self.perception.speak(f"{i}: {h['title']}")
                return True
            else:
                self.perception.speak(f"No news found for {keyword}, sir.")
                return False
                
        except Exception as e:
            print(f"[NEWS] Search error: {e}")
            self.perception.speak(f"Unable to search news for {keyword}, sir.")
            return False

    def get_news(self, category="general", count=5):
        """Unified method for getting news - returns data dict"""
        cached = self._get_cached_news(category)
        if cached:
            return {"items": [h['title'] for h in cached[:count]]}
        
        # Fetch fresh
        url_or_type = self.categories.get(category, self.categories["general"])
        
        if url_or_type.startswith("hackernews_"):
            return self._get_hacker_news_data(count, url_or_type.replace("hackernews_", ""))
        
        try:
            response = requests.get(url_or_type, timeout=8)
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:count]
            headlines = [self._clean_title(item.title.text.strip()) for item in items]
            
            # Cache
            cache = self._load_cache()
            cache[category] = {
                "timestamp": datetime.now().isoformat(),
                "items": [{"title": h} for h in headlines]
            }
            self._save_cache(cache)
            
            return {"items": headlines}
        except:
            return {"items": []}

    def _get_hacker_news_data(self, count, hn_type):
        """Get Hacker News as data dict"""
        try:
            if hn_type == "top":
                url = f"{self.HN_API_BASE}/topstories.json"
            elif hn_type == "ask":
                url = f"{self.HN_API_BASE}/askstories.json"
            else:
                url = f"{self.HN_API_BASE}/topstories.json"
            
            response = requests.get(url, timeout=8)
            story_ids = response.json()[:count]
            
            headlines = []
            for story_id in story_ids[:count]:
                item_url = f"{self.HN_API_BASE}/item/{story_id}.json"
                item = requests.get(item_url, timeout=5).json()
                if item and 'title' in item:
                    headlines.append(self._clean_title(item['title']))
            
            return {"items": headlines}
        except:
            return {"items": []}

    def _clean_title(self, title):
        title = title.replace("&apos;", "'").replace("&quot;", '"')
        if len(title) > self.MAX_HEADLINE_LENGTH:
            title = title[:self.MAX_HEADLINE_LENGTH].rsplit(" ", 1)[0] + "..."
        return title

    def _speak_headlines(self, headlines, category):
        self.perception.speak(f"Here are the top {len(headlines)} {category} headlines, sir.")
        for i, h in enumerate(headlines, 1):
            self.perception.speak(f"Headline {i}: {h['title']}")

    def get_category_news(self, category, count=5):
        return self.get_headlines(count, category)
