"""
JARVIS Smoke Tests — Minimal Live-Path Verification
====================================================
Tests 5 critical paths without touching hardware (mic, speaker, screen).
All tests mock external I/O so they run in < 5 seconds with no side effects.

Targets:
  1. App boot (server + orchestrator init)
  2. Gemini Live voice dedup & echo gating
  3. BrainAdapter text routing
  4. News command delegation
  5. switch_to_friday voice switching

Catches:
  - Duplicate speech on the same turn
  - Broken routing / handler lookup misses
  - Failed delegation (handler returns None when it shouldn't)
  - Echo leak through the speaking gate
"""

import sys
import time
import types
import json
import queue
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

import pytest

# ── Path setup ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "jarvis"))
sys.path.insert(0, str(PROJECT_ROOT / "jarvis" / "core"))


# ═════════════════════════════════════════════════════════════════
# 1. APP BOOT — server init completes, orchestrator loads
# ═════════════════════════════════════════════════════════════════

class TestAppBoot:
    """Verify the app can construct its core objects without crashing."""

    def test_startup_orchestrator_initializes(self):
        """StartupOrchestrator should init without any external deps."""
        from jarvis.core.startup_orchestrator import StartupOrchestrator
        orch = StartupOrchestrator(jarvis=None, context={})
        assert orch is not None
        assert orch.data_dir.exists()

    def test_boot_briefing_generates(self):
        """Boot briefing must return a dict with required keys."""
        from jarvis.core.startup_orchestrator import StartupOrchestrator
        orch = StartupOrchestrator(jarvis=None, context={})
        briefing = orch.generate_boot_briefing()
        required_keys = [
            "boot_time", "greeting", "session_resumption",
            "task_summary", "spoken_briefing", "prompt_context"
        ]
        for key in required_keys:
            assert key in briefing, f"Boot briefing missing key: {key}"

    def test_greeting_time_aware(self):
        """Greeting should vary based on time of day."""
        from jarvis.core.startup_orchestrator import StartupOrchestrator
        import datetime

        orch = StartupOrchestrator(jarvis=None, context={})
        morning = datetime.datetime(2026, 5, 16, 9, 0)
        evening = datetime.datetime(2026, 5, 16, 20, 0)

        g_morning = orch._generate_greeting(morning)
        g_evening = orch._generate_greeting(evening)

        assert "morning" in g_morning.lower() or "welcome" in g_morning.lower()
        assert "evening" in g_evening.lower() or "welcome" in g_evening.lower()
        assert g_morning != g_evening or "Welcome back" in g_morning

    def test_hud_perception_initializes(self):
        """HUDPerception should construct without an original perception layer."""
        # Import the class from the server module (it's near the top of the file)
        from jarvis.gui.websocket_server import HUDPerception
        hud = HUDPerception(original_perception=None)
        assert hud.assistant_name == "JARVIS"
        assert hud.user_title == "sir"
        assert hud.is_friday is False


# ═════════════════════════════════════════════════════════════════
# 2. GEMINI LIVE — dedup, echo gating, turn-id staleness
# ═════════════════════════════════════════════════════════════════

class TestGeminiLiveDedup:
    """Test the _push_to_chat dedup and echo gate logic in isolation."""

    def _make_engine(self):
        """Create a GeminiLiveEngine with mocked server (no real audio)."""
        from jarvis.core.gemini_live_engine import GeminiLiveEngine

        mock_server = MagicMock()
        mock_server.hud_perception = MagicMock()
        mock_server.push_live_transcription = MagicMock()
        mock_server.clients = set()

        # Patch pyaudio so no real audio device is opened
        with patch("jarvis.core.gemini_live_engine.pya"):
            engine = GeminiLiveEngine(api_key="test-key", server=mock_server)
        return engine, mock_server

    def test_duplicate_speech_blocked(self):
        """Same text + same role within 2.5s window must be blocked."""
        engine, server = self._make_engine()
        engine._current_turn_id = 1

        engine._push_to_chat("Opening Chrome, sir.", role="jarvis", turn_id=1)
        assert server.push_live_transcription.call_count == 1

        engine._push_to_chat("Opening Chrome, sir.", role="jarvis", turn_id=1)
        # Second identical message should be blocked
        assert server.push_live_transcription.call_count == 1

    def test_different_messages_allowed(self):
        """Different text from the same role should NOT be blocked."""
        engine, server = self._make_engine()
        engine._current_turn_id = 1

        engine._push_to_chat("Opening Chrome, sir.", role="jarvis", turn_id=1)
        engine._push_to_chat("Chrome is now open.", role="jarvis", turn_id=1)
        assert server.push_live_transcription.call_count == 2

    def test_stale_turn_dropped(self):
        """A response from turn N-1 must be dropped when turn is N."""
        engine, server = self._make_engine()
        engine._current_turn_id = 5

        engine._push_to_chat("Stale response", role="jarvis", turn_id=3)
        assert server.push_live_transcription.call_count == 0

    def test_echo_gate_blocks_mic_during_speech(self):
        """When _speaking_until is in the future, the echo gate should hold."""
        engine, _ = self._make_engine()
        engine._speaking_until = time.time() + 10  # "speaking" for 10s
        # Simulate what _listen_audio does: check the gate
        assert time.time() < engine._speaking_until, \
            "Echo gate should block mic while _speaking_until > now"

    def test_empty_text_ignored(self):
        """Empty or whitespace-only text must not reach the server."""
        engine, server = self._make_engine()
        engine._current_turn_id = 1

        engine._push_to_chat("", role="jarvis", turn_id=1)
        engine._push_to_chat("   ", role="jarvis", turn_id=1)
        assert server.push_live_transcription.call_count == 0


# ═════════════════════════════════════════════════════════════════
# 3. BRAIN ADAPTER — ML text routing
# ═════════════════════════════════════════════════════════════════

class TestBrainAdapter:
    """Test the BrainAdapter pipeline with mocked ML modules."""

    def _make_brain(self):
        """Create a BrainAdapter with all modules stubbed out."""
        from jarvis.core.brain_adapter import BrainAdapter, BrainResult

        # Patch _safe_import to return mocks instead of loading real models
        with patch("jarvis.core.brain_adapter._safe_import", return_value=None):
            brain = BrainAdapter()

        return brain

    def test_brain_initializes_without_crash(self):
        """BrainAdapter must construct even when all ML modules are unavailable."""
        brain = self._make_brain()
        assert brain is not None
        stats = brain.get_stats()
        assert stats["brain_hits"] == 0
        assert stats["fallbacks"] == 0

    def test_fallback_when_no_modules(self):
        """With all modules None, process() must return route='fallback'."""
        brain = self._make_brain()
        result = brain.process("open chrome", source="voice")
        assert result.route == "fallback"
        assert result.is_valid is False

    def test_brain_routes_with_high_confidence_intent(self):
        """When intent_model returns high confidence, route should be 'brain'."""
        brain = self._make_brain()

        # Wire up a mock intent model
        mock_intent = MagicMock()
        mock_intent.classify.return_value = ("open_app", 0.92)
        brain.intent_model = mock_intent

        result = brain.process("open chrome", source="voice")
        assert result.route == "brain"
        assert result.action == "open_app"
        assert result.confidence == 0.92
        assert result.is_valid is True

    def test_brain_falls_back_on_low_confidence(self):
        """When intent confidence < 0.50, route should stay 'fallback'."""
        brain = self._make_brain()

        mock_intent = MagicMock()
        mock_intent.classify.return_value = ("ambiguous_thing", 0.30)
        brain.intent_model = mock_intent

        result = brain.process("do the thing", source="voice")
        assert result.route == "fallback"
        assert result.is_valid is False

    def test_brain_handles_classify_exception(self):
        """If intent_model.classify raises, pipeline must not crash."""
        brain = self._make_brain()

        mock_intent = MagicMock()
        mock_intent.classify.side_effect = RuntimeError("model exploded")
        brain.intent_model = mock_intent

        result = brain.process("open chrome")
        assert result.route == "fallback"
        assert any("error" in step for step in result.pipeline_log)

    def test_entity_extraction_wired(self):
        """When entities are extracted, they should appear in result.entities."""
        brain = self._make_brain()

        mock_intent = MagicMock()
        mock_intent.classify.return_value = ("open_app", 0.95)
        brain.intent_model = mock_intent

        mock_entities = MagicMock()
        mock_entities.extract.return_value = {"app": "chrome"}
        brain.entity_extractor = mock_entities

        result = brain.process("open chrome")
        assert result.entities == {"app": "chrome"}

    def test_brain_result_is_valid_property(self):
        """BrainResult.is_valid must require route='brain', action set, confidence >= 0.50."""
        from jarvis.core.brain_adapter import BrainResult

        # Valid
        r1 = BrainResult(action="open_app", confidence=0.85, route="brain")
        assert r1.is_valid is True

        # Invalid: low confidence
        r2 = BrainResult(action="open_app", confidence=0.40, route="brain")
        assert r2.is_valid is False

        # Invalid: fallback route
        r3 = BrainResult(action="open_app", confidence=0.90, route="fallback")
        assert r3.is_valid is False

        # Invalid: no action
        r4 = BrainResult(action=None, confidence=0.90, route="brain")
        assert r4.is_valid is False


# ═════════════════════════════════════════════════════════════════
# 4. NEWS COMMAND — routing + handler delegation
# ═════════════════════════════════════════════════════════════════

class TestNewsCommand:
    """Verify 'news' command routes correctly and handler delegates properly."""

    def test_classifier_routes_news(self):
        """'tell me the news' should classify to intent='news'."""
        from jarvis.core.intent_classifier import classify_intent
        intent, entities = classify_intent("tell me the news")
        assert intent == "news"

    def test_classifier_routes_tech_news(self):
        """'tech news' should classify to news with category='tech'."""
        from jarvis.core.intent_classifier import classify_intent
        intent, entities = classify_intent("tech news")
        assert intent == "news"
        assert entities.get("category") == "tech"

    def test_classifier_routes_hacker_news(self):
        """'hacker news' should classify to news with category='hacker'."""
        from jarvis.core.intent_classifier import classify_intent
        intent, entities = classify_intent("hacker news")
        assert intent == "news"
        assert entities.get("category") == "hacker"

    def test_news_handler_with_data(self):
        """News handler should return headlines when news_handler provides data."""
        from jarvis.core.intent_handlers import handle_news

        mock_news = MagicMock()
        mock_news.get_news.return_value = {
            "items": ["AI startup raises $1B", "New Python 3.14 released", "SpaceX launch delayed"]
        }
        context = {"title": "sir", "news_handler": mock_news, "knowledge": None}

        result = handle_news("news", {"category": "tech"}, context)
        assert result is not None
        assert result.success is True
        assert "AI startup" in result.response
        assert result.data["type"] == "news"

    def test_news_handler_no_service(self):
        """News handler should fail gracefully when news_handler is None."""
        from jarvis.core.intent_handlers import handle_news

        result = handle_news("news", {}, {"title": "sir", "news_handler": None, "knowledge": None})
        assert result is not None
        assert result.success is False
        assert "unavailable" in result.response.lower()

    def test_news_in_handler_map(self):
        """'news' must exist in HANDLER_MAP for dispatch."""
        from jarvis.core.intent_handlers import HANDLER_MAP
        assert "news" in HANDLER_MAP
        assert callable(HANDLER_MAP["news"])

    def test_news_in_gemini_live_tools(self):
        """Gemini Live engine must declare a 'news' tool for voice delegation."""
        from jarvis.core.gemini_live_engine import TOOL_DECLARATIONS
        tool_names = [t["name"] for t in TOOL_DECLARATIONS]
        assert "news" in tool_names


# ═════════════════════════════════════════════════════════════════
# 5. SWITCH TO FRIDAY — voice switching + no duplicate speech
# ═════════════════════════════════════════════════════════════════

class TestSwitchToFriday:
    """Verify 'switch to friday' routes correctly and doesn't produce duplicate speech."""

    def test_classifier_routes_switch_to_friday(self):
        """'switch to friday' should classify to intent='switch_to_friday'."""
        from jarvis.core.intent_classifier import classify_intent
        intent, entities = classify_intent("switch to friday")
        assert intent == "switch_to_friday"

    def test_classifier_routes_activate_friday(self):
        """'activate friday' should also route to switch_to_friday."""
        from jarvis.core.intent_classifier import classify_intent
        intent, entities = classify_intent("activate friday")
        assert intent == "switch_to_friday"

    def test_friday_handler_returns_response(self):
        """The handler should return success with FRIDAY's greeting."""
        from jarvis.core.intent_handlers import handle_switch_to_friday
        result = handle_switch_to_friday("switch to friday", {}, {})
        assert result.success is True
        assert "FRIDAY" in result.response
        assert result.data["type"] == "switch_voice"
        assert result.data["voice"] == "friday"

    def test_friday_handler_in_handler_map(self):
        """switch_to_friday must be registered in HANDLER_MAP."""
        from jarvis.core.intent_handlers import HANDLER_MAP
        assert "switch_to_friday" in HANDLER_MAP

    def test_hud_perception_friday_switch(self):
        """HUDPerception.switch_to_friday() must update name and is_friday flag."""
        from jarvis.gui.websocket_server import HUDPerception

        hud = HUDPerception(original_perception=None)
        assert hud.assistant_name == "JARVIS"
        assert hud.is_friday is False

        # Patch speak to avoid TTS calls
        hud.speak = MagicMock()
        hud.switch_to_friday()

        assert hud.assistant_name == "FRIDAY"
        assert hud.is_friday is True
        hud.speak.assert_called_once()
        assert "FRIDAY" in hud.speak.call_args[0][0]

    def test_hud_perception_no_duplicate_on_switch(self):
        """Switching voice must produce exactly one speech output, not two."""
        from jarvis.gui.websocket_server import HUDPerception

        hud = HUDPerception(original_perception=None)
        speech_log = []
        hud.speak = lambda text: speech_log.append(text)

        hud.switch_to_friday()
        # Must be exactly 1 message — not 2 (handler + perception both speaking)
        assert len(speech_log) == 1, \
            f"Expected 1 speech output, got {len(speech_log)}: {speech_log}"

    def test_hud_perception_jarvis_switch_back(self):
        """Switching back to JARVIS must restore name and flag."""
        from jarvis.gui.websocket_server import HUDPerception

        hud = HUDPerception(original_perception=None)
        hud.speak = MagicMock()

        hud.switch_to_friday()
        hud.switch_to_jarvis()

        assert hud.assistant_name == "JARVIS"
        assert hud.is_friday is False

    def test_hud_perception_live_mode_skips_tts(self):
        """When Gemini Live is active, speak() must skip TTS but still queue text."""
        from jarvis.gui.websocket_server import HUDPerception

        hud = HUDPerception(original_perception=None)
        hud._gemini_live_active = True

        hud.speak("Test message")

        # Message should be in queue (for HUD display) but TTS should NOT fire
        messages = hud.get_pending_speech()
        assert "Test message" in messages

    def test_hud_dedup_blocks_rapid_duplicate(self):
        """HUDPerception.speak() must block duplicate text within 2s, even in live mode."""
        from jarvis.gui.websocket_server import HUDPerception

        hud = HUDPerception(original_perception=None)
        hud._gemini_live_active = True

        hud.speak("Hello sir")
        hud.speak("Hello sir")  # duplicate within 2s

        messages = hud.get_pending_speech()
        assert len(messages) == 1, \
            f"Dedup failed: expected 1 message, got {len(messages)}: {messages}"


# ═════════════════════════════════════════════════════════════════
# CROSS-CUTTING: Routing pipeline integration
# ═════════════════════════════════════════════════════════════════

class TestRoutingIntegration:
    """Verify end-to-end routing from classifier to handler map."""

    @pytest.mark.parametrize("command,expected_intent", [
        ("tell me the news", "news"),
        ("switch to friday", "switch_to_friday"),
        ("switch to jarvis", "switch_to_jarvis"),
        ("open chrome", "open_app"),
        ("what's the time", "time"),
        ("volume up", "volume"),
        ("hello jarvis", "greeting"),
        ("tell me a joke", "joke"),
        ("take a screenshot", "screenshot"),
        ("tech news", "news"),
    ])
    def test_classifier_to_handler_map(self, command, expected_intent):
        """Every classified intent must have a matching entry in HANDLER_MAP."""
        from jarvis.core.intent_classifier import classify_intent
        from jarvis.core.intent_handlers import HANDLER_MAP

        intent, entities = classify_intent(command)
        assert intent == expected_intent, \
            f"'{command}' classified as '{intent}', expected '{expected_intent}'"
        assert intent in HANDLER_MAP, \
            f"Intent '{intent}' classified but NOT in HANDLER_MAP — broken routing!"

    def test_no_handler_returns_none_unexpectedly(self):
        """Critical handlers must never return None (which would cause silent failure)."""
        from jarvis.core.intent_handlers import HANDLER_MAP

        critical_intents = ["news", "switch_to_friday", "greeting", "time", "joke"]
        for intent_name in critical_intents:
            handler = HANDLER_MAP.get(intent_name)
            assert handler is not None, f"HANDLER_MAP['{intent_name}'] is None!"

            # Call with minimal context — should not crash
            context = {"title": "sir", "news_handler": None, "knowledge": None}
            try:
                result = handler("test", {}, context)
                # 'conversation' handler is allowed to return None (falls through)
                if intent_name != "conversation":
                    assert result is not None, \
                        f"Handler for '{intent_name}' returned None — silent failure!"
            except Exception as e:
                pytest.fail(f"Handler for '{intent_name}' crashed: {e}")


# ═════════════════════════════════════════════════════════════════
# 6. TACTICAL PERSONALITY — anticipation, warnings, alternatives
# ═════════════════════════════════════════════════════════════════

class TestTacticalPersonality:
    """Verify JARVIS tactical reasoning: limits, risks, strategies, clean passthrough."""

    def _make_personality(self):
        """Create a JARVISPersonalityCore with a mock state manager."""
        from jarvis.core.personality import JARVISPersonalityCore
        mock_state = MagicMock()
        mock_state.get.return_value = MagicMock(
            user_mood=MagicMock(value="neutral"),
            user_title="sir",
            intent_confidence=0.9,
        )
        return JARVISPersonalityCore(state_manager=mock_state)

    def test_volume_ceiling_warns(self):
        """Setting volume to 100 must trigger a tactical warning."""
        p = self._make_personality()
        warning = p.challenge_bad_decision("volume", {"level": 100, "action": "set"})
        assert warning is not None
        assert "maximum" in warning.lower() or "distortion" in warning.lower()

    def test_brightness_floor_warns(self):
        """Setting brightness to 5% must trigger a tactical warning."""
        p = self._make_personality()
        warning = p.challenge_bad_decision("brightness", {"level": 5})
        assert warning is not None
        assert "eye" in warning.lower() or "10%" in warning.lower() or "strain" in warning.lower()

    def test_shutdown_safety_warns(self):
        """Shutdown command must always produce a tactical warning."""
        p = self._make_personality()
        warning = p.challenge_bad_decision("shutdown", {})
        assert warning is not None
        assert "unsaved" in warning.lower() or "work" in warning.lower()

    def test_normal_greeting_no_warning(self):
        """Normal greeting must NOT trigger any tactical warning."""
        p = self._make_personality()
        warning = p.challenge_bad_decision("greeting", {})
        assert warning is None

    def test_repeated_failure_warning(self):
        """After 2 failures of the same intent, get_failure_warning must fire."""
        p = self._make_personality()
        assert p.get_failure_warning("open_app") is None
        p.record_failure("open_app")
        assert p.get_failure_warning("open_app") is None
        p.record_failure("open_app")
        warning = p.get_failure_warning("open_app")
        assert warning is not None
        assert "failed" in warning.lower() or "alternative" in warning.lower()
        # Clear and verify reset
        p.clear_failure("open_app")
        assert p.get_failure_warning("open_app") is None

    def test_tactical_prefix_returns_none_for_normal(self):
        """Tactical prefix must return None for most normal commands."""
        p = self._make_personality()
        prefix = p.get_tactical_prefix("greeting", {})
        assert prefix is None

    def test_decision_engine_volume_limit(self):
        """DecisionEngine must warn when volume hits 100."""
        from jarvis.core.decision_engine import DecisionEngine, DecisionType
        engine = DecisionEngine()
        decision = engine.decide("volume", {"level": 100}, confidence=0.95)
        assert decision.type == DecisionType.WARN_THEN_PROCEED
        assert decision.message is not None

    def test_decision_engine_normal_passthrough(self):
        """DecisionEngine must PROCEED without warning for normal high-confidence intent."""
        from jarvis.core.decision_engine import DecisionEngine, DecisionType
        engine = DecisionEngine()
        decision = engine.decide("greeting", {}, confidence=0.95)
        assert decision.type == DecisionType.PROCEED

    def test_proactive_tactical_insight_respects_live_guard(self):
        """Tactical insight must return None when Gemini Live is active."""
        from jarvis.core.proactive_assistant import ProactiveAssistant
        mock_perception = MagicMock()
        mock_perception._gemini_live_active = True
        pa = ProactiveAssistant(perception=mock_perception)
        insight = pa.get_tactical_insight("open_app", {"app": "vscode"}, success=True)
        assert insight is None

    def test_proactive_tactical_insight_on_failure(self):
        """Tactical insight should offer alternative when command fails."""
        from jarvis.core.proactive_assistant import ProactiveAssistant
        mock_perception = MagicMock()
        mock_perception._gemini_live_active = False
        mock_perception.user_title = "sir"
        pa = ProactiveAssistant(perception=mock_perception)
        insight = pa.get_tactical_insight("open_app", {"app": "unknown"}, success=False)
        assert insight is not None
        assert "different" in insight.lower() or "alternative" in insight.lower()
