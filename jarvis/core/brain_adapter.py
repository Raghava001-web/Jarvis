"""
Brain Adapter - Thin bridge between WebSocket server and advanced JARVIS brain
==============================================================================
Routes command-like inputs through the advanced ML pipeline:
    input_priority -> intent_model -> entity_extractor -> decision_engine -> emotion_router

Falls back gracefully if any module is unavailable.
Does NOT replace the keyword engine - augments it.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


# ── Structured Result ──────────────────────────────────────────
@dataclass
class BrainResult:
    """Structured result from the advanced brain pipeline."""
    action: Optional[str] = None          # Resolved intent name
    response: Optional[str] = None        # Optional pre-built response
    confidence: float = 0.0               # Classification confidence
    route: str = "fallback"               # "brain" or "fallback"
    entities: Dict[str, Any] = field(default_factory=dict)
    decision_type: Optional[str] = None   # proceed / warn / clarify / refuse
    decision_message: Optional[str] = None
    priority: str = "normal"              # normal / urgent / gentle / cautious
    mood: Optional[str] = None            # Detected user mood
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_log: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Brain produced a usable result (not a fallback)."""
        return self.route == "brain" and self.action is not None and self.confidence >= 0.50


# ── Module Loading (fault-tolerant) ────────────────────────────
def _safe_import(label, factory):
    """Import a module safely; return None on failure."""
    try:
        obj = factory()
        print(f"[BRAIN] {label} loaded")
        return obj
    except Exception as e:
        print(f"[BRAIN] {label} unavailable: {e}")
        return None


class BrainAdapter:
    """
    Thin adapter that wires the advanced JARVIS modules into the live system.

    Usage (from websocket_server.py):
        self._brain = BrainAdapter()
        result = self._brain.process("open chrome", source="voice")
        if result.is_valid:
            # Use brain result
        else:
            # Fall through to keyword engine
    """

    def __init__(self):
        print("[BRAIN] Initializing Brain Adapter...")
        self._lock = threading.Lock()

        # ── Lazy-load advanced modules ──
        self.input_priority = _safe_import(
            "InputPriorityManager",
            lambda: __import__("jarvis.core.input_priority", fromlist=["get_priority_manager"]).get_priority_manager()
        )
        self.intent_model = _safe_import(
            "IntentModel",
            lambda: __import__("jarvis.core.intent_model", fromlist=["get_intent_model"]).get_intent_model()
        )
        self.entity_extractor = _safe_import(
            "EntityExtractor",
            lambda: __import__("jarvis.core.entity_extractor", fromlist=["get_entity_extractor"]).get_entity_extractor()
        )
        self.decision_engine = _safe_import(
            "DecisionEngine",
            lambda: __import__("jarvis.core.decision_engine", fromlist=["get_decision_engine"]).get_decision_engine()
        )
        self.emotion_router = _safe_import(
            "EmotionRouter",
            lambda: __import__("jarvis.core.emotion_router", fromlist=["get_emotion_router"]).get_emotion_router()
        )
        self.state_manager = _safe_import(
            "StateManager",
            lambda: __import__("jarvis.core.state_manager", fromlist=["get_state_manager"]).get_state_manager()
        )

        # Stats
        self._stats = {"brain_hits": 0, "fallbacks": 0, "errors": 0}
        print("[BRAIN] Brain Adapter Ready")

    # ── Main entry point ───────────────────────────────────────
    def process(self, text: str, source: str = "voice", context: Dict[str, Any] = None) -> BrainResult:
        """
        Run text through the advanced brain pipeline.

        Args:
            text: User command text (wake word already stripped)
            source: "voice", "gesture", "ui", "scheduled"
            context: Optional context dict (active_app, last_intent, etc.)

        Returns:
            BrainResult with route="brain" if successful, "fallback" otherwise.
        """
        result = BrainResult()
        result.metadata["source"] = source
        result.metadata["input"] = text
        t0 = time.time()

        try:
            # ── Step 1: Input Priority ──
            result = self._step_priority(result, text, source)

            # ── Step 2: Intent Classification (ML) ──
            result = self._step_classify(result, text)

            # ── Step 3: Entity Extraction ──
            result = self._step_entities(result, text)

            # ── Step 4: Decision Engine ──
            result = self._step_decide(result)

            # ── Step 5: Emotion / State Update ──
            result = self._step_emotion(result, text)

            # ── Step 6: Update State Manager ──
            self._step_update_state(result, text)

            # ── Mark as brain-routed if we got a valid intent ──
            if result.action and result.confidence >= 0.50:
                result.route = "brain"
                self._stats["brain_hits"] += 1
            else:
                result.route = "fallback"
                result.pipeline_log.append("confidence too low -> fallback")
                self._stats["fallbacks"] += 1

        except Exception as e:
            result.route = "fallback"
            result.pipeline_log.append(f"pipeline error: {e}")
            self._stats["errors"] += 1

        elapsed = (time.time() - t0) * 1000
        result.metadata["elapsed_ms"] = round(elapsed, 1)

        # ── Observable log ──
        self._log_result(result)
        return result

    # ── Pipeline Steps ─────────────────────────────────────────

    def _step_priority(self, result: BrainResult, text: str, source: str) -> BrainResult:
        """Step 1: Prioritize input."""
        if not self.input_priority:
            result.pipeline_log.append("priority: skipped (unavailable)")
            return result

        try:
            from jarvis.core.input_priority import PrioritizedInput, InputSource

            source_map = {
                "voice": InputSource.VOICE,
                "gesture": InputSource.GESTURE,
                "ui": InputSource.UI_BUTTON,
                "scheduled": InputSource.SCHEDULED,
            }
            inp = PrioritizedInput(
                source=source_map.get(source, InputSource.VOICE),
                text=text
            )
            accepted = self.input_priority.add(inp)
            if not accepted:
                result.pipeline_log.append("priority: debounced (duplicate)")
                return result

            winner = self.input_priority.get_winner()
            if winner:
                result.priority = "urgent" if winner.source == InputSource.EMERGENCY else "normal"
                result.pipeline_log.append(f"priority: {winner.source.name} (accepted)")
            else:
                result.pipeline_log.append("priority: no winner")
        except Exception as e:
            result.pipeline_log.append(f"priority: error ({e})")

        return result

    def _step_classify(self, result: BrainResult, text: str) -> BrainResult:
        """Step 2: ML intent classification."""
        if not self.intent_model:
            result.pipeline_log.append("classify: skipped (unavailable)")
            return result

        try:
            intent, confidence = self.intent_model.classify(text)
            result.action = intent
            result.confidence = confidence

            if intent == "AMBIGUOUS":
                result.pipeline_log.append(f"classify: AMBIGUOUS ({confidence:.2f})")
                result.action = None  # Let fallback handle
            elif intent is None:
                result.pipeline_log.append(f"classify: below threshold ({confidence:.2f})")
            else:
                result.pipeline_log.append(f"classify: {intent} ({confidence:.2f})")
        except Exception as e:
            result.pipeline_log.append(f"classify: error ({e})")

        return result

    def _step_entities(self, result: BrainResult, text: str) -> BrainResult:
        """Step 3: Entity extraction."""
        if not self.entity_extractor or not result.action:
            result.pipeline_log.append("entities: skipped")
            return result

        try:
            entities = self.entity_extractor.extract(text, result.action)
            result.entities = entities
            result.pipeline_log.append(f"entities: {entities}" if entities else "entities: none")
        except Exception as e:
            result.pipeline_log.append(f"entities: error ({e})")

        return result

    def _step_decide(self, result: BrainResult) -> BrainResult:
        """Step 4: Decision engine."""
        if not self.decision_engine or not result.action:
            result.pipeline_log.append("decision: skipped")
            return result

        try:
            decision = self.decision_engine.decide(
                result.action, result.entities, result.confidence
            )
            result.decision_type = decision.type.value
            result.decision_message = decision.message
            result.priority = decision.priority.value
            result.pipeline_log.append(
                f"decision: {decision.type.value} / {decision.priority.value}"
                + (f" - {decision.message}" if decision.message else "")
            )
        except Exception as e:
            result.pipeline_log.append(f"decision: error ({e})")

        return result

    def _step_emotion(self, result: BrainResult, text: str) -> BrainResult:
        """Step 5: Emotion detection and state update."""
        if not self.emotion_router:
            result.pipeline_log.append("emotion: skipped (unavailable)")
            return result

        try:
            mood = self.emotion_router.update_mood(text)
            if mood:
                result.mood = mood.value
                result.pipeline_log.append(f"emotion: {mood.value}")
            else:
                result.pipeline_log.append("emotion: neutral (no cues)")
        except Exception as e:
            result.pipeline_log.append(f"emotion: error ({e})")

        return result

    def _step_update_state(self, result: BrainResult, text: str):
        """Step 6: Write results back to central StateManager."""
        if not self.state_manager:
            return

        try:
            if result.action:
                self.state_manager.update_intent(
                    result.action, result.confidence, result.entities
                )
            if result.mood:
                self.state_manager.set_mood(result.mood)
        except Exception:
            pass

    # ── Perception Bridge ──────────────────────────────────────
    def consume_perception_event(self, event):
        """
        Consume a PerceptionEvent from UnifiedPerception.
        Updates brain state based on modality.

        Args:
            event: PerceptionEvent with source, event_type, data, confidence
        """
        if not self.state_manager:
            return

        try:
            if event.event_type == "gesture" and event.data:
                gesture = event.data.get("gesture", "")
                meta = event.data.get("meta", {})
                self.state_manager.update_gesture(gesture, meta)
                print(f"[BRAIN] Perception -> gesture: {gesture}")

            elif event.event_type == "recognition" and event.data:
                user = event.data.get("user", "")
                if user:
                    self.state_manager.update_recognized_user(user)
                    print(f"[BRAIN] Perception -> user: {user}")

            elif event.event_type == "emotion" and event.data:
                emotion = event.data.get("emotion", "")
                if emotion:
                    self.state_manager.update_emotion(emotion)
                    print(f"[BRAIN] Perception -> emotion: {emotion}")

        except Exception as e:
            print(f"[BRAIN] Perception event error: {e}")

    # ── Perception Background Consumer ─────────────────────────
    def start_perception_consumer(self, perception):
        """
        Start a background thread that polls UnifiedPerception events
        and feeds them into the brain state.

        Args:
            perception: UnifiedPerception instance with get_next_event()
        """
        if not perception or not hasattr(perception, 'get_next_event'):
            print("[BRAIN] No UnifiedPerception available for background consumer")
            return

        self._perception_running = True

        def _consumer_loop():
            print("[BRAIN] Perception consumer started")
            while self._perception_running:
                try:
                    event = perception.get_next_event(timeout=0.5)
                    if event:
                        self.consume_perception_event(event)
                except Exception:
                    pass

        t = threading.Thread(target=_consumer_loop, daemon=True, name="brain-perception")
        t.start()
        return t

    def stop_perception_consumer(self):
        """Stop the perception consumer thread."""
        self._perception_running = False

    # ── Logging ────────────────────────────────────────────────
    def _log_result(self, result: BrainResult):
        """Print observable pipeline log."""
        route_tag = "BRAIN" if result.route == "brain" else "FALLBACK"
        elapsed = result.metadata.get("elapsed_ms", "?")
        lines = [f"[BRAIN] -- {route_tag} ({elapsed}ms) --"]
        lines.append(f"[BRAIN]   input: {result.metadata.get('input', '?')}")
        for step in result.pipeline_log:
            lines.append(f"[BRAIN]   {step}")
        if result.action:
            lines.append(f"[BRAIN]   -> action={result.action} conf={result.confidence:.2f}")
        print("\n".join(lines))

    # ── Stats ──────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, int]:
        """Get brain adapter statistics."""
        return dict(self._stats)


# ── Singleton ──────────────────────────────────────────────────
_brain: Optional[BrainAdapter] = None

def get_brain_adapter() -> BrainAdapter:
    global _brain
    if _brain is None:
        _brain = BrainAdapter()
    return _brain
