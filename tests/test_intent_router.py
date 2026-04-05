# tests/test_intent_router.py
"""
Unit tests for IntentRouter.
Tests: dispatch, confidence handling, personality integration.
"""

import pytest
import sys
from pathlib import Path


# === Mock Handlers ===

class MockMusicHandler:
    """Fake music handler for testing"""
    def __init__(self):
        self.calls = []
        
    def handle_play(self, entities):
        self.calls.append(("play", entities))
        return f"Playing {entities.get('song', 'music')}"
        
    def handle_pause(self, entities):
        self.calls.append(("pause", entities))
        return "Music paused"


class MockAlarmHandler:
    """Fake alarm handler for testing"""
    def __init__(self):
        self.calls = []
        
    def set_alarm(self, time, label=None):
        self.calls.append(("set", time, label))
        return f"Alarm set for {time}"
        
    def list_alarms(self):
        self.calls.append(("list",))
        return "No alarms set"


class MockAppHandler:
    """Fake app handler for testing"""
    def __init__(self):
        self.calls = []
        
    def open_app(self, app_name):
        self.calls.append(("open", app_name))
        return f"Opening {app_name}"
        
    def close_app(self, app_name):
        self.calls.append(("close", app_name))
        return f"Closing {app_name}"


class MockSearchHandler:
    """Fake search handler for testing"""
    def __init__(self):
        self.calls = []
        
    def search(self, query):
        self.calls.append(("search", query))
        return f"Searching for: {query}"


class MockSpeaker:
    """Fake speaker for testing"""
    def __init__(self):
        self.spoken = []
        
    def speak(self, text):
        self.spoken.append(text)


# === Tests ===

class TestIntentRouter:
    """Tests for IntentRouter dispatch"""
    
    @pytest.fixture
    def setup(self):
        """Set up router with mock handlers"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis"))
        
        from core.state_manager import StateManager
        from core.personality import JARVISPersonalityCore
        from core.intent_router import IntentRouter
        
        state = StateManager()
        personality = JARVISPersonalityCore(state)
        speaker = MockSpeaker()
        
        handlers = {
            "music": MockMusicHandler(),
            "alarm": MockAlarmHandler(),
            "apps": MockAppHandler(),
            "search": MockSearchHandler(),
        }
        
        router = IntentRouter(state, handlers, personality, speaker.speak)
        
        return {
            "router": router,
            "state": state,
            "handlers": handlers,
            "speaker": speaker,
        }
    
    # === Dispatch Tests ===
    
    def test_route_play_music(self, setup):
        """play_music intent should dispatch to music handler"""
        router = setup["router"]
        handlers = setup["handlers"]
        
        entities = {"song": "blinding lights"}
        result = router.route("play_music", entities)
        
        # Check handler was called
        assert len(handlers["music"].calls) > 0
        assert "play" in handlers["music"].calls[-1][0]
    
    def test_route_set_alarm(self, setup):
        """set_alarm intent should dispatch to alarm handler"""
        router = setup["router"]
        handlers = setup["handlers"]
        
        entities = {"time": "07:00"}
        result = router.route("set_alarm", entities)
        
        assert len(handlers["alarm"].calls) > 0
    
    def test_route_open_app(self, setup):
        """open_app intent should dispatch to app handler"""
        router = setup["router"]
        handlers = setup["handlers"]
        
        entities = {"app": "chrome"}
        result = router.route("open_app", entities)
        
        assert len(handlers["apps"].calls) > 0
        assert handlers["apps"].calls[-1][1] == "chrome"
    
    def test_route_search_web(self, setup):
        """search_web intent should dispatch to search handler"""
        router = setup["router"]
        handlers = setup["handlers"]
        
        entities = {"query": "python tutorials"}
        result = router.route("search_web", entities)
        
        assert len(handlers["search"].calls) > 0
    
    # === Unknown Intent Tests ===
    
    def test_route_unknown_intent(self, setup):
        """Unknown intent should return clarification"""
        router = setup["router"]
        
        result = router.route("unknown_xyz", {})
        
        # Should not crash, should return some response
        assert result is not None
        assert isinstance(result, str)
    
    def test_route_none_intent(self, setup):
        """None intent should be handled"""
        router = setup["router"]
        
        result = router.route(None, {})
        assert result is not None


class TestIntentRouterState:
    """Tests for router-state interaction"""
    
    @pytest.fixture
    def setup(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "jarvis"))
        
        from core.state_manager import StateManager
        from core.personality import JARVISPersonalityCore
        from core.intent_router import IntentRouter
        
        state = StateManager()
        personality = JARVISPersonalityCore(state)
        speaker = MockSpeaker()
        
        handlers = {
            "music": MockMusicHandler(),
            "alarm": MockAlarmHandler(),
            "apps": MockAppHandler(),
            "search": MockSearchHandler(),
        }
        
        router = IntentRouter(state, handlers, personality, speaker.speak)
        
        return {"router": router, "state": state}
    
    def test_state_updated_before_route(self, setup):
        """State should reflect intent before routing"""
        state = setup["state"]
        
        # Update state as would happen in pipeline
        state.update_intent("play_music", 0.9, {"song": "test"})
        
        s = state.get()
        assert s.current_intent == "play_music"
        assert s.intent_confidence == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
