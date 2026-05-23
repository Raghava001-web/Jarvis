"""
JARVIS Desktop GUI — Iron Man Holographic HUD (mirrors Web HUD)
CustomTkinter + Canvas-based interface matching the web_hud/index.html design.
"""

import customtkinter as ctk
import tkinter as tk
import threading
import json
import time
import datetime
import asyncio
import sys
import os
import math
import random
from pathlib import Path

# Fix imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# ── Theme ──
ctk.set_appearance_mode("dark")

# ── Colors (matching Web HUD CSS variables) ──
C = {
    "bg":           "#020a12",
    "panel_bg":     "#001828",
    "panel_border": "#005480",
    "cyan":         "#00d4ff",
    "cyan_dim":     "#0099cc",
    "cyan_glow":    "#005580",
    "orange":       "#ff9500",
    "green":        "#00ff88",
    "red":          "#ff4444",
    "text":         "#00d4ff",
    "text_dim":     "#0088aa",
    "text_muted":   "#004466",
}


class HoloPanel(ctk.CTkFrame):
    """Holographic floating panel — mirrors .holo-panel CSS class."""

    def __init__(self, master, title="", width=220, **kwargs):
        super().__init__(
            master, width=width,
            fg_color="#001420",
            border_color="#005577",
            border_width=1,
            corner_radius=12,
            **kwargs
        )

        # Top glow line
        glow = ctk.CTkFrame(self, height=2, fg_color=C["cyan_dim"], corner_radius=0)
        glow.pack(fill="x", padx=0, pady=0)

        if title:
            title_frame = ctk.CTkFrame(self, fg_color="transparent")
            title_frame.pack(fill="x", padx=14, pady=(10, 6))

            ctk.CTkLabel(
                title_frame, text="◆",
                font=("Consolas", 8), text_color=C["orange"]
            ).pack(side="left", padx=(0, 6))

            ctk.CTkLabel(
                title_frame, text=title.upper(),
                font=("Consolas", 10, "bold"),
                text_color=C["orange"]
            ).pack(side="left")

        # Content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=14, pady=(0, 12))


class OrbCanvas(tk.Canvas):
    """Central JARVIS orb — matches .jarvis-orb + .orb-core + .orb-ring CSS."""

    def __init__(self, master, size=200, **kwargs):
        super().__init__(master, width=size, height=size,
                         bg="#020a12", highlightthickness=0, bd=0, **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.phase = 0
        self.ring_angle = 0
        self.state = "idle"
        self.particles = []
        for _ in range(25):
            self.particles.append({
                "angle": random.uniform(0, 360),
                "radius": random.uniform(50, 90),
                "speed": random.uniform(0.2, 0.8),
                "size": random.uniform(1, 3),
            })
        self._draw()

    def set_state(self, state):
        self.state = state.lower() if state else "idle"

    def _draw(self):
        self.delete("all")

        self.phase += 0.04
        self.ring_angle += 0.3
        pulse = (math.sin(self.phase) + 1) / 2

        # State color
        colors = {
            "idle":       ("#003050", "#00aadd", "#00d4ff"),
            "listening":  ("#003322", "#00cc66", "#00ff88"),
            "processing": ("#332200", "#ccaa00", "#ffcc00"),
            "speaking":   ("#002244", "#0088ff", "#00bbff"),
        }
        dark, mid, bright = colors.get(self.state, colors["idle"])

        # Outer glow
        for i in range(3):
            r = 85 - i * 5 + int(pulse * 3)
            alpha = hex(int(30 + i * 15))[2:].zfill(2)
            self.create_oval(
                self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                outline=dark, width=1
            )

        # Ring 3 (outermost)
        r3 = 80
        self.create_oval(
            self.cx - r3, self.cy - r3, self.cx + r3, self.cy + r3,
            outline=mid, width=1, dash=(4, 6)
        )

        # Ring 2
        r2 = 65
        self.create_oval(
            self.cx - r2, self.cy - r2, self.cx + r2, self.cy + r2,
            outline=mid, width=2
        )

        # Rotating tick marks on ring 2
        for i in range(12):
            a = math.radians(self.ring_angle + i * 30)
            x1 = self.cx + math.cos(a) * (r2 - 4)
            y1 = self.cy + math.sin(a) * (r2 - 4)
            x2 = self.cx + math.cos(a) * (r2 + 4)
            y2 = self.cy + math.sin(a) * (r2 + 4)
            self.create_line(x1, y1, x2, y2, fill=mid, width=1)

        # Ring 1 (inner)
        r1 = 45
        self.create_oval(
            self.cx - r1, self.cy - r1, self.cx + r1, self.cy + r1,
            outline=mid, width=2
        )

        # Arc segments (rotating)
        for i in range(3):
            start = self.ring_angle * 2 + i * 120
            self.create_arc(
                self.cx - 55, self.cy - 55, self.cx + 55, self.cy + 55,
                start=start, extent=40, outline=bright, width=2, style="arc"
            )

        # Core glow
        core_r = int(22 + pulse * 6)
        # Outer glow
        for blur_r in range(core_r + 10, core_r, -2):
            self.create_oval(
                self.cx - blur_r, self.cy - blur_r,
                self.cx + blur_r, self.cy + blur_r,
                fill="", outline=dark, width=1
            )
        # Core
        self.create_oval(
            self.cx - core_r, self.cy - core_r,
            self.cx + core_r, self.cy + core_r,
            fill=bright, outline=""
        )

        # Floating particles
        for p in self.particles:
            p["angle"] += p["speed"]
            a = math.radians(p["angle"])
            x = self.cx + math.cos(a) * p["radius"]
            y = self.cy + math.sin(a) * p["radius"]
            s = p["size"]
            self.create_oval(x - s, y - s, x + s, y + s, fill=mid, outline="")

        # State text below orb
        state_text = {
            "idle": "STANDBY", "listening": "LISTENING",
            "processing": "PROCESSING", "speaking": "SPEAKING"
        }
        self.create_text(
            self.cx, self.size - 8,
            text=state_text.get(self.state, "ONLINE"),
            fill=bright, font=("Consolas", 9, "bold")
        )

        self.after(33, self._draw)


class JARVISDesktopApp(ctk.CTk):
    """Main JARVIS Desktop HUD — layout mirrors the Web HUD."""

    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S. HUD")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=C["bg"])

        # Set icon
        icon_path = Path(__file__).parent / "web_hud" / "favicon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # State
        self.ws = None
        self.ws_connected = False
        self.server = None
        self.messages = []
        self._ws_loop = None

        # Build UI
        self._build_top_bar()
        self._build_main_area()

        # Start
        self._update_clock()
        self._update_system_stats()
        self._start_backend()

    # ═══════════════════════════════════════════════════
    # TOP BAR — matches .top-bar CSS
    # ═══════════════════════════════════════════════════
    def _build_top_bar(self):
        bar = ctk.CTkFrame(self, height=50, fg_color="#000D1A", corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left: Logo
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=20)

        ctk.CTkLabel(
            left, text="J.A.R.V.I.S.",
            font=("Consolas", 18, "bold"), text_color=C["cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            left, text="  HOLOGRAPHIC HUD",
            font=("Consolas", 11), text_color=C["text_dim"]
        ).pack(side="left")

        # Right: Status + Clock
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=20)

        # Connection status
        self.conn_dot = ctk.CTkLabel(right, text="●", font=("Consolas", 12),
                                     text_color=C["red"])
        self.conn_dot.pack(side="right", padx=(0, 5))

        self.conn_text = ctk.CTkLabel(right, text="OFFLINE",
                                      font=("Consolas", 10), text_color=C["red"])
        self.conn_text.pack(side="right", padx=(0, 3))

        ctk.CTkLabel(right, text="│", font=("Consolas", 14),
                     text_color="#002040").pack(side="right", padx=10)

        self.clock_label = ctk.CTkLabel(right, text="--:--:-- --",
                                        font=("Consolas", 13), text_color=C["cyan"])
        self.clock_label.pack(side="right")

        ctk.CTkLabel(right, text="│", font=("Consolas", 14),
                     text_color="#002040").pack(side="right", padx=10)

        self.date_label = ctk.CTkLabel(right, text="---",
                                       font=("Consolas", 11), text_color=C["text_dim"])
        self.date_label.pack(side="right")

    # ═══════════════════════════════════════════════════
    # MAIN AREA — left panels, center orb, right panels, bottom chat
    # ═══════════════════════════════════════════════════
    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # Left column
        left_col = ctk.CTkFrame(main, fg_color="transparent", width=240)
        left_col.pack(side="left", fill="y", padx=(15, 5), pady=10)
        left_col.pack_propagate(False)

        self._build_weather_panel(left_col)
        self._build_system_panel(left_col)
        self._build_quick_actions(left_col)

        # Right column
        right_col = ctk.CTkFrame(main, fg_color="transparent", width=220)
        right_col.pack(side="right", fill="y", padx=(5, 15), pady=10)
        right_col.pack_propagate(False)

        self._build_features_panel(right_col)
        self._build_news_panel(right_col)

        # Center: Orb + Chat
        center = ctk.CTkFrame(main, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True, padx=5, pady=10)

        # Orb in upper center
        orb_frame = ctk.CTkFrame(center, fg_color="transparent")
        orb_frame.pack(fill="both", expand=True)

        self.orb = OrbCanvas(orb_frame, size=200)
        self.orb.place(relx=0.5, rely=0.4, anchor="center")

        # Chat at bottom center
        self._build_chat_panel(center)

    # ═══════════════════════════════════════════════════
    # WEATHER PANEL — matches #weatherPanel
    # ═══════════════════════════════════════════════════
    def _build_weather_panel(self, parent):
        panel = HoloPanel(parent, title="WEATHER", width=230)
        panel.pack(fill="x", pady=(0, 8))

        self.weather_temp = ctk.CTkLabel(
            panel.content, text="--°C",
            font=("Consolas", 28, "bold"), text_color=C["cyan"]
        )
        self.weather_temp.pack(anchor="w")

        self.weather_desc = ctk.CTkLabel(
            panel.content, text="Loading...",
            font=("Consolas", 12), text_color=C["text_dim"]
        )
        self.weather_desc.pack(anchor="w")

        self.weather_location = ctk.CTkLabel(
            panel.content, text="📍 ---",
            font=("Consolas", 10), text_color=C["text_muted"]
        )
        self.weather_location.pack(anchor="w", pady=(4, 0))

    # ═══════════════════════════════════════════════════
    # SYSTEM STATUS — matches #systemPanel
    # ═══════════════════════════════════════════════════
    def _build_system_panel(self, parent):
        panel = HoloPanel(parent, title="SYSTEM STATUS", width=230)
        panel.pack(fill="x", pady=(0, 8))

        self.sys_labels = {}
        for key, icon in [("CPU", "⚡"), ("RAM", "💾"), ("DISK", "📁"), ("BAT", "🔋")]:
            row = ctk.CTkFrame(panel.content, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f"{icon} {key}", font=("Consolas", 11),
                         text_color=C["text_dim"]).pack(side="left")

            val = ctk.CTkLabel(row, text="---%", font=("Consolas", 11, "bold"),
                               text_color=C["cyan"])
            val.pack(side="right")
            self.sys_labels[key] = val

            # Progress bar
            bar = ctk.CTkProgressBar(panel.content, height=4,
                                     fg_color="#001520", progress_color=C["cyan_dim"])
            bar.pack(fill="x", pady=(0, 4))
            bar.set(0)
            self.sys_labels[f"{key}_bar"] = bar

    # ═══════════════════════════════════════════════════
    # QUICK ACTIONS — matches #quickActionsPanel
    # ═══════════════════════════════════════════════════
    def _build_quick_actions(self, parent):
        panel = HoloPanel(parent, title="QUICK ACTIONS", width=230)
        panel.pack(fill="x", pady=(0, 8))

        actions = [
            ("🎤", "Voice Command", self._focus_input),
            ("📸", "Screenshot", self._take_screenshot),
            ("🌐", "Web HUD", self._open_web_hud),
            ("🔒", "Lock Screen", self._lock_screen),
        ]

        for icon, label, cmd in actions:
            btn = ctk.CTkButton(
                panel.content, text=f"  {icon}  {label}",
                anchor="w", height=32,
                fg_color="#001525", hover_color="#002a40",
                border_color="#005577", border_width=1,
                text_color=C["cyan"], font=("Consolas", 11),
                corner_radius=6, command=cmd
            )
            btn.pack(fill="x", pady=2)

    # ═══════════════════════════════════════════════════
    # FEATURES PANEL — matches #featurePanel
    # ═══════════════════════════════════════════════════
    def _build_features_panel(self, parent):
        panel = HoloPanel(parent, title="FEATURES", width=210)
        panel.pack(fill="x", pady=(0, 8))

        self.feature_indicators = {}
        features = [
            ("🎤", "Voice", True),
            ("👋", "Gesture", False),
            ("👤", "Face ID", False),
            ("😊", "Emotion", False),
            ("🧠", "AI Engine", True),
        ]

        for icon, name, active in features:
            row = ctk.CTkFrame(panel.content, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=f"{icon} {name}", font=("Consolas", 11),
                         text_color=C["text_dim"]).pack(side="left")

            status = ctk.CTkLabel(
                row,
                text="ACTIVE" if active else "OFF",
                font=("Consolas", 9, "bold"),
                text_color=C["green"] if active else C["text_muted"]
            )
            status.pack(side="right")
            self.feature_indicators[name] = status

    # ═══════════════════════════════════════════════════
    # NEWS PANEL
    # ═══════════════════════════════════════════════════
    def _build_news_panel(self, parent):
        panel = HoloPanel(parent, title="NEWS FEED", width=210)
        panel.pack(fill="x", pady=(0, 8))

        self.news_frame = panel.content

        for i in range(3):
            ctk.CTkLabel(
                self.news_frame, text=f"Loading headlines...",
                font=("Consolas", 10), text_color=C["text_dim"],
                wraplength=180, justify="left", anchor="w"
            ).pack(fill="x", pady=3)

    # ═══════════════════════════════════════════════════
    # CHAT PANEL — matches #chatPanel
    # ═══════════════════════════════════════════════════
    def _build_chat_panel(self, parent):
        chat_panel = HoloPanel(parent, title="COMMUNICATION LOG")
        chat_panel.pack(fill="x", pady=(0, 0), padx=10)

        # Scrollable messages
        self.chat_scroll = ctk.CTkScrollableFrame(
            chat_panel.content, height=150,
            fg_color="transparent",
            scrollbar_button_color="#003050",
            scrollbar_button_hover_color=C["cyan_dim"]
        )
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 8))

        # Welcome
        self._add_chat_msg("jarvis", "Systems online, sir. How may I assist you?")

        # Input bar
        input_frame = ctk.CTkFrame(chat_panel.content, fg_color="transparent")
        input_frame.pack(fill="x")

        self.chat_input = ctk.CTkEntry(
            input_frame, placeholder_text="Type a command...",
            font=("Consolas", 13), height=36,
            fg_color="#001828", border_color="#005577",
            text_color=C["cyan"],
            placeholder_text_color="#004466"
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.chat_input.bind("<Return>", self._on_send)

        send_btn = ctk.CTkButton(
            input_frame, text="SEND", width=70, height=36,
            fg_color="#002a40", hover_color="#004060",
            border_color=C["cyan_dim"], border_width=1,
            text_color=C["cyan"], font=("Consolas", 11, "bold"),
            command=lambda: self._on_send(None)
        )
        send_btn.pack(side="right")

    # ═══════════════════════════════════════════════════
    # CHAT MESSAGES — matches .chat-message CSS
    # ═══════════════════════════════════════════════════
    def _add_chat_msg(self, sender, text):
        if not text or not text.strip():
            return

        is_jarvis = sender.lower() in ("jarvis", "friday")
        is_user = sender.lower() == "user"

        # Color scheme matches CSS
        if is_jarvis:
            bg_color = "#001828"
            border_color = C["cyan"]
            text_color = "#00bbdd"
            name = "JARVIS"
        else:
            bg_color = "#001410"
            border_color = C["green"]
            text_color = "#00dd77"
            name = "YOU"

        msg_frame = ctk.CTkFrame(self.chat_scroll, fg_color=bg_color,
                                 corner_radius=6)
        msg_frame.pack(fill="x", pady=3, padx=2)

        # Left border accent (like border-left: 3px)
        accent = ctk.CTkFrame(msg_frame, width=3, fg_color=border_color,
                              corner_radius=0)
        accent.pack(side="left", fill="y")

        content = ctk.CTkFrame(msg_frame, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=6)

        # Sender name
        ctk.CTkLabel(
            content, text=name,
            font=("Consolas", 9, "bold"), text_color=border_color
        ).pack(anchor="w")

        # Message text
        ctk.CTkLabel(
            content, text=text.strip(),
            font=("Consolas", 12), text_color=text_color,
            wraplength=400, justify="left", anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        self.messages.append(msg_frame)

        # Auto-scroll
        self.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    # ═══════════════════════════════════════════════════
    # INPUT / SEND
    # ═══════════════════════════════════════════════════
    def _on_send(self, event):
        text = self.chat_input.get().strip()
        if not text:
            return
        self.chat_input.delete(0, "end")
        self._add_chat_msg("user", text)

        if self.ws and self.ws_connected:
            try:
                msg = json.dumps({"type": "chat", "text": text})
                asyncio.run_coroutine_threadsafe(self.ws.send(msg), self._ws_loop)
            except Exception as e:
                self._add_chat_msg("jarvis", f"Connection error: {e}")

    def _focus_input(self):
        self.chat_input.focus()

    def _take_screenshot(self):
        if self.ws and self.ws_connected:
            msg = json.dumps({"type": "chat", "text": "take a screenshot"})
            asyncio.run_coroutine_threadsafe(self.ws.send(msg), self._ws_loop)

    def _open_web_hud(self):
        import webbrowser
        # Start HTTP server if not already running
        if not hasattr(self, '_http_server'):
            try:
                from jarvis.gui.web_hud_launcher import start_http_server
                self._http_server = start_http_server(8080)
            except Exception as e:
                print(f"[DESKTOP] HTTP server error: {e}")
        webbrowser.open("http://localhost:8080")

    def _lock_screen(self):
        import subprocess
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)

    # ═══════════════════════════════════════════════════
    # CLOCK & SYSTEM STATS
    # ═══════════════════════════════════════════════════
    def _update_clock(self):
        now = datetime.datetime.now()
        self.clock_label.configure(text=now.strftime("%I:%M:%S %p"))
        self.date_label.configure(text=now.strftime("%A, %b %d"))
        self.after(1000, self._update_clock)

    def _update_system_stats(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            self.sys_labels["CPU"].configure(text=f"{cpu:.0f}%")
            self.sys_labels["CPU_bar"].set(cpu / 100)
            self.sys_labels["RAM"].configure(text=f"{ram:.0f}%")
            self.sys_labels["RAM_bar"].set(ram / 100)
            self.sys_labels["DISK"].configure(text=f"{disk:.0f}%")
            self.sys_labels["DISK_bar"].set(disk / 100)

            bat = psutil.sensors_battery()
            if bat:
                self.sys_labels["BAT"].configure(
                    text=f"{bat.percent:.0f}%{'⚡' if bat.power_plugged else ''}")
                self.sys_labels["BAT_bar"].set(bat.percent / 100)
        except Exception:
            pass
        self.after(3000, self._update_system_stats)

    # ═══════════════════════════════════════════════════
    # BACKEND CONNECTION
    # ═══════════════════════════════════════════════════
    def _start_backend(self):
        threading.Thread(target=self._backend_thread, daemon=True).start()

    def _backend_thread(self):
        try:
            from jarvis.gui.websocket_server import JARVISWebSocketServer
            self.server = JARVISWebSocketServer()
            self.server.run_in_thread()
            print("[DESKTOP] WebSocket server started")
        except Exception as e:
            err_msg = str(e)
            print(f"[DESKTOP] Server error: {err_msg}")
            self.after(0, lambda e_msg=err_msg: self._add_chat_msg(
                "jarvis", f"Backend startup failed: {e_msg}"))
            return

        time.sleep(2)
        self._ws_loop = asyncio.new_event_loop()
        threading.Thread(target=self._ws_client_loop, daemon=True).start()

    def _ws_client_loop(self):
        asyncio.set_event_loop(self._ws_loop)
        self._ws_loop.run_until_complete(self._ws_connect())

    async def _ws_connect(self):
        import websockets
        uri = "ws://localhost:8765"
        retry = 0

        while retry < 15:
            try:
                async with websockets.connect(uri) as ws:
                    self.ws = ws
                    self.ws_connected = True
                    retry = 0
                    self.after(0, self._set_connected, True)
                    print("[DESKTOP] WebSocket connected")

                    # Request full state + weather + news on connect
                    try:
                        await ws.send(json.dumps({"type": "get_state"}))
                        await ws.send(json.dumps({"type": "get_weather"}))
                        await ws.send(json.dumps({"type": "get_news"}))
                    except Exception:
                        pass

                    async for message in ws:
                        try:
                            data = json.loads(message)
                            self.after(0, self._handle_ws_message, data)
                        except json.JSONDecodeError:
                            pass

            except Exception as e:
                self.ws_connected = False
                self.after(0, self._set_connected, False)
                retry += 1
                await asyncio.sleep(2)

    def _set_connected(self, connected):
        if connected:
            self.conn_dot.configure(text_color=C["green"])
            self.conn_text.configure(text="ONLINE", text_color=C["green"])
        else:
            self.conn_dot.configure(text_color=C["red"])
            self.conn_text.configure(text="OFFLINE", text_color=C["red"])

    def _handle_ws_message(self, data):
        """Handle ALL WebSocket message types — mirrors Web HUD handleServerMessage()."""
        msg_type = data.get("type", "")

        # ── Chat: JARVIS response ──
        if msg_type == "response":
            text = data.get("text", "")
            if text:
                self._add_chat_msg("jarvis", text)
                self.orb.set_state("speaking")
                self.after(2000, lambda: self.orb.set_state("idle"))

        # ── Chat: Tool result ──
        elif msg_type == "result":
            text = data.get("response", "")
            if text:
                self._add_chat_msg("jarvis", text)
                self.orb.set_state("speaking")
                self.after(2000, lambda: self.orb.set_state("idle"))
            # Update state if included
            if data.get("state"):
                self._render_full_state(data["state"])

        # ── Chat: User voice input ──
        elif msg_type == "voice_recognized":
            text = data.get("text", "")
            if text:
                self._add_chat_msg("user", text)
                self.orb.set_state("listening")
                self.after(1500, lambda: self.orb.set_state("processing"))

        # ── Error ──
        elif msg_type == "error":
            msg = data.get("message", "Unknown error")
            self._add_chat_msg("jarvis", f"⚠ Error: {msg}")

        # ── Stop speaking (no-op for desktop since TTS is on server) ──
        elif msg_type == "stop_speaking":
            pass

        # ── Gemini Live transcription (real-time audio speech) ──
        elif msg_type == "live_transcription":
            text = data.get("text", "")
            role = data.get("role", "jarvis")
            if text:
                sender = "user" if role == "user" else "jarvis"
                self._add_chat_msg(sender, text)
                if sender == "jarvis":
                    self.orb.set_state("speaking")
                    self.after(2000, lambda: self.orb.set_state("idle"))
                else:
                    self.orb.set_state("listening")
                    self.after(1000, lambda: self.orb.set_state("processing"))

        # ── Full state update ──
        elif msg_type in ("state", "feature_status"):
            state = data.get("state", data)
            if state:
                self._render_full_state(state)

        # ── System status (CPU/RAM from server) ──
        elif msg_type == "status":
            try:
                if "cpu" in data:
                    self.sys_labels["CPU"].configure(text=f"{data['cpu']:.0f}%")
                    self.sys_labels["CPU_bar"].set(data["cpu"] / 100)
                if "ram" in data or "memory" in data:
                    ram = data.get("ram", data.get("memory", 0))
                    self.sys_labels["RAM"].configure(text=f"{ram:.0f}%")
                    self.sys_labels["RAM_bar"].set(ram / 100)
            except Exception:
                pass

        # ── Weather ──
        elif msg_type == "weather":
            try:
                temp = data.get("temp", data.get("temperature", "--"))
                desc = data.get("description", data.get("condition", ""))
                city = data.get("city", data.get("location", ""))
                humidity = data.get("humidity", "")
                self.weather_temp.configure(text=f"{temp}°C")
                desc_text = desc.title() if desc else ""
                if humidity:
                    desc_text += f" • 💧{humidity}%"
                self.weather_desc.configure(text=desc_text)
                self.weather_location.configure(text=f"📍 {city}" if city else "")
            except Exception:
                pass

        # ── News ──
        elif msg_type == "news":
            items = data.get("items", data.get("headlines", []))
            if items:
                for w in self.news_frame.winfo_children():
                    w.destroy()
                for item in items[:5]:
                    title = item if isinstance(item, str) else item.get("title", "")
                    if title:
                        ctk.CTkLabel(
                            self.news_frame, text=f"• {title[:60]}",
                            font=("Consolas", 10), text_color=C["text_dim"],
                            wraplength=180, justify="left", anchor="w"
                        ).pack(fill="x", pady=2)

        # ── Assistant info (name/mode) ──
        elif msg_type == "assistant_info":
            name = data.get("name", "JARVIS")
            # Could update title if switching to FRIDAY etc.
            self.title(f"{name.upper()} HUD")

        # ── Gesture feedback ──
        elif msg_type in ("gesture_feedback", "gesture_action"):
            gesture = data.get("gesture", "")
            action = data.get("action", "")
            if gesture:
                if "Gesture" in self.feature_indicators:
                    self.feature_indicators["Gesture"].configure(
                        text=gesture.upper(), text_color=C["orange"]
                    )
                    # Reset after 3 seconds
                    self.after(3000, lambda: self.feature_indicators["Gesture"].configure(
                        text="ACTIVE", text_color=C["green"]
                    ))
            if action == "stop_speaking":
                self._add_chat_msg("jarvis", "🤚 Speech stopped (palm gesture)")

        # ── Emotion update ──
        elif msg_type == "emotion_update":
            emotion = data.get("emotion", "neutral")
            if "Emotion" in self.feature_indicators:
                self.feature_indicators["Emotion"].configure(
                    text=emotion.upper(), text_color=C["orange"]
                )

        # ── Face recognition update ──
        elif msg_type == "face_update":
            user = data.get("user", "")
            confidence = data.get("confidence", 0)
            if user and "Face ID" in self.feature_indicators:
                self.feature_indicators["Face ID"].configure(
                    text=f"{user.upper()}", text_color=C["green"]
                )

        # ── Speak request (server wants browser TTS — not needed for desktop) ──
        elif msg_type == "speak":
            pass  # Desktop uses server-side TTS through Gemini Live

        # ── Startup briefing (full boot data) ──
        elif msg_type == "startup_briefing":
            briefing = data.get("briefing", {})
            
            # Auto-enable all feature indicators
            features = briefing.get("features_enabled", {})
            for name, indicator in self.feature_indicators.items():
                indicator.configure(text="ACTIVE", text_color=C["green"])
            
            # Update weather from boot data
            weather_ctx = briefing.get("weather_context", "")
            if weather_ctx and "°C" in weather_ctx:
                try:
                    temp = weather_ctx.split("°C")[0].split()[-1]
                    desc = weather_ctx.split(",")[-1].strip() if "," in weather_ctx else ""
                    self.weather_temp.configure(text=f"{temp}°C")
                    if desc:
                        self.weather_desc.configure(text=desc.title())
                except Exception:
                    pass
            
            # Update system stats from boot data
            sys_status = briefing.get("system_status", {})
            if sys_status:
                for key, api_key in [("CPU", "cpu"), ("RAM", "ram")]:
                    val = sys_status.get(api_key)
                    if val is not None:
                        self.sys_labels[key].configure(text=f"{val:.0f}%")
                        self.sys_labels[f"{key}_bar"].set(val / 100)
                bat = sys_status.get("battery")
                if bat is not None:
                    plug = "⚡" if sys_status.get("plugged") else ""
                    self.sys_labels["BAT"].configure(text=f"{bat:.0f}%{plug}")
                    self.sys_labels["BAT_bar"].set(bat / 100)

        # ── Init Payload / Greeting ──
        elif msg_type == "init_payload":
            greeting_group = data.get("greeting", {})
            greeting_text = greeting_group.get("text", "")
            if greeting_text:
                self._add_chat_msg("jarvis", greeting_text)
                self.orb.set_state("speaking")
                self.after(3000, lambda: self.orb.set_state("idle"))

    def _render_full_state(self, state):
        """Update all UI panels from a full state object — mirrors renderFullState()."""
        if not state:
            return

        # Feature indicators
        mapping = {
            "gesture_enabled": "Gesture",
            "gesture_available": "Gesture",
            "face_enabled": "Face ID",
            "face_available": "Face ID",
            "emotion_enabled": "Emotion",
            "emotion_available": "Emotion",
        }
        for key, name in mapping.items():
            if key in state and name in self.feature_indicators:
                active = state[key]
                if "available" in key and not active:
                    self.feature_indicators[name].configure(
                        text="OFF", text_color=C["text_muted"]
                    )
                elif active:
                    self.feature_indicators[name].configure(
                        text="ACTIVE", text_color=C["green"]
                    )
                else:
                    self.feature_indicators[name].configure(
                        text="OFF", text_color=C["text_muted"]
                    )

        # Last gesture
        if state.get("last_gesture"):
            g = state["last_gesture"]
            if "Gesture" in self.feature_indicators:
                self.feature_indicators["Gesture"].configure(
                    text=g.upper(), text_color=C["orange"]
                )

        # Current emotion/mood
        mood = state.get("current_mood", state.get("mood", ""))
        if mood and "Emotion" in self.feature_indicators:
            self.feature_indicators["Emotion"].configure(
                text=mood.upper(), text_color=C["orange"] if mood != "neutral" else C["green"]
            )

        # Orb state from JARVIS state
        jarvis_state = state.get("jarvis_state", state.get("state", ""))
        if jarvis_state:
            self.orb.set_state(jarvis_state)

    def on_closing(self):
        print("[DESKTOP] Shutting down...")
        self.destroy()
        sys.exit(0)


def main():
    print("=" * 60)
    print("     J.A.R.V.I.S. DESKTOP INTERFACE")
    print("=" * 60)
    print()

    app = JARVISDesktopApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
