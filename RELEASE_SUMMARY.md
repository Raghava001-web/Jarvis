# JARVIS — Release Summary

> Stable release snapshot as of May 2026.

---

## System Overview

JARVIS is a voice-first AI desktop assistant for Windows. It combines Google Gemini Live (full-duplex audio), a multi-layer NLP pipeline, direct system control, and an Iron Man–inspired Web HUD into a single runtime.

---

## Major Modules (68 core + 18 GUI)

### Core Engine
| Module | Lines | Purpose |
|--------|-------|---------|
| `gemini_live_engine.py` | ~1550 | Full-duplex Gemini Live audio, echo gate, 14 native tools |
| `websocket_server.py` | ~4100 | Central WebSocket gateway, command routing, HUD serving |
| `intent_classifier.py` | ~900 | 30+ intent classification with confidence scoring |
| `intent_handlers.py` | ~1400 | Handler implementations for all intents |
| `brain_adapter.py` | ~380 | ML pipeline bridge (intent → entity → decision → emotion) |
| `jarvis_ultimate.py` | ~1200 | Legacy monolith adapter for backward compatibility |

### Intelligence Layer
| Module | Purpose |
|--------|---------|
| `decision_engine.py` | Safety evaluation, tactical warnings, action gating |
| `entity_extractor.py` | Named entity recognition from natural language |
| `emotion_router.py` | Text-based mood detection → state updates |
| `context_memory.py` | Conversation memory with SQLite + compression |
| `intent_model.py` | Sentence-transformer intent embeddings |

### Voice & Audio
| Module | Purpose |
|--------|---------|
| `voice_engine.py` | Edge TTS with automatic cache cleanup |
| `perception.py` | HUDPerception — identity, dedup, live-mode gating |
| `sound_effects.py` | Pygame audio backend with mixer safety |

### System Control
| Module | Purpose |
|--------|---------|
| `system_control.py` | Volume, brightness, lock, shutdown, Bluetooth |
| `app_finder.py` | Application discovery and launch |
| `workflow_manager.py` | Multi-step automation with Unicode support |
| `screen_control.py` | Display and window management |

### Communication & Productivity
| Module | Purpose |
|--------|---------|
| `whatsapp_handler.py` | WhatsApp message sending |
| `email_handler.py` | Gmail SMTP send/read |
| `reminder_manager.py` | Thread-safe SQLite reminders with background checker |
| `chat_history.py` | Thread-safe conversation storage with FTS5 |
| `smart_notes.py` | Note creation and search |
| `task_manager.py` | Todo list management |

### GUI & HUD
| Module | Purpose |
|--------|---------|
| `state_controller.py` | UIStateController — state machine, trust scoring |
| `mood_engine.py` | Emotion state machine for UI |
| `web_hud/index.html` | Single-file Iron Man HUD (111KB) |
| `desktop_gui.py` | Pygame desktop window |
| `advanced_hud.py` | Pygame HUD renderer |

---

## Stabilization Work Completed

### Thread Safety (Critical)
- **Reminder DB**: Replaced per-operation SQLite connections with a single persistent connection + `threading.Lock`
- **Chat History DB**: Added `_db_lock` on all write operations and VACUUM
- **Context Memory**: Thread-safe compression and retrieval

### Audio Integrity
- **Gemini Live echo gate**: Mic is suppressed while JARVIS is speaking (0.8s window)
- **TTS cache cleanup**: Background thread purges temp MP3 files older than 5 minutes
- **Pygame mixer guard**: Checks `get_init()` before calling `mixer.init()` to prevent killing active audio
- **Lazy PyAudio**: `_get_pya()` defers hardware reservation until first use
- **Live-mode gating**: All `speak()` calls check `_gemini_live_active` before using legacy TTS

### Correctness Fixes
- **StateManager rename**: `UIStateController` in GUI to avoid collision with `core.state_manager.StateManager`
- **Trust score formula**: Fixed inverted emotion stability calculation
- **Unicode typewrite**: Clipboard paste fallback for non-ASCII input
- **Battery display**: Handles `None` battery gracefully on desktops
- **Emotion cue dedup**: Removed duplicate keywords across emotion categories
- **Multi-tool execution**: Gemini Live now processes all tool calls per turn (not just first)
- **Send error handling**: Network drops in Gemini Live are caught and logged

### Performance
- **Non-blocking CPU check**: `psutil.cpu_percent(interval=None)` saves 500ms at boot
- **Loop import cleanup**: Moved `import time` outside hot audio loops in Gemini Live
- **Conditional cv2**: OpenCV import failure doesn't crash the entire core

---

## Test Coverage

| Suite | Tests | Status |
|-------|-------|--------|
| `test_smoke.py` | 53 | ✅ All passing |
| `test_intent_model.py` | ML intent tests | ✅ |
| `test_entity_extractor.py` | Entity extraction | ✅ |
| `test_intent_router.py` | Router integration | ✅ |

---

## Before Use — Review Checklist

- [ ] Add your `GEMINI_API_KEY` to `.env`
- [ ] Verify Python 3.10+ and Windows 10/11
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `python -m pytest tests/test_smoke.py -v` to confirm baseline
- [ ] Optional: Add `NEWS_API_KEY`, `OPENWEATHER_API_KEY`, `SMTP_*` for full features
- [ ] Optional: Connect webcam for face recognition, gestures, emotion detection
