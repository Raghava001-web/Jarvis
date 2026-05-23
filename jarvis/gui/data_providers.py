"""
JARVIS Data Providers
=====================
Extracted from websocket_server.py — pure data-gathering functions
for system stats, weather, news, and title helpers.

These functions produce HUD-ready dicts. They do NOT touch
websocket transport, client sessions, or audio playback.
"""

import os
import psutil
from typing import Dict, Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_system_stats() -> Dict[str, Any]:
    """Get current system statistics.
    
    Returns HUD-ready dict with keys: type, cpu, memory, battery, charging, disk.
    """
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent if os.name == 'nt' else psutil.disk_usage('/').percent
        
        battery = 100
        charging = False
        try:
            bat = psutil.sensors_battery()
            if bat:
                battery = bat.percent
                charging = bat.power_plugged
        except:
            pass
        
        return {
            'type': 'status',
            'cpu': round(cpu),
            'memory': round(memory),
            'battery': round(battery),
            'charging': charging,
            'disk': round(disk)
        }
    except Exception as e:
        return {'type': 'status', 'cpu': 0, 'memory': 0, 'battery': 100}


# ═══════════════════════════════════════════════════════════════════════════════
# WEATHER DATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_weather_data(weather_handler=None, city: Optional[str] = None) -> Dict[str, Any]:
    """Get weather data from handler or return fallback.
    
    Args:
        weather_handler: WeatherHandler instance (optional)
        city: City name override (optional)
    
    Returns HUD-ready dict with keys: type, temp, condition, location, humidity, wind.
    """
    try:
        if weather_handler:
            # Use correct method - get_weather() not get_weather_data()
            data = weather_handler.get_weather(city)
            if data:
                return {
                    'type': 'weather',
                    'temp': data.get('temp_c', 24),
                    'condition': data.get('description', 'Clear'),
                    'location': data.get('city', city or 'Hyderabad'),
                    'humidity': data.get('humidity', 50),
                    'wind': data.get('wind_speed_kmh', 10)
                }
    except Exception as e:
        print(f"[DataProvider] Weather error: {e}")
    
    return {
        'type': 'weather',
        'temp': 24,
        'condition': 'Partly Cloudy',
        'location': city or 'Hyderabad',
        'humidity': 65,
        'wind': 12
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS DATA
# ═══════════════════════════════════════════════════════════════════════════════

# Fallback headlines by category (used when NewsHandler is unavailable)
_FALLBACK_HEADLINES = {
    'economics': [
        'Global markets rally on positive economic data',
        'Central banks signal cautious approach to rates',
        'Tech sector leads economic recovery trends',
        'Consumer spending shows strong momentum',
        'Trade negotiations progress between major economies'
    ],
    'business': [
        'Major tech companies report strong earnings',
        'Startup funding reaches new quarterly high',
        'Retail sector adapts to changing consumer habits',
        'Energy companies invest in renewable transition',
        'Financial services embrace digital transformation'
    ],
    'politics': [
        'Parliament debates new economic policies',
        'International summit addresses global challenges',
        'Electoral reforms proposed by commission',
        'Defense budget allocation under review',
        'Environmental legislation gains support'
    ],
    'technology': [
        'AI research achieves breakthrough in reasoning',
        'Quantum computing milestone announced',
        'Cybersecurity concerns drive new regulations',
        'Space exploration reaches new frontiers',
        'Clean energy tech innovations accelerate'
    ],
    'sports': [
        'Championship finals set for weekend showdown',
        'National team announces squad for tournament',
        'Record-breaking performance stuns spectators',
        'Transfer window sees major moves',
        'Youth program produces rising stars'
    ]
}

_DEFAULT_HEADLINES = [
    'AI research achieves breakthrough in reasoning',
    'Global markets rally on positive indicators',
    'Space exploration milestone announced',
    'Tech innovations reshape digital landscape',
    'Climate summit announces new agreements'
]

# Location → category mapping
_LOCATION_CATEGORIES = {
    'india': 'general',
    'usa': 'general',
    'china': 'world',
    'europe': 'world',
    'africa': 'world',
    'washington': 'politics',
    'silicon valley': 'technology',
    'wall street': 'business',
    'london': 'business',
    'tokyo': 'technology'
}


def get_news_data(news_handler=None, category: str = 'general',
                  count: int = 5, location: Optional[str] = None) -> Dict[str, Any]:
    """Get news headlines by category or location.
    
    Args:
        news_handler: NewsHandler instance (optional)
        category: News category (general, technology, sports, etc.)
        count: Number of headlines to return
        location: Location override (maps to category)
    
    Returns HUD-ready dict with keys: type, items, category.
    """
    try:
        if news_handler:
            # Map location to category if provided
            if location:
                category = _LOCATION_CATEGORIES.get(location.lower(), 'world')
            
            # Delegate entirely to NewsHandler (handles caching, HN, RSS)
            result = news_handler.get_news(category, count)
            if result and result.get('items'):
                return {'type': 'news', 'items': result['items'][:count], 'category': category}
    except Exception as e:
        print(f"[DataProvider] News error: {e}")
    
    # Fallback
    default = _FALLBACK_HEADLINES.get(category, _DEFAULT_HEADLINES)
    return {
        'type': 'news',
        'items': default[:count],
        'category': category
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE HELPERS — reduce "sir" usage
# ═══════════════════════════════════════════════════════════════════════════════

import random


def maybe_title(title: str, chance: float = 0.25) -> str:
    """Returns ', {title}' only 25% of the time to avoid excessive formality"""
    if random.random() < chance:
        return f", {title}"
    return ""


def always_title(title: str) -> str:
    """Always returns ', {title}' for important responses"""
    return f", {title}"
