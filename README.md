# 🤖 J.A.R.V.I.S. — AI Desktop Assistant

> **Just A Rather Very Intelligent System**
> A real-time, voice-first AI desktop assistant with full-duplex Gemini Live conversation, an Iron Man–inspired Web HUD, gesture control, emotion detection, and 30+ integrated system tools — all running locally on Windows.
>
> 🚀 **Active Ongoing Project & Massive Future Potential:** JARVIS is continuously evolved with new capabilities, holding immense potential for advanced desktop automation, custom agent workflows, and deeper spatial-visual perception.

<p align="center">
  <img src="docs/jarvis_banner.png" alt="JARVIS Banner" width="800">
</p>

---

## Overview

JARVIS is a modular AI assistant that goes beyond chat. It combines **real-time bidirectional voice** (via Google Gemini Live), a **multi-layer intelligence pipeline** (intent classification → entity extraction → decision engine → emotion routing), and **direct system control** (apps, volume, brightness, screenshots) into a single cohesive runtime.

The interface is a full **Iron Man–style Web HUD** served over WebSocket, with live system vitals, a 3D globe, waveform visualization, and a tabbed Feature Hub for face recognition, gestures, WhatsApp, and news.

### What makes this different

- **Voice-first, not text-first** — Gemini Live provides full-duplex audio streaming. You talk, JARVIS talks back — simultaneously, with echo suppression and interrupt handling.
- **Tool execution, not just conversation** — When you say "open Chrome," JARVIS doesn't just say "I opened Chrome." It calls `open_app("Chrome")` through a registered tool dispatcher and actually opens it.
- **Layered intelligence** — A fast keyword classifier handles 90% of commands instantly. Ambiguous inputs route through BrainAdapter's ML pipeline. Only truly open-ended queries go to the LLM.
- **Tactical personality** — JARVIS warns you before destructive actions (shutdown, max volume), detects repeated failures, and adapts responses to your emotional state.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        TRANSPORT LAYER                           │
│              websocket_server.py (WebSocket gateway)             │
│         Serves Web HUD · Routes all commands · Manages state     │
└───────────┬──────────────┬──────────────────┬────────────────────┘
            │              │                  │
   ┌────────▼────────┐ ┌──▼───────────┐ ┌───▼──────────────┐
   │  GEMINI LIVE    │ │  BRAIN       │ │  KEYWORD ENGINE  │
   │  ENGINE         │ │  ADAPTER     │ │  (dispatcher.py) │
   │                 │ │              │ │                  │
   │ Full-duplex     │ │ IntentModel  │ │ Pattern-match    │
   │ audio streaming │ │ EntityExtr.  │ │ 30+ intents      │
   │ 14 native tools │ │ DecisionEng. │ │ Cache + memory   │
   │ Echo gate       │ │ EmotionRoute │ │                  │
   └────────┬────────┘ └──┬───────────┘ └───┬──────────────┘
            │              │                  │
            └──────────────┴──────────────────┘
                           │
            ┌──────────────▼──────────────────┐
            │         EXECUTION LAYER          │
            │                                  │
            │  system_control.py   apps        │
            │  voice_engine.py     TTS         │
            │  workflow_manager.py automation   │
            │  news / weather / email / notes  │
            │  WhatsApp / YouTube / calendar    │
            └──────────────────────────────────┘
```

### Key Modules

| Module | Role |
|--------|------|
| **`websocket_server.py`** | Central gateway. Serves the Web HUD, manages WebSocket connections, routes all commands through keyword engine or BrainAdapter, manages Gemini Live lifecycle. |
| **`gemini_live_engine.py`** | Full-duplex audio via Gemini 2.0 Flash. Handles mic capture, speaker playback, echo suppression, tool calls, and turn management — all async. |
| **`brain_adapter.py`** | ML pipeline bridge. Routes text through IntentModel → EntityExtractor → DecisionEngine → EmotionRouter for nuanced understanding. Falls back gracefully if any module is unavailable. |
| **`state_controller.py`** | UI state machine (`UIStateController`). Tracks state transitions (idle → listening → processing → speaking), trust scoring, emotion vectors, and deduplication. |
| **`startup_orchestrator.py`** | Boot sequence. Generates time-aware greetings, loads session history, reports system status, and builds context for the first Gemini Live turn. |
| **`intent_classifier.py`** | 30+ intent classifier with confidence scoring. Maps natural language to structured actions. |
| **`decision_engine.py`** | Safety layer. Evaluates commands before execution — warns on destructive actions, blocks dangerous operations, enforces tactical personality. |
| **`voice_engine.py`** | Edge TTS backend with automatic cache cleanup. Provides `speak()` for non-live-mode responses. |
| **`perception.py`** | HUDPerception layer. Manages assistant identity (JARVIS/FRIDAY), speech deduplication, live-mode gating, and persona switching. |

---

## What Works Now

### ✅ Core — Fully Functional

| Feature | Status | Details |
|---------|--------|---------|
| **Gemini Live Voice** | ✅ Working | Full-duplex audio, echo gate, interrupt handling, tool dispatch |
| **BrainAdapter Text Routing** | ✅ Working | ML pipeline with intent → entity → decision → emotion |
| **Keyword Engine** | ✅ Working | 30+ intents, cache, memory, pattern matching |
| **System Control** | ✅ Working | Open/close apps, volume, brightness, screenshots, lock/shutdown |
| **Web HUD** | ✅ Working | Real-time dashboard with globe, vitals, chat, waveform |
| **Feature Hub Tabs** | ✅ Working | Face Recognition, WhatsApp, Hand Gestures, News — tabbed UI |
| **Tactical Personality** | ✅ Working | Safety warnings, failure detection, emotional adaptation |
| **Switch to FRIDAY** | ✅ Working | Voice command to swap persona (JARVIS ↔ FRIDAY) |
| **News** | ✅ Working | Category-filtered headlines via News API |
| **Weather** | ✅ Working | Live weather via OpenWeatherMap (requires API key) |
| **Reminders & Alarms** | ✅ Working | Natural language time parsing, background checker |
| **Chat History** | ✅ Working | SQLite-backed with FTS5 search, thread-safe |
| **Smart Notes** | ✅ Working | Create, search, list notes |
| **Hotkeys** | ✅ Working | Ctrl+Alt+J (wake), Ctrl+Alt+S (shutdown) |

### ⚙️ Optional — Dependency-Based

| Feature | Requires | Details |
|---------|----------|---------|
| **Face Recognition** | Webcam + OpenCV | Enrolls and recognizes users |
| **Hand Gestures** | Webcam + MediaPipe | Thumbs up/down, wave, swipe |
| **Emotion Detection** | Webcam + TensorFlow | Facial emotion → response adaptation |
| **WhatsApp** | `pywhatkit` | Send messages to contacts |
| **Email** | Gmail SMTP credentials | Send/read emails |
| **YouTube** | `yt-dlp` | Search and play videos |
| **Calendar** | Google Calendar API | Event listing and reminders |
| **Spotify** | `spotipy` + Spotify API | Music playback |

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Windows 10/11** (system control features are Windows-native)
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/apikey)
- **Microphone + Speakers** (for Gemini Live voice)
- **Webcam** (optional — for gesture, face recognition, emotion)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/JARVIS-AI-Assistant.git
cd JARVIS-AI-Assistant

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Configuration

Create a `.env` file in the project root (or edit the copied `.env.example`):

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_LIVE_ENABLED=true

# Optional
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
OPENWEATHER_API_KEY=your_weather_key
NEWS_API_KEY=your_news_key
```

### Run JARVIS

```bash
# Option 1: Batch launcher
start_jarvis.bat

# Option 2: Direct
python jarvis/gui/websocket_server.py
```

JARVIS will:
1. Start the WebSocket server on `ws://localhost:8765`
2. Serve the Web HUD on `http://localhost:8080`
3. Connect to Gemini Live for voice interaction
4. Initialize gesture/face/emotion (if webcam available)

### Access the Web HUD

Open your browser to **`http://localhost:8080`** to see the Iron Man–style dashboard.

---

## Testing

### Smoke Test Suite

A 53-test smoke suite validates all critical paths without requiring hardware or API keys:

```bash
python -m pytest tests/test_smoke.py -v
```

**Current status: 53/53 passing**

The suite covers:
- Application boot and startup orchestrator
- Gemini Live deduplication and echo gating
- BrainAdapter pipeline routing
- Intent classification (30+ intents)
- News command end-to-end flow
- JARVIS ↔ FRIDAY persona switching
- Tactical personality (safety warnings, failure detection)
- Handler map completeness

### Additional Test Suites

```bash
# Intent model unit tests
python -m pytest tests/test_intent_model.py -v

# Entity extractor tests
python -m pytest tests/test_entity_extractor.py -v

# Intent router tests
python -m pytest tests/test_intent_router.py -v

# Run everything
python -m pytest tests/ -v
```

---

## Voice Commands

```
"Open YouTube"                              → launches YouTube
"Close Chrome"                              → closes Chrome
"Set volume to 50"                          → adjusts system volume
"Take a screenshot"                         → captures screen
"What's the weather like?"                  → weather report
"Tell me the news"                          → headlines summary
"Set alarm for 7 AM"                        → alarm
"Remind me to call Mom in 30 minutes"       → reminder
"Send WhatsApp to Dad saying I'll be late"  → WhatsApp message
"Switch to Friday"                          → persona swap
"What time is it?"                          → time
"Search for latest AI research"             → web search
"Tell me a joke"                            → entertainment
"Shutdown JARVIS"                           → graceful shutdown
```

---

## Project Structure

```
JARVIS-AI-Assistant/
├── jarvis/
│   ├── core/                        # 68 modules — brain, voice, tools, handlers
│   │   ├── gemini_live_engine.py       # Gemini Live full-duplex audio (1500+ lines)
│   │   ├── brain_adapter.py            # ML pipeline bridge
│   │   ├── intent_classifier.py        # 30+ intent classifier
│   │   ├── intent_handlers.py          # Handler implementations
│   │   ├── decision_engine.py          # Safety/tactical layer
│   │   ├── voice_engine.py             # Edge TTS backend
│   │   ├── perception.py               # HUDPerception + persona management
│   │   ├── startup_orchestrator.py     # Boot sequence
│   │   ├── system_control.py           # OS-level commands
│   │   ├── reminder_manager.py         # Thread-safe SQLite reminders
│   │   ├── chat_history.py             # Thread-safe chat storage
│   │   ├── context_memory.py           # Conversation memory
│   │   ├── emotion_router.py           # Text → mood detection
│   │   ├── state_manager.py            # Core state machine
│   │   └── ...                         # weather, news, email, WhatsApp, etc.
│   │
│   ├── gui/                         # Interface layer
│   │   ├── websocket_server.py         # Central gateway (WebSocket + HTTP)
│   │   ├── state_controller.py         # UI state controller
│   │   ├── mood_engine.py              # Emotion state machine
│   │   ├── command_processor.py        # Command routing
│   │   ├── desktop_gui.py              # Pygame desktop window
│   │   ├── advanced_hud.py             # Pygame HUD renderer
│   │   └── web_hud/
│   │       └── index.html              # Iron Man Web HUD (single-file app)
│   │
│   ├── tools/                       # Tool architecture
│   │   ├── dispatcher.py               # Intent → tool routing + caching
│   │   ├── tool_registry.py            # Async tool execution
│   │   └── web_tools.py                # Web search, news, URL fetch
│   │
│   └── data/                        # Runtime databases (SQLite)
│
├── tests/                           # Test suites
│   ├── test_smoke.py                   # 53 smoke tests
│   ├── test_intent_model.py            # Intent model tests
│   ├── test_entity_extractor.py        # Entity extraction tests
│   └── test_intent_router.py           # Router tests
│
├── jarvis_data/                     # Session data (gitignored)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── start_jarvis.bat                 # One-click launcher
└── README.md                        # This file
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | Google Gemini 2.0 Flash (Live + Text) |
| **Voice** | Gemini Live (full-duplex), Edge TTS |
| **Vision** | MediaPipe, OpenCV, TensorFlow |
| **Desktop GUI** | Pygame |
| **Web HUD** | Vanilla HTML/CSS/JS + WebSocket |
| **Transport** | WebSocket (real-time), HTTP (HUD serving) |
| **System Control** | pyautogui, pycaw, psutil |
| **NLP** | Custom intent classifier + sentence-transformers |
| **Storage** | SQLite (thread-safe, persistent) |

---

## API Keys

| Service | Required | Get Key |
|---------|----------|---------|
| **Gemini API** | ✅ Required | [Google AI Studio](https://aistudio.google.com/apikey) |
| **OpenWeather** | Optional | [openweathermap.org](https://openweathermap.org/api) |
| **News API** | Optional | [newsapi.org](https://newsapi.org) |
| **Gmail SMTP** | Optional | [Google App Passwords](https://myaccount.google.com/apppasswords) |

---

## Project Status & Ongoing Potential

🚀 **Active & Ongoing Development — Massive Potential**

JARVIS is an **ongoing project with immense potential for expansion**. While it is currently highly stable and fully prepared for demos, publishing, and daily use, we are continuously pushing updates to expand its capabilities. 

Our current focus:
- **Core Stability**: The runtime is stabilized with thread-safe database operations, audio clash prevention, and resource leak patches.
- **Robust Verification**: 53/53 smoke tests pass consistently to prevent regressions.
- **Multimodal Focus**: Gemini Live voice is the primary, full-duplex interaction mode.
- **Modular & Extensible**: All core features are functional out of the box. Optional features (webcam, email, calendar) degrade gracefully when dependencies are missing.
- **Active Roadmap**: Future releases aim to add offline-first intent routing, tighter OS-level automation loops, and multi-modal vision perception enhancements.

### Known Limitations

- **Windows only** — System control (volume, brightness, app management) uses Windows-native APIs
- **Gemini API key required** — No offline fallback for AI features
- **Single user** — Designed as a personal desktop assistant, not multi-tenant
- **Webcam features are optional** — Face recognition, gestures, and emotion detection require a webcam and their respective ML dependencies
- **WebSocket server is monolithic** — `websocket_server.py` is large (~4100 lines); partial extraction into `command_processor.py`, `state_controller.py`, and `ws_channels.py` has begun

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Google Gemini** — For the Gemini Live API and Flash model
- **MediaPipe** — For real-time hand and face tracking
- **The Iron Man franchise** — For the JARVIS inspiration

---

<p align="center">
  <i>"Good evening, sir. All systems are online and ready."</i>
  <br>
  <b>— J.A.R.V.I.S.</b>
</p>
