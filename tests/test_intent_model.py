# tests/test_intent_model.py
"""
Unit tests for IntentModel.
Tests: classification, rejection, ambiguity detection, confidence.
"""

import pytest
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis"))


class TestIntentModel:
    """Tests for IntentModel classification"""
    
    @pytest.fixture(scope="class")
    def model(self):
        """Load model once for all tests (expensive startup)"""
        from core.intent_model import IntentModel
        return IntentModel(lazy=False)
    
    # === Core Intent Tests ===
    
    def test_play_music_intent(self, model):
        """'play music' should classify as play_music with high confidence"""
        intent, conf = model.classify("play some music")
        assert intent == "play_music", f"Expected play_music, got {intent}"
        assert conf > 0.70, f"Low confidence: {conf}"
    
    def test_play_music_with_song(self, model):
        """Song name should still classify as play_music"""
        intent, conf = model.classify("play blinding lights")
        assert intent == "play_music"
        assert conf > 0.60  # Song names can lower confidence slightly
    
    def test_set_alarm_intent(self, model):
        """'set alarm for X' should classify as set_alarm"""
        intent, conf = model.classify("set alarm for 7 am")
        assert intent == "set_alarm", f"Expected set_alarm, got {intent}"
        assert conf > 0.70
    
    def test_set_alarm_reminder(self, model):
        """'remind me' should also classify as set_alarm"""
        intent, conf = model.classify("remind me in 10 minutes")
        assert intent == "set_alarm"
        assert conf > 0.55  # Natural language variation
    
    def test_open_app_intent(self, model):
        """'open X' should classify as open_app"""
        intent, conf = model.classify("open chrome")
        assert intent == "open_app", f"Expected open_app, got {intent}"
        assert conf > 0.60  # This was the weak link
    
    def test_open_app_launch(self, model):
        """'launch X' should also classify as open_app"""
        intent, conf = model.classify("launch vscode")
        assert intent == "open_app"
        assert conf > 0.65
    
    def test_get_time_intent(self, model):
        """'what time is it' should classify as get_time"""
        intent, conf = model.classify("what time is it")
        assert intent == "get_time", f"Expected get_time, got {intent}"
        assert conf > 0.70
    
    def test_greeting_intent(self, model):
        """'hello jarvis' should classify as greeting"""
        intent, conf = model.classify("hello jarvis")
        assert intent == "greeting", f"Expected greeting, got {intent}"
        assert conf > 0.60
    
    def test_volume_up_intent(self, model):
        """Volume control intents"""
        intent, conf = model.classify("turn up the volume")
        # May be ambiguous with brightness_up - accept either
        assert intent in ["volume_up", "AMBIGUOUS"], f"Expected volume_up or AMBIGUOUS, got {intent}"
    
    def test_search_web_intent(self, model):
        """'search for X' should classify as search_web"""
        intent, conf = model.classify("google python tutorials")
        # More explicit search signal
        assert intent in ["search_web", "ask_question"], f"Expected search intent, got {intent}"
    
    # === Rejection Tests ===
    
    def test_rejection_for_nonsense(self, model):
        """Gibberish should be rejected (None)"""
        intent, conf = model.classify("blorb florp zingo wango")
        assert intent is None, f"Should reject gibberish, got {intent}"
    
    def test_rejection_low_confidence(self, model):
        """Very ambiguous input should be rejected or marked ambiguous"""
        intent, conf = model.classify("do the thing")
        # Should either be rejected or ambiguous
        assert intent is None or intent == "AMBIGUOUS", f"Got: {intent}"
    
    # === Confidence Tests ===
    
    def test_high_confidence_for_clear_intent(self, model):
        """Clear, explicit commands should have high confidence"""
        _, conf = model.classify("play music on spotify")
        assert conf > 0.75, f"Expected high confidence, got {conf}"
    
    def test_lower_confidence_for_vague_intent(self, model):
        """Vague commands may have lower confidence"""
        _, conf = model.classify("play something")
        # Still should match, but potentially lower confidence
        assert conf > 0.50
    
    # === Top Intents ===
    
    def test_get_top_intents(self, model):
        """get_top_intents should return ranked list"""
        top = model.get_top_intents("play some music", top_k=3)
        assert len(top) == 3
        assert top[0][0] == "play_music"  # First should be play_music
        assert top[0][1] >= top[1][1]  # Scores should be descending


class TestIntentModelEdgeCases:
    """Edge case tests"""
    
    @pytest.fixture(scope="class")
    def model(self):
        from core.intent_model import IntentModel
        return IntentModel(lazy=False)
    
    def test_empty_string(self, model):
        """Empty string should handle gracefully"""
        intent, conf = model.classify("")
        assert intent is None or conf < 0.5
    
    def test_single_word(self, model):
        """Single word commands"""
        intent, _ = model.classify("play")
        # Should still work, likely play_music
        assert intent in ["play_music", None, "AMBIGUOUS"]
    
    def test_very_long_input(self, model):
        """Long input shouldn't crash"""
        long_text = "play music " * 50
        intent, conf = model.classify(long_text)
        assert intent == "play_music"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
