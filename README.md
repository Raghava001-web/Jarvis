# 🤖 J.A.R.V.I.S. — AI Desktop Assistant

> **Just A Rather Very Intelligent System**
> A fully autonomous, real-time AI desktop assistant with voice control, gesture recognition, emotion detection, and a stunning Iron Man-inspired Web HUD.

<p align="center">
  <img src="docs/jarvis_banner.png" alt="JARVIS Banner" width="800">
</p>

---

## ⚡ Features

### 🎙️ Voice-First Interaction
- **Gemini Live Engine** — Real-time bi-directional voice conversation powered by Google's Gemini 2.0 Flash
- **Natural Language Understanding** — Intent classification with 30+ command categories
- **Wake Word Free** — Always listening, always ready
- **Edge TTS** — High-quality text-to-speech with multiple voice options

### 🖥️ Web HUD (Iron Man Style)
The crown jewel — a **real-time web dashboard** inspired by Tony Stark's holographic interface:
- 🌍 **Interactive 3D Globe** — Live rotating Earth visualization
- 📊 **System Vitals** — CPU, RAM, battery, network stats in real-time
- 🎯 **Intent Visualization** — See JARVIS thinking in real-time
- 💬 **Chat Panel** — Full conversation history with markdown support
- 🌤️ **Weather Widget** — Live weather data with animations
- 📰 **News Feed** — Real-time news ticker
- 🎨 **Mood Ring** — Visual emotion detection feedback
- 🔊 **Waveform Visualizer** — Audio visualization during speech
- ⚙️ **Settings Panel** — Configure everything from the HUD

### 🖐️ Gesture Control
- **MediaPipe-powered** hand gesture recognition
- Thumbs up/down, wave, swipe, and custom gestures
- Control JARVIS hands-free from across the room

### 😊 Emotion Detection
- Real-time facial emotion analysis
- JARVIS adapts tone and responses based on your mood
- Multimodal emotion detection (voice + face + text)

### 🧠 Intelligence Layer
- **40+ Tool Functions** — Open apps, send messages, control system, search web, manage files
- **Context Memory** — Remembers conversations and user preferences
- **Proactive Assistant** — Learns your patterns and suggests actions
- **Multi-step Workflows** — Chain commands: "open Chrome and search for AI news"

### 🔧 System Control
| Category | Commands |
|----------|----------|
| **Apps** | Open, close, switch between any application |
| **Volume** | Up, down, mute, set to specific level |
| **Brightness** | Up, down, set to specific level |
| **Screen** | Screenshot, screen capture, read screen (OCR) |
| **System** | Lock, restart, shutdown, bluetooth toggle |
| **Media** | Play/pause video, next/previous track |

### 📱 Communication
- **WhatsApp** — Send messages to contacts
- **Email** — Send, read, summarize emails via Gmail
- **Clipboard Intelligence** — Smart clipboard monitoring

### 📝 Productivity
- **Smart Notes** — Create, list, search notes
- **Alarms & Reminders** — Natural language time parsing
- **Habit Tracker** — Track daily habits with reminders
- **Task Manager** — Todo list management
- **Wellness Monitor** — Break reminders, screen time tracking

### 🎵 Entertainment
- **YouTube** — Search and play videos directly
- **Spotify** — Play music by song/artist name
- **Jokes, Stories, Poems** — Entertainment on demand
- **News** — Category-specific news headlines

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Windows 10/11** (system control features are Windows-native)
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/apikey)
- **Microphone + Speakers** (for voice interaction)
- **Webcam** (optional, for gesture/face/emotion detection)

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

Create a `.env` file in the project root:

```env
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
# Option 1: Double-click the batch file
START_JARVIS.bat

# Option 2: Run directly
python -m jarvis.gui.desktop_gui
```

JARVIS will:
1. 🖥️ Open the desktop GUI window
2. 🌐 Start the WebSocket server on `ws://localhost:8765`
3. 🎙️ Connect to Gemini Live for voice interaction
4. 🖐️ Initialize gesture recognition (if webcam available)

### Access the Web HUD

Once JARVIS is running, open the Web HUD:
1. Click the **"Web HUD"** button in the desktop GUI, or
2. Navigate to `http://localhost:8080` in your browser

---

## 🏗️ Architecture

```
JARVIS-AI-Assistant/
├── jarvis/
│   ├── core/                    # Brain — 65+ modules
│   │   ├── gemini_live_engine.py   # Real-time voice (Gemini 2.0)
│   │   ├── intent_classifier.py    # NLP intent classification
│   │   ├── intent_handlers.py      # 30+ command handlers
│   │   ├── perception.py           # Voice + vision layer
│   │   ├── gesture_controller.py   # Hand gesture recognition
│   │   ├── emotion_detector.py     # Facial emotion analysis
│   │   ├── context_memory.py       # Conversation memory
│   │   ├── system_control.py       # OS-level control
│   │   ├── workflow_manager.py     # Multi-step automation
│   │   └── ...                     # 55+ more modules
│   │
│   ├── gui/                     # Interface layer
│   │   ├── desktop_gui.py          # Pygame desktop window
│   │   ├── websocket_server.py     # WebSocket + command router
│   │   └── web_hud/                # Iron Man Web HUD
│   │       ├── index.html          # Main HUD interface
│   │       ├── styles.css          # HUD styling
│   │       └── app.js              # Real-time WebSocket client
│   │
│   ├── data/                    # Static data files
│   ├── models/                  # ML model weights
│   └── utils/                   # Utility functions
│
├── jarvis_data/                 # Runtime data (not in repo)
├── requirements.txt             # Python dependencies
├── START_JARVIS.bat            # One-click launcher
└── .env                        # API keys (not in repo)
```

### Data Flow

```
Voice Input ──► Gemini Live Engine ──► Tool Execution ──► Audio Response
                     │                       │
Text Input ──► WebSocket Server ──► Fast Path ──► Instant Response
                     │                  │
                     │              Intent Router ──► Handler ──► Response
                     │                  │
                     │              Gemini Flash API ──► AI Response
                     │
                     ▼
              Web HUD (Real-time state sync via WebSocket)
```

---

## 🎨 Web HUD Preview

The Web HUD provides a real-time, immersive interface:

- **Dark theme** with glowing accents (Iron Man aesthetic)
- **Real-time data** — all widgets update via WebSocket
- **Responsive** — works on desktop and tablet
- **State visualization** — see JARVIS transition between idle → listening → processing → speaking

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | Google Gemini 2.0 Flash (Live + Text) |
| **Voice** | Gemini Live (bidirectional), Edge TTS, Whisper STT |
| **Vision** | MediaPipe, OpenCV, TensorFlow |
| **Desktop GUI** | Pygame |
| **Web HUD** | Vanilla HTML/CSS/JS + WebSocket |
| **Communication** | WebSocket (ws://), HTTP |
| **System Control** | pyautogui, pycaw, subprocess |
| **NLP** | Custom intent classifier + sentence-transformers |

---

## 🔑 API Keys Required

| Service | Required | Get Key |
|---------|----------|---------|
| **Gemini API** | ✅ Yes | [Google AI Studio](https://aistudio.google.com/apikey) |
| **OpenWeather** | ⬜ Optional | [openweathermap.org](https://openweathermap.org/api) |
| **News API** | ⬜ Optional | [newsapi.org](https://newsapi.org) |
| **Gmail SMTP** | ⬜ Optional | [Google App Passwords](https://myaccount.google.com/apppasswords) |

---

## 📝 Voice Commands Examples

```
"Open YouTube"
"Play Despacito in YouTube"
"Close WhatsApp"
"Set volume to 50"
"Take a screenshot"
"What's the weather like?"
"Set alarm for 7 AM"
"Remind me to drink water in 30 minutes"
"Send a WhatsApp message to Mom saying I'll be late"
"Tell me a joke"
"What time is it?"
"Search for latest AI news"
"Read my screen"
"Switch to Chrome"
"Shutdown laptop"
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** — For the incredible Live API and Flash model
- **MediaPipe** — For real-time hand and face tracking
- **The Iron Man franchise** — For the JARVIS inspiration

---

<p align="center">
  <i>"Good evening, sir. All systems are online and ready."</i>
  <br>
  <b>— J.A.R.V.I.S.</b>
</p>
