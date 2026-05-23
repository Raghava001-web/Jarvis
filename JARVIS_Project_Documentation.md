# JARVIS — Just A Rather Very Intelligent System
## AI Voice Assistant Project Documentation

**Creator:** Chevula Aditya Syamala Viswanatha Raghavendra Rao (Raghava)  
**Date:** January 2026 – May 2026  
**Platform:** Windows 10/11 (Python 3.12)

---

## 1. Problem Statement

Current personal computing requires constant manual interaction — typing, clicking, and navigating between applications. Users must repeatedly switch contexts, breaking concentration and productivity. Existing voice assistants (Siri, Cortana, Google Assistant) are cloud-dependent, lack deep system-level control, and provide generic, personality-less responses.

**JARVIS solves this** by providing a unified, intelligent interface that allows a user to control their entire computer through **natural voice commands, hand gestures, and facial recognition**, while maintaining personalized, context-aware conversation with an Iron Man JARVIS-inspired personality — all running **locally** on the user's machine.

---

## 2. Justification

| Need | How JARVIS Addresses It |
|------|------------------------|
| **Hands-free Computing** | Voice and gesture control for users who are multitasking, cooking, exercising, or working away from keyboard |
| **Accessibility** | People with motor impairments can control their computer entirely through voice and hand gestures |
| **Efficiency** | Compound commands like *"set alarm in 5 minutes and open YouTube"* eliminate repetitive manual steps |
| **Personalization** | Face-authenticated, mood-aware AI that remembers past interactions and adapts behavior |
| **Privacy** | Runs locally on the user's machine — unlike cloud-only assistants, no data leaves the device |
| **System Integration** | Deep Windows integration — volume, brightness, Bluetooth, app launching, screenshot, shutdown — all via voice |
| **Entertainment** | Jokes, stories, news with AI-generated opinions, music control via gestures |

---

## 3. Tools & Technologies

### 3.1 Programming Language
- **Python 3.12** — Core backend, AI logic, system control
- **HTML5/CSS3/JavaScript** — Browser-based HUD (Heads-Up Display)

### 3.2 AI & Machine Learning

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM (Primary) | Google Gemini 2.0 Flash (Live + Text) | Real-time voice conversation and intelligent responses |
| LLM (Voice) | Gemini Live API | Full-duplex bidirectional audio streaming |
| Intent Classification | SentenceTransformer (MiniLM) | Classify user commands into intents (open app, set alarm, etc.) |
| Emotion Detection | TensorFlow/Keras CNN | Detect user mood via facial expressions |
| Face Recognition | FaceNet-PyTorch, DeepFace | Owner authentication and access control |
| Hand Gesture Detection | MediaPipe HandLandmarker | Touchless control via 21-point hand tracking |

### 3.3 Voice & Audio

| Component | Technology |
|-----------|-----------|
| Speech Recognition | Gemini Live (primary), Google Speech API (fallback) |
| Text-to-Speech | Edge TTS (primary), Browser Web Speech API (HUD fallback) |
| Audio Control | `pycaw` (Windows Core Audio API) |

### 3.4 System Integration

| Component | Technology |
|-----------|-----------|
| App Launching | `subprocess`, `os.startfile()` |
| Brightness Control | `screen_brightness_control` |
| Keyboard/Mouse Simulation | `pyautogui` |
| Bluetooth Toggle | PowerShell `Windows.Devices.Radios` API |
| Screenshot | `pyautogui.screenshot()` |
| System Shutdown | `shutdown /s /t 5` via subprocess |

### 3.5 Communication & GUI

| Component | Technology |
|-----------|-----------|
| Real-time Server↔HUD | WebSocket (`websockets` library) |
| HUD Rendering | HTML5 Canvas, CSS3 animations, JavaScript |
| News/Weather Data | `requests`, `BeautifulSoup`, OpenWeatherMap API |

---

## 4. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    JARVIS SYSTEM                         │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Voice    │  │  Camera      │  │  Text Input       │  │
│  │  (Mic)    │  │  (Webcam)    │  │  (HUD Chat Box)   │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       │               │                   │              │
│       ▼               ▼                   │              │
│  ┌─────────┐  ┌──────────────┐            │              │
│  │ Speech   │  │ Gesture +    │            │              │
│  │ Recog.   │  │ Face + Mood  │            │              │
│  └────┬─────┘  └──────┬───────┘            │              │
│       │               │                   │              │
│       └───────┬───────┴───────────────────┘              │
│               ▼                                          │
│  ┌─────────────────────────────────────┐                 │
│  │    WebSocket Server (Port 8765)     │                 │
│  │    ┌───────────────────────┐        │                 │
│  │    │  Command Pipeline     │        │                 │
│  │    │  1. Wake Word Strip   │        │                 │
│  │    │  2. Spell Correction  │        │                 │
│  │    │  3. Stop/Quiet Check  │        │                 │
│  │    │  4. Pre-Router Match  │        │                 │
│  │    │  5. ML Intent Router  │        │                 │
│  │    │  6. Legacy Handler    │        │                 │
│  │    │  7. AI Knowledge      │        │                 │
│  │    └───────────────────────┘        │                 │
│  └───────────────┬─────────────────────┘                 │
│                  │                                       │
│    ┌─────────────┼─────────────────┐                     │
│    ▼             ▼                 ▼                     │
│  ┌─────┐  ┌──────────┐  ┌──────────────┐                │
│  │ TTS │  │ System   │  │ AI Response  │                │
│  │ Out │  │ Actions  │  │ (Groq/Gemini)│                │
│  └─────┘  └──────────┘  └──────────────┘                │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │    Browser HUD (Port 8080)          │                │
│  │    Globe + Chat + Stats + Controls  │                │
│  └──────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Algorithms

### 5.1 Intent Classification Pipeline

```
User Input
    │
    ▼
Wake Word Stripping ("jarvis open youtube" → "open youtube")
    │
    ▼
Spell Correction (SentenceTransformer similarity matching)
    │
    ▼
Pre-Router (exact keyword match for critical commands)
    ├── "shut up" / "keep quiet" → Stop Speaking + Quiet Mode
    ├── "shutdown" → Exit JARVIS Process
    ├── "turn off bluetooth" → PowerShell Radio Toggle
    ├── "switch off laptop" → System Shutdown
    │
    ▼
ML Intent Classifier (SentenceTransformer embeddings)
    ├── Encode user input → 384-dim vector
    ├── Compare against pre-defined intent embeddings via cosine similarity
    ├── Route to handler if confidence > threshold
    │
    ▼
Legacy Pattern Handler (fallback keyword matching)
    ├── "what time" → datetime.now()
    ├── "open <app>" → subprocess launch
    ├── "volume up/down" → pycaw adjustment
    │
    ▼
AI Knowledge Layer (Gemini 2.0 Flash)
    └── General conversation with Iron Man JARVIS personality
```

### 5.2 Gesture Detection Algorithm (MediaPipe)

```
Camera Frame (640×480 BGR)
    │
    ▼
Convert BGR → RGB → MediaPipe Image
    │
    ▼
HandLandmarker.detect() → 21 hand landmarks (x, y, z)
    │
    ▼
Calculate Features:
    ├── Palm Center = avg(wrist, middle_MCP)
    ├── Velocity = Δpalm / Δframe (smoothed)
    ├── Pinch Distance = dist(thumb_tip, index_tip)
    ├── Hand Angle = arctan2(middle_MCP - wrist)
    │
    ▼
Priority-Ordered Gesture Classification:
    1. Open Palm (≥4 fingers extended)  → stop_speaking
    2. Pinch (thumb-index < 0.05)       → play_pause / select
    3. Zoom (thumb-index > 0.12)        → zoom_in
    4. Rotation (Δangle > 0.02)         → seek / rotate globe
    5. Horizontal Swipe (vel_x > 0.015) → next / previous
    6. Vertical Swipe (vel_y > 0.015)   → scroll / volume
```

### 5.3 TTS Echo Prevention (2-Layer)

```
Layer 1: Flag-Based
    Before JARVIS speaks → mic_muted = True
    After speech ends → mic_muted = False (timed delay)

Layer 2: Content-Based
    For each voice input:
        Compare word set against last 3 JARVIS responses
        If word overlap > 50% → DROP as echo

Quiet Mode:
    After "shut up" → quiet_mode = True
    Voice loop only listens for wake word ("Jarvis" / "Friday")
    All other input is silently ignored
```

### 5.4 Face Recognition Algorithm

```
Registration:
    Capture 5 webcam frames → Detect face with MTCNN
    → Extract 512-dim embedding with InceptionResnetV1
    → Store embeddings + UserProfile in pickle file

Verification:
    Capture frame → Enhance low-light (CLAHE on LAB)
    → Detect face → Extract embedding
    → Compare against stored embeddings (cosine similarity)
    → If similarity > 0.7 → OWNER verified
    → If similarity > 0.5 → KNOWN_GUEST
    → Else → UNKNOWN
```

---

## 6. Approach & Implementation

### Phase 1: Core Foundation
- Built WebSocket server as the communication backbone
- Implemented voice recognition with Google Speech API  
- Created basic intent classification with keyword matching

### Phase 2: AI Integration
- Integrated Google Gemini 2.0 Flash for intelligent conversation
- Added Gemini Live API for full-duplex real-time voice
- Engineered Iron Man JARVIS personality prompt (dry wit, probability framing, loyal obedience)

### Phase 3: System Control
- Implemented Windows system commands: volume, brightness, app launching
- Added Bluetooth toggle via PowerShell Windows.Devices.Radios API
- Built compound command splitting ("do X and Y and Z")
- Added laptop shutdown/restart with safety delay

### Phase 4: Computer Vision
- Integrated MediaPipe HandLandmarker for gesture control
- Implemented face recognition with FaceNet-PyTorch
- Added emotion detection with CNN model
- Built app-aware gesture mapping (YouTube, Spotify, browser, PDF, globe)

### Phase 5: HUD Development
- Created browser-based HUD with WebSocket real-time updates
- Built 3D globe visualization with news integration
- Added chat interface, system stats, and mood indicators
- Implemented Web Speech API for browser-based TTS

### Phase 6: Bug Fixing & Polish
- Fixed TTS echo (2-layer prevention: flag + content matching)
- Added quiet mode for "shut up"/"keep quiet" commands
- Implemented silent mode for stop/shutdown responses
- Tuned gesture priority (open_palm before pinch/zoom)
- Removed robotic personality quirks (scripted phrases, excessive "sir")

---

## 7. Features Summary

| Feature | Status |
|---------|--------|
| Voice Commands | ✅ Working |
| AI Conversation (Groq/Gemini) | ✅ Working |
| Iron Man JARVIS Personality | ✅ Working |
| App Launching (20+ apps) | ✅ Working |
| Volume/Brightness Control | ✅ Working |
| Bluetooth Toggle | ✅ Working |
| Laptop Shutdown/Restart | ✅ Working |
| Screenshot | ✅ Working |
| Alarm/Reminder/Timer | ✅ Working |
| News with AI Opinions | ✅ Working |
| Weather | ✅ Working |
| Hand Gesture Control | ✅ Working |
| Open Palm → Stop Speaking | ✅ Working |
| Quiet Mode (wake word only) | ✅ Working |
| Compound Commands | ✅ Working |
| Spell Correction | ✅ Working |
| TTS Echo Prevention | ✅ Working |
| Browser HUD | ✅ Working |
| Face Recognition | ✅ Working |
| Emotion Detection | ✅ Working |
| WhatsApp Message Sending | ✅ Working |
| Gemini Live Voice | ✅ Working |
| BrainAdapter ML Pipeline | ✅ Working |
| Feature Hub (Tabbed UI) | ✅ Working |
| Tactical Personality | ✅ Working |
| JARVIS ↔ FRIDAY Persona | ✅ Working |

---

## 8. Future Enhancements

1. **NVIDIA Voice Model** — Replace browser TTS with NVIDIA open-source voice model for more natural, low-latency voice-to-voice conversation
2. **Smart Home Integration** — IoT control for lights, temperature, appliances
3. **User Presence Detection** — Activate/deactivate based on whether the user is at the desk
4. **Multi-User Support** — Different permissions and preferences per face-recognized user
5. **Plugin System** — Allow third-party skill development

---

*Last updated: May 2026*
