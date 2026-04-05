"""
JARVIS Web HUD Launcher
Opens the Iron Man style holographic HUD with WebSocket backend
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import asyncio
from pathlib import Path

# Fix module imports by adding project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
jarvis_root = current_dir.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(jarvis_root))



def start_http_server(port=8080):
    """Start a simple HTTP server to serve the web HUD"""
    web_dir = Path(__file__).parent / "web_hud"
    
    if not web_dir.exists():
        print(f"[ERROR] Web HUD directory not found: {web_dir}")
        return None
    
    os.chdir(web_dir)
    
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    # Run in background thread
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    
    print(f"[HTTP] Serving at http://localhost:{port}")
    return httpd


def start_websocket_server():
    """Start the WebSocket server for backend communication"""
    try:
        from jarvis.gui.websocket_server import JARVISWebSocketServer
        server = JARVISWebSocketServer()
        server.run_in_thread()
        print("[WebSocket] Server started on ws://localhost:8765")
        return server
    except ImportError as e:
        print(f"[WebSocket] Could not start server: {e}")
        print("[WebSocket] Install websockets: pip install websockets")
        return None
    except Exception as e:
        print(f"[WebSocket] Error starting server: {e}")
        return None


def main():
    """Main entry point"""
    print("=" * 60)
    print("       J.A.R.V.I.S. HOLOGRAPHIC HUD")
    print("=" * 60)
    print()
    
    # Start HTTP server
    http_port = 8080
    httpd = start_http_server(http_port)
    
    if not httpd:
        print("[ERROR] Could not start HTTP server")
        return
    
    # Start WebSocket server
    ws_server = start_websocket_server()
    
    print()
    print("=" * 60)
    print("  JARVIS HUD ONLINE")
    print("=" * 60)
    print(f"  Web Interface: http://localhost:{http_port}")
    print(f"  WebSocket:     ws://localhost:8765")
    print()
    print("  Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()
    
    # Open browser (Chrome preferred — Brave blocks location)
    try:
        chrome = webbrowser.get('chrome')
        chrome.open(f"http://localhost:{http_port}")
    except webbrowser.Error:
        try:
            # Try explicit Chrome path on Windows
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
                webbrowser.get('chrome').open(f"http://localhost:{http_port}")
            else:
                webbrowser.open(f"http://localhost:{http_port}")
        except Exception:
            webbrowser.open(f"http://localhost:{http_port}")
    
    # Keep running
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[JARVIS] Shutting down...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
