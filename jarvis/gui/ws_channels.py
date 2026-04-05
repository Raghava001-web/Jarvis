"""
JARVIS 4-Channel WebSocket Server
==================================
Clean architecture with separation of concerns:

    WS1 (8765) UI       - HUD display updates only
    WS2 (8766) Voice    - Speech recognition & TTS
    WS3 (8767) Vision   - Camera, gesture, face, mood
    WS4 (8768) Command  - User commands & actions

Rules:
    1. Strict message types per channel
    2. No cross-talking (each channel does ONE job)
    3. JARVIS core is the hub, channels are spokes
"""

import asyncio
import json
import logging
import time
from typing import Set, Dict, Any

try:
    import websockets
except ImportError:
    print("[CHANNELS] Installing websockets...")
    import subprocess
    subprocess.run(["pip", "install", "websockets"], check=True)
    import websockets

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
logger = logging.getLogger("WS-CHANNELS")

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT REGISTRIES (one set per channel)
# ═══════════════════════════════════════════════════════════════════════════════

UI_CLIENTS: Set = set()
VOICE_CLIENTS: Set = set()
VISION_CLIENTS: Set = set()
COMMAND_CLIENTS: Set = set()

# Reference to JARVIS core (set by start_channels())
_jarvis = None


# ═══════════════════════════════════════════════════════════════════════════════
# BACKPRESSURE CONTROL (TokenBucket Algorithm)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenBucket:
    """
    Token bucket rate limiter with burst support.
    
    - rate: tokens per second (sustained throughput)
    - burst: max tokens (allows temporary spikes)
    """
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_time = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rate limited."""
        now = time.time()
        elapsed = now - self.last_time
        self.last_time = now
        
        # Refill tokens based on elapsed time
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def available(self) -> float:
        """Return current available tokens"""
        return self.tokens


class BackpressureManager:
    """
    Manages rate limiting across different stream types.
    Each stream has its own TokenBucket with appropriate limits.
    """
    def __init__(self):
        # Vision: 10 fps sustained, burst to 15
        self.vision = TokenBucket(rate=10, burst=15)
        # Gesture: 5/sec sustained, burst to 8
        self.gesture = TokenBucket(rate=5, burst=8)
        # Emotion: 1/sec sustained, burst to 2
        self.emotion = TokenBucket(rate=1, burst=2)
        # State updates: 5/sec sustained, burst to 10
        self.state = TokenBucket(rate=5, burst=10)
        # UI updates: 10/sec sustained, burst to 20
        self.ui = TokenBucket(rate=10, burst=20)
        # Responses: 20/sec sustained, burst to 30 (chat is bursty)
        self.response = TokenBucket(rate=20, burst=30)
    
    def can_send(self, stream_type: str) -> bool:
        """Check if we can send on this stream type"""
        bucket = getattr(self, stream_type, None)
        if bucket is None:
            return True  # Unknown stream, don't rate limit
        return bucket.consume()
    
    def get_stats(self) -> Dict[str, float]:
        """Get current token levels for monitoring"""
        return {
            "vision": self.vision.available(),
            "gesture": self.gesture.available(),
            "emotion": self.emotion.available(),
            "state": self.state.available(),
            "ui": self.ui.available(),
            "response": self.response.available(),
        }


# Global backpressure manager
_backpressure = BackpressureManager()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def register(ws, client_set: Set, channel: str):
    """Register a client to a channel"""
    client_set.add(ws)
    logger.info(f"[{channel}] Connected: {ws.remote_address}")


async def unregister(ws, client_set: Set, channel: str):
    """Unregister a client from a channel"""
    client_set.discard(ws)
    logger.info(f"[{channel}] Disconnected: {ws.remote_address}")


async def broadcast(client_set: Set, message: Dict[str, Any], stream_type: str = None):
    """Send message to all clients in a set with optional backpressure"""
    if not client_set:
        return False
    
    # Apply backpressure if stream type specified
    if stream_type and not _backpressure.can_send(stream_type):
        logger.debug(f"[BACKPRESSURE] Dropping {stream_type} message (rate limited)")
        return False
    
    msg = json.dumps(message)
    await asyncio.gather(
        *[client.send(msg) for client in client_set],
        return_exceptions=True
    )
    return True


async def send_to_ui(message: Dict[str, Any], stream_type: str = "ui"):
    """Send update to all UI clients with backpressure"""
    return await broadcast(UI_CLIENTS, message, stream_type)


async def send_to_voice(message: Dict[str, Any]):
    """Send TTS or voice control to voice clients"""
    return await broadcast(VOICE_CLIENTS, message, "response")


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL 1: UI (Port 8765)
# Responsibility: Display updates ONLY (orb, chat, status, features)
# ═══════════════════════════════════════════════════════════════════════════════

async def ui_handler(websocket, path=None):
    """UI Channel - HUD display updates"""
    await register(websocket, UI_CLIENTS, "UI")
    try:
        # Send initial state
        if _jarvis:
            initial_state = _jarvis.state.get_full_state() if hasattr(_jarvis, 'state') else {}
            await websocket.send(json.dumps({
                "type": "state",
                "payload": initial_state
            }))
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # UI channel mostly RECEIVES, but can request state
            if msg_type == "get_state":
                if _jarvis and hasattr(_jarvis, 'state'):
                    state = _jarvis.state.get_full_state()
                    await websocket.send(json.dumps({
                        "type": "state",
                        "payload": state
                    }))
            
            elif msg_type == "toggle_feature":
                # Forward to command channel
                await broadcast(COMMAND_CLIENTS, data)
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket, UI_CLIENTS, "UI")


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL 2: VOICE (Port 8766)
# Responsibility: Speech recognition input & TTS output
# ═══════════════════════════════════════════════════════════════════════════════

async def voice_handler(websocket, path=None):
    """Voice Channel - Speech input/output"""
    await register(websocket, VOICE_CLIENTS, "VOICE")
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type in ("voice_input", "recognized_speech"):
                text = data.get("text", "")
                confidence = data.get("confidence", 1.0)
                
                logger.info(f"[VOICE] Input: '{text}' (conf: {confidence})")
                
                # Forward to command channel for processing
                await broadcast(COMMAND_CLIENTS, {
                    "type": "command",
                    "source": "voice",
                    "text": text,
                    "confidence": confidence
                })
            
            elif msg_type == "tts_status":
                # TTS finished speaking
                if _jarvis and hasattr(_jarvis, 'state'):
                    _jarvis.state.transition("idle")
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket, VOICE_CLIENTS, "VOICE")


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL 3: VISION (Port 8767)
# Responsibility: Camera frames, gestures, face, emotion
# Uses TokenBucket backpressure instead of manual time tracking
# ═══════════════════════════════════════════════════════════════════════════════

async def vision_handler(websocket, path=None):
    """Vision Channel - Camera/gesture/face/mood with backpressure"""
    await register(websocket, VISION_CLIENTS, "VISION")
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "gesture":
                # Use backpressure manager for rate limiting
                if not _backpressure.can_send("gesture"):
                    continue
                
                gesture = data.get("gesture")
                confidence = data.get("confidence", 0)
                meta = data.get("meta", {})
                
                if confidence > 0.6:
                    logger.info(f"[VISION] Gesture: {gesture} (conf: {confidence})")
                    
                    # Update JARVIS state (continuous - doesn't trigger pipeline)
                    if _jarvis and hasattr(_jarvis, 'state'):
                        _jarvis.state.update_gesture(gesture, meta)
                    
                    # Forward as command if actionable
                    if gesture not in ("idle", "tracking"):
                        await broadcast(COMMAND_CLIENTS, {
                            "type": "gesture_command",
                            "gesture": gesture,
                            "confidence": confidence,
                            "meta": meta
                        })
            
            elif msg_type == "emotion":
                # Emotion updates are rate limited to prevent jitter
                if not _backpressure.can_send("emotion"):
                    continue
                
                emotion = data.get("emotion")
                confidence = data.get("confidence", 0)
                
                logger.info(f"[VISION] Emotion: {emotion}")
                
                # Update state continuously (stream-based, not triggering pipeline)
                if _jarvis and hasattr(_jarvis, 'state'):
                    _jarvis.state.update_mood(emotion, confidence)
                
                # Update UI with backpressure
                await send_to_ui({
                    "type": "emotion_update",
                    "emotion": emotion,
                    "confidence": confidence
                }, stream_type="emotion")
            
            elif msg_type == "face":
                # Vision frames for face detection
                if not _backpressure.can_send("vision"):
                    continue
                
                user = data.get("user")
                confidence = data.get("confidence", 0)
                
                if _jarvis and hasattr(_jarvis, 'state'):
                    _jarvis.state.update_user(user, confidence)
                
                await send_to_ui({
                    "type": "face_update",
                    "user": user,
                    "confidence": confidence
                }, stream_type="vision")
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket, VISION_CLIENTS, "VISION")


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL 4: COMMAND (Port 8768)
# Responsibility: Process all commands & coordinate responses
# ═══════════════════════════════════════════════════════════════════════════════

async def command_handler(websocket, path=None):
    """Command Channel - All user commands & actions"""
    await register(websocket, COMMAND_CLIENTS, "COMMAND")
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type in ("command", "text_input", "voice_command"):
                text = data.get("text", "")
                source = data.get("source", "text")
                
                logger.info(f"[COMMAND] {source}: '{text}'")
                
                # Process through JARVIS
                if _jarvis:
                    result = _jarvis.handle_input(text=text)
                    
                    # Send response to UI
                    await send_to_ui({
                        "type": "response",
                        "text": result.get("response", ""),
                        "speak": result.get("should_speak", True),
                        "confidence": result.get("confidence", 0)
                    })
                    
                    # Send TTS command to voice channel
                    if result.get("should_speak", True):
                        await send_to_voice({
                            "type": "speak",
                            "text": result.get("response", "")
                        })
                    
                    # Send state update to UI
                    await send_to_ui({
                        "type": "state",
                        "payload": result.get("state", {})
                    })
            
            elif msg_type == "gesture_command":
                gesture = data.get("gesture")
                
                logger.info(f"[COMMAND] Gesture action: {gesture}")
                
                if _jarvis:
                    # Map gesture to action
                    from core.gesture_controller import get_gesture_action
                    active_app = "default"
                    if hasattr(_jarvis, 'state'):
                        active_app = getattr(_jarvis.state, 'active_app', 'default')
                    
                    action = get_gesture_action(gesture, active_app)
                    
                    # Execute action
                    result = _jarvis.handle_input(text=f"gesture:{action}")
                    
                    await send_to_ui({
                        "type": "gesture_feedback",
                        "gesture": gesture,
                        "action": action
                    })
            
            elif msg_type == "toggle_feature":
                feature = data.get("feature")
                enabled = data.get("enabled", True)
                
                logger.info(f"[COMMAND] Toggle: {feature} = {enabled}")
                
                if _jarvis:
                    # Handle feature toggle
                    pass
                
                await send_to_ui({
                    "type": "feature_status",
                    "feature": feature,
                    "enabled": enabled
                })
            
            elif msg_type == "music_control":
                action = data.get("action")
                
                logger.info(f"[COMMAND] Music: {action}")
                
                if _jarvis and hasattr(_jarvis, 'handlers'):
                    music = _jarvis.handlers.get("music")
                    if music:
                        if action == "play": music.play()
                        elif action == "pause": music.pause()
                        elif action == "next": music.next_track()
                        elif action == "previous": music.previous_track()
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket, COMMAND_CLIENTS, "COMMAND")


# ═══════════════════════════════════════════════════════════════════════════════
# SERVER STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

async def start_channels(jarvis_instance=None):
    """Start all 4 WebSocket channels"""
    global _jarvis
    _jarvis = jarvis_instance
    
    server_ui = await websockets.serve(ui_handler, "localhost", 8765)
    server_voice = await websockets.serve(voice_handler, "localhost", 8766)
    server_vision = await websockets.serve(vision_handler, "localhost", 8767)
    server_command = await websockets.serve(command_handler, "localhost", 8768)
    
    logger.info("=" * 60)
    logger.info("JARVIS 4-Channel WebSocket Server")
    logger.info("=" * 60)
    logger.info("UI      -> ws://localhost:8765  (HUD display)")
    logger.info("VOICE   -> ws://localhost:8766  (Speech I/O)")
    logger.info("VISION  -> ws://localhost:8767  (Camera/gesture)")
    logger.info("COMMAND -> ws://localhost:8768  (User commands)")
    logger.info("=" * 60)
    
    await asyncio.Future()  # Run forever


async def main():
    """Standalone mode (for testing)"""
    await start_channels()


if __name__ == "__main__":
    asyncio.run(main())
