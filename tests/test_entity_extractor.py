# tests/test_entity_extractor.py
"""
Unit tests for EntityExtractor.
Tests: music, alarms, apps, search queries.
"""

import pytest
import sys
from pathlib import Path


class TestEntityExtractor:
    """Tests for entity extraction"""
    
    @pytest.fixture
    def extractor(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis"))
        from core.entity_extractor import EntityExtractor
        return EntityExtractor()
    
    # === Music Entities ===
    
    def test_extract_song_simple(self, extractor):
        """Extract song from simple request"""
        entities = extractor.extract("play blinding lights", "play_music")
        assert "song" in entities
        assert "blinding" in entities["song"].lower()
    
    def test_extract_song_with_artist(self, extractor):
        """Extract song and artist"""
        entities = extractor.extract(
            "play blinding lights by the weeknd on spotify", 
            "play_music"
        )
        assert "song" in entities
        assert "artist" in entities or "app" in entities
    
    def test_extract_music_app(self, extractor):
        """Extract music app preference"""
        entities = extractor.extract("play music on spotify", "play_music")
        assert entities.get("app") == "spotify"
    
    # === Alarm Entities ===
    
    def test_extract_absolute_time(self, extractor):
        """Extract absolute time"""
        entities = extractor.extract("set alarm for 7:30 am", "set_alarm")
        assert "time" in entities
        assert "07:30" in entities["time"]
    
    def test_extract_relative_time(self, extractor):
        """Extract relative time"""
        entities = extractor.extract("remind me in 10 minutes", "set_alarm")
        assert "time" in entities
        assert entities.get("relative") == True
    
    def test_extract_pm_time(self, extractor):
        """Extract PM time correctly"""
        entities = extractor.extract("set alarm for 3 pm", "set_alarm")
        assert "time" in entities
        # 3 PM should be 15:00
        assert "15" in entities["time"]
    
    # === App Entities ===
    
    def test_extract_app_name(self, extractor):
        """Extract app name"""
        entities = extractor.extract("open chrome", "open_app")
        assert entities.get("app") == "chrome"
    
    def test_extract_app_with_please(self, extractor):
        """Extract app even with 'please'"""
        entities = extractor.extract("please open vscode", "open_app")
        assert "vscode" in entities.get("app", "").lower()
    
    def test_extract_known_app(self, extractor):
        """Known apps should be recognized"""
        entities = extractor.extract("launch discord", "open_app")
        assert entities.get("app") == "discord"
    
    # === Search Entities ===
    
    def test_extract_search_query(self, extractor):
        """Extract search query"""
        entities = extractor.extract("search for python tutorials", "search_web")
        assert "query" in entities
        assert "python" in entities["query"]
    
    # === Edge Cases ===
    
    def test_empty_text(self, extractor):
        """Empty text should return empty entities"""
        entities = extractor.extract("", "play_music")
        assert isinstance(entities, dict)
    
    def test_unknown_intent(self, extractor):
        """Unknown intent should return empty or minimal entities"""
        entities = extractor.extract("do something", "unknown_intent")
        assert isinstance(entities, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
