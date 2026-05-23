"""
Weather Handler - Weather information with auto-location
Provides current weather, temperature, humidity, wind speed
"""

import os
import json
import requests
from typing import Optional, Dict
from datetime import datetime


class WeatherHandler:
    """Handles weather queries with automatic location detection"""
    
    def __init__(self, perception=None):
        print("[WEATHER] Initializing Weather Handler...")
        self.perception = perception
        
        # API configuration
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.geocoder_available = False
        
        # Check for geocoder
        try:
            import geocoder
            self.geocoder_available = True
            print("[WEATHER] geocoder available for location")
        except ImportError:
            print("[WEATHER] geocoder not available - manual location required")
        
        # Cache
        self.cached_location = None
        self.location_cache_time = None
        self.cached_weather = None
        self.cache_time = None
        self.cache_duration = 600  # 10 minutes
        self.location_cache_duration = 3600  # 1 hour
        
        print("[WEATHER] Weather Handler Ready")
    
    def _get_title(self) -> str:
        """Get user title from perception layer"""
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        """Speak text via perception layer"""
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[WEATHER] {text}")
    
    def get_location(self) -> Optional[Dict]:
        """Get current location using IP geolocation"""
        if self.cached_location and getattr(self, 'location_cache_time', None):
            if (datetime.now() - self.location_cache_time).total_seconds() < getattr(self, 'location_cache_duration', 3600):
                return self.cached_location
        
        # Try gecoder first
        if self.geocoder_available:
            try:
                import geocoder
                g = geocoder.ip('me')
                
                if g.ok:
                    self.cached_location = {
                        "city": g.city,
                        "country": g.country,
                        "lat": g.latlng[0] if g.latlng else None,
                        "lon": g.latlng[1] if g.latlng else None
                    }
                    self.location_cache_time = datetime.now()
                    print(f"[WEATHER] Location from geocoder: {self.cached_location['city']}")
                    return self.cached_location
            except Exception as e:
                print(f"[WEATHER] Geocoder error: {e}")
        
        # Fallback to ipinfo.io (no library needed)
        try:
            response = requests.get('https://ipinfo.io/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', '')
                if city:
                    loc = data.get('loc', '').split(',')
                    self.cached_location = {
                        "city": city,
                        "country": data.get('country', ''),
                        "lat": float(loc[0]) if len(loc) > 1 else None,
                        "lon": float(loc[1]) if len(loc) > 1 else None
                    }
                    self.location_cache_time = datetime.now()
                    print(f"[WEATHER] Location from ipinfo.io: {city}")
                    return self.cached_location
        except Exception as e:
            print(f"[WEATHER] ipinfo.io error: {e}")
        
        return None
    
    def get_weather(self, city: str = None) -> Optional[Dict]:
        """Get current weather for a city or auto-detected location"""
        title = self._get_title()
        
        # Check cache
        if self.cached_weather and self.cache_time:
            if (datetime.now() - self.cache_time).total_seconds() < self.cache_duration:
                return self.cached_weather
        
        # Get location
        if not city:
            location = self.get_location()
            if location:
                city = location.get("city")
                lat = location.get("lat")
                lon = location.get("lon")
            else:
                self._speak(f"I couldn't determine your location, {title}. Please specify a city.")
                return None
        
        # Try free weather API (doesn't require key)
        weather = self._get_weather_free(city)
        
        if weather:
            self.cached_weather = weather
            self.cache_time = datetime.now()
            return weather
        
        # Fallback to OpenWeatherMap if key available
        if self.api_key:
            weather = self._get_weather_openweather(city)
            if weather:
                self.cached_weather = weather
                self.cache_time = datetime.now()
                return weather
        
        # Don't speak weather errors — they interrupt conversations randomly
        print(f"[WEATHER] Could not fetch weather data for {city}")
        return None
    
    def _get_weather_free(self, city: str) -> Optional[Dict]:
        """Get weather using free wttr.in API"""
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                
                return {
                    "city": city,
                    "temp_c": int(current.get("temp_C", 0)),
                    "temp_f": int(current.get("temp_F", 0)),
                    "feels_like_c": int(current.get("FeelsLikeC", 0)),
                    "humidity": int(current.get("humidity", 0)),
                    "wind_speed_kmh": int(current.get("windspeedKmph", 0)),
                    "wind_dir": current.get("winddir16Point", ""),
                    "description": current.get("weatherDesc", [{}])[0].get("value", ""),
                    "visibility": current.get("visibility", ""),
                    "uv_index": current.get("uvIndex", ""),
                    "source": "wttr.in"
                }
        except Exception as e:
            print(f"[WEATHER] wttr.in error: {e}")
        
        return None
    
    def _get_weather_openweather(self, city: str) -> Optional[Dict]:
        """Get weather using OpenWeatherMap API"""
        if not self.api_key:
            return None
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "city": data.get("name", city),
                    "temp_c": round(data["main"]["temp"]),
                    "feels_like_c": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "wind_speed_kmh": round(data["wind"]["speed"] * 3.6),  # m/s to km/h
                    "description": data["weather"][0]["description"],
                    "source": "OpenWeatherMap"
                }
        except Exception as e:
            print(f"[WEATHER] OpenWeatherMap error: {e}")
        
        return None
    
    def report_weather(self, city: str = None) -> bool:
        """Get and speak weather report"""
        title = self._get_title()
        
        weather = self.get_weather(city)
        
        if not weather:
            return False
        
        city_name = weather.get("city", "your location")
        temp = weather.get("temp_c", "unknown")
        feels_like = weather.get("feels_like_c", temp)
        humidity = weather.get("humidity", "unknown")
        wind = weather.get("wind_speed_kmh", "unknown")
        description = weather.get("description", "")
        
        report = f"The current weather in {city_name} is {temp} degrees Celsius"
        
        if description:
            report += f" with {description}"
        
        report += f". It feels like {feels_like} degrees."
        report += f" Humidity is at {humidity} percent"
        report += f" with wind speeds of {wind} kilometers per hour."
        
        self._speak(f"{report}")
        return True
    
    def get_temperature(self, city: str = None) -> bool:
        """Get just the temperature"""
        title = self._get_title()
        weather = self.get_weather(city)
        
        if weather:
            temp = weather.get("temp_c", "unknown")
            city_name = weather.get("city", "your location")
            self._speak(f"It's currently {temp} degrees Celsius in {city_name}, {title}.")
            return True
        
        return False
    
    def will_it_rain(self, city: str = None) -> bool:
        """Check if rain is expected"""
        title = self._get_title()
        weather = self.get_weather(city)
        
        if weather:
            description = weather.get("description", "").lower()
            rain_words = ["rain", "shower", "drizzle", "storm", "thunder"]
            
            if any(word in description for word in rain_words):
                self._speak(f"Yes {title}, it looks like rain is expected. {description}. You might want an umbrella.")
            else:
                self._speak(f"No rain expected at the moment, {title}. The forecast shows {description}.")
            return True
        
        return False
