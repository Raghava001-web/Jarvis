# 🎯 START HERE — JARVIS Quick Setup

## 3 Steps to Run

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create `.env` File
Copy the template and add your Gemini API key:
```bash
copy .env.example .env
```
Then edit `.env` and set:
```
GEMINI_API_KEY=your-gemini-api-key-here
```
Get your key at: https://aistudio.google.com/apikey

### Step 3: Run JARVIS
```bash
python jarvis/gui/websocket_server.py
```
Then open **http://localhost:8080** in your browser for the Web HUD.

---

## 🎤 First Commands to Try

1. "What time is it?" — basic functionality
2. "Open calculator" — app launching
3. "Tell me a joke" — AI conversation
4. "Tell me the news" — news headlines
5. "Switch to Friday" — persona swap

---

## 📁 Project Structure

- **`jarvis/gui/websocket_server.py`** — Start JARVIS here (main entry point)
- **`jarvis/core/`** — 68 core modules (brain, voice, tools, handlers)
- **`jarvis/gui/web_hud/`** — Iron Man Web HUD interface
- **`tests/`** — Smoke tests and unit tests
- **`jarvis_data/`** — Runtime data (auto-created, gitignored)

---

## ✅ Verify Installation

```bash
python -m pytest tests/test_smoke.py -v
```
All 53 tests should pass.

---

See `README.md` for full documentation.
