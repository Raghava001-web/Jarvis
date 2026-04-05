"""
JARVIS Web Interface - Complete Version
Features: Chat, Camera feed (face/gesture/mood), IP address, Widgets
"""

from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import threading
import sys
import socket
import cv2
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
jarvis_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(jarvis_root))

app = Flask(__name__)
CORS(app)

# Global instances
jarvis = None
perception = None
camera = None
is_speaking = False
should_stop = False

def get_local_ips():
    """Get all local IP addresses"""
    ips = []
    try:
        hostname = socket.gethostname()
        ips.append(f"Hostname: {hostname}")
        # Get all IPs
        for ip in socket.gethostbyname_ex(hostname)[2]:
            ips.append(f"Local: {ip}")
    except:
        pass
    try:
        # Get actual LAN IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(f"LAN: {s.getsockname()[0]}")
        s.close()
    except:
        pass
    return ips

def init_jarvis():
    """Initialize JARVIS core"""
    global jarvis, perception
    try:
        from jarvis.core.jarvis_ultimate import JARVISUltimate
        jarvis = JARVISUltimate()
        perception = jarvis.perception
        print("[WEB] JARVIS Ultimate initialized")
        return True
    except Exception as e:
        print(f"[WEB] JARVIS init error: {e}")
        return False

def init_camera():
    """Initialize camera for video feed"""
    global camera
    try:
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            print("[WEB] Camera initialized")
            return True
    except Exception as e:
        print(f"[WEB] Camera error: {e}")
    return False

# HTML with all widgets
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>J.A.R.V.I.S.</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
            color: #00d4ff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Grid Layout */
        .dashboard {
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            grid-template-rows: auto 1fr auto;
            gap: 15px;
            padding: 15px;
            height: 100vh;
        }
        
        /* Header */
        .header {
            grid-column: 1 / -1;
            text-align: center;
            padding: 10px;
        }
        h1 {
            font-size: 2.5em;
            text-shadow: 0 0 20px #00d4ff;
            letter-spacing: 8px;
        }
        
        /* Widget Base */
        .widget {
            background: rgba(0, 40, 60, 0.4);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 15px;
            backdrop-filter: blur(10px);
        }
        .widget-title {
            font-size: 12px;
            letter-spacing: 2px;
            opacity: 0.7;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
            padding-bottom: 5px;
        }
        
        /* Left Column - Widgets */
        .left-col { display: flex; flex-direction: column; gap: 15px; }
        
        /* Center - Main Content */
        .center-col { display: flex; flex-direction: column; gap: 15px; }
        
        /* Right Column - Widgets */
        .right-col { display: flex; flex-direction: column; gap: 15px; }
        
        /* Chat Widget */
        .chat-box {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            max-height: 400px;
        }
        .msg {
            margin: 8px 0;
            padding: 10px 14px;
            border-radius: 10px;
            max-width: 85%;
        }
        .msg.user { background: rgba(0, 212, 255, 0.2); margin-left: auto; }
        .msg.jarvis { background: rgba(255, 149, 0, 0.15); border-left: 3px solid #ff9500; }
        .input-row {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            background: rgba(0, 40, 60, 0.8);
            border: 1px solid rgba(0, 212, 255, 0.4);
            border-radius: 8px;
            color: #00d4ff;
            font-size: 14px;
        }
        button {
            padding: 12px 20px;
            background: rgba(0, 212, 255, 0.3);
            border: 1px solid #00d4ff;
            border-radius: 8px;
            color: #00d4ff;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover { background: rgba(0, 212, 255, 0.5); }
        button.listening { background: rgba(255, 50, 50, 0.5); border-color: #ff5555; }
        button.stop { background: rgba(255, 50, 50, 0.3); }
        
        /* Video Feed */
        .video-container {
            position: relative;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            height: 240px;
        }
        .video-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .video-overlay {
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
        }
        .detection-badge {
            background: rgba(0, 0, 0, 0.7);
            padding: 4px 10px;
            border-radius: 4px;
        }
        
        /* System Stats */
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 13px;
        }
        .stat-bar {
            width: 60%;
            height: 6px;
            background: rgba(0, 212, 255, 0.2);
            border-radius: 3px;
            overflow: hidden;
        }
        .stat-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            transition: width 0.5s;
        }
        
        /* IP Widget */
        .ip-list { font-size: 12px; }
        .ip-list div { margin: 4px 0; }
        
        /* Quick Actions */
        .quick-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .quick-btn {
            padding: 10px;
            font-size: 12px;
            text-align: center;
        }
        
        /* Feature Status */
        .feature-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 12px;
        }
        .feature-status {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
        }
        .feature-status.active { background: rgba(0, 255, 136, 0.3); color: #00ff88; }
        .feature-status.inactive { background: rgba(100, 100, 100, 0.3); color: #888; }
        
        /* Status Bar */
        .status-bar {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            padding: 10px 20px;
            font-size: 12px;
            opacity: 0.7;
        }
        
        /* Listening Animation */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .listening-indicator {
            animation: pulse 1s infinite;
            color: #ff5555;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <div class="header">
            <h1>J.A.R.V.I.S.</h1>
        </div>
        
        <!-- Left Column -->
        <div class="left-col">
            <!-- IP Address Widget -->
            <div class="widget">
                <div class="widget-title">📡 NETWORK</div>
                <div class="ip-list" id="ipList">Loading...</div>
            </div>
            
            <!-- System Stats -->
            <div class="widget">
                <div class="widget-title">📊 SYSTEM</div>
                <div class="stat-row">
                    <span>CPU</span>
                    <div class="stat-bar"><div class="stat-fill" id="cpuBar" style="width: 0%"></div></div>
                    <span id="cpuVal">0%</span>
                </div>
                <div class="stat-row">
                    <span>RAM</span>
                    <div class="stat-bar"><div class="stat-fill" id="ramBar" style="width: 0%"></div></div>
                    <span id="ramVal">0%</span>
                </div>
                <div class="stat-row">
                    <span>DISK</span>
                    <div class="stat-bar"><div class="stat-fill" id="diskBar" style="width: 0%"></div></div>
                    <span id="diskVal">0%</span>
                </div>
            </div>
            
            <!-- Features Status -->
            <div class="widget">
                <div class="widget-title">🔧 FEATURES</div>
                <div class="feature-row">
                    <span>👤 Face Recognition</span>
                    <span class="feature-status active" id="faceStatus">READY</span>
                </div>
                <div class="feature-row">
                    <span>✋ Gesture Control</span>
                    <span class="feature-status active" id="gestureStatus">READY</span>
                </div>
                <div class="feature-row">
                    <span>😊 Mood Detection</span>
                    <span class="feature-status active" id="moodStatus">READY</span>
                </div>
                <div class="feature-row">
                    <span>🎤 Voice Input</span>
                    <span class="feature-status active" id="voiceStatus">READY</span>
                </div>
            </div>
        </div>
        
        <!-- Center Column -->
        <div class="center-col">
            <!-- Camera Feed -->
            <div class="widget">
                <div class="widget-title">📹 CAMERA FEED</div>
                <div class="video-container">
                    <img id="videoFeed" src="/video_feed" alt="Camera">
                    <div class="video-overlay">
                        <span class="detection-badge" id="faceDetect">Face: --</span>
                        <span class="detection-badge" id="moodDetect">Mood: --</span>
                        <span class="detection-badge" id="gestureDetect">Gesture: --</span>
                    </div>
                </div>
            </div>
            
            <!-- Chat -->
            <div class="widget chat-box">
                <div class="widget-title">💬 CONVERSATION</div>
                <div class="messages" id="messages">
                    <div class="msg jarvis">At your service, sir. All systems operational.</div>
                </div>
                <div class="input-row">
                    <input type="text" id="input" placeholder="Type or speak..." onkeypress="if(event.key==='Enter')send()">
                    <button onclick="toggleMic()" id="micBtn">🎤</button>
                    <button onclick="send()">Send</button>
                    <button onclick="stopSpeech()" class="stop">⏹️ Stop</button>
                </div>
            </div>
        </div>
        
        <!-- Right Column -->
        <div class="right-col">
            <!-- Quick Actions -->
            <div class="widget">
                <div class="widget-title">⚡ QUICK ACTIONS</div>
                <div class="quick-grid">
                    <button class="quick-btn" onclick="cmd('what time is it')">🕐 Time</button>
                    <button class="quick-btn" onclick="cmd('weather')">🌤️ Weather</button>
                    <button class="quick-btn" onclick="cmd('news')">📰 News</button>
                    <button class="quick-btn" onclick="cmd('system status')">📊 Status</button>
                    <button class="quick-btn" onclick="cmd('tell me a joke')">😂 Joke</button>
                    <button class="quick-btn" onclick="cmd('play music')">🎵 Music</button>
                    <button class="quick-btn" onclick="cmd('recognize my face')">👤 Face ID</button>
                    <button class="quick-btn" onclick="cmd('detect my mood')">😊 Mood</button>
                </div>
            </div>
            
            <!-- Music Player placeholder -->
            <div class="widget">
                <div class="widget-title">🎵 NOW PLAYING</div>
                <div style="text-align: center; padding: 20px; opacity: 0.5;">
                    Say "play music" to start
                </div>
            </div>
            
            <!-- Date/Time -->
            <div class="widget">
                <div class="widget-title">📅 DATE & TIME</div>
                <div id="datetime" style="font-size: 18px; text-align: center;"></div>
            </div>
        </div>
        
        <!-- Status Bar -->
        <div class="status-bar">
            <span id="status">🟢 Connected</span>
            <span id="listeningStatus"></span>
            <span id="time"></span>
        </div>
    </div>

    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');
        let recognition = null;
        let isListening = false;
        
        // Speech recognition setup
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            
            recognition.onstart = () => {
                isListening = true;
                document.getElementById('micBtn').classList.add('listening');
                document.getElementById('micBtn').textContent = '🔴';
                document.getElementById('listeningStatus').innerHTML = '<span class="listening-indicator">🎤 LISTENING...</span>';
            };
            
            recognition.onresult = (e) => {
                let text = '';
                for (let i = e.resultIndex; i < e.results.length; i++) {
                    text += e.results[i][0].transcript;
                }
                input.value = text;
                if (e.results[e.results.length - 1].isFinal) send();
            };
            
            recognition.onend = () => {
                isListening = false;
                document.getElementById('micBtn').classList.remove('listening');
                document.getElementById('micBtn').textContent = '🎤';
                document.getElementById('listeningStatus').textContent = '';
            };
        }
        
        function toggleMic() {
            if (!recognition) return alert('Speech not supported');
            isListening ? recognition.stop() : recognition.start();
        }
        
        function addMsg(text, isUser) {
            const div = document.createElement('div');
            div.className = 'msg ' + (isUser ? 'user' : 'jarvis');
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function send() {
            const text = input.value.trim();
            if (!text) return;
            addMsg(text, true);
            input.value = '';
            document.getElementById('status').textContent = '⏳ Processing...';
            
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: text})
            })
            .then(r => r.json())
            .then(data => {
                addMsg(data.response || 'No response', false);
                document.getElementById('status').textContent = '🟢 Ready';
                // Speak response
                if (data.response && speechSynthesis) {
                    const u = new SpeechSynthesisUtterance(data.response);
                    u.rate = 1.1;
                    speechSynthesis.speak(u);
                }
            })
            .catch(() => {
                addMsg('Connection error', false);
                document.getElementById('status').textContent = '🔴 Error';
            });
        }
        
        function cmd(c) { input.value = c; send(); }
        
        function stopSpeech() {
            if (speechSynthesis) speechSynthesis.cancel();
            fetch('/api/stop');
        }
        
        // Update time
        setInterval(() => {
            const d = new Date();
            document.getElementById('datetime').textContent = d.toLocaleString();
            document.getElementById('time').textContent = d.toLocaleTimeString();
        }, 1000);
        
        // Load IPs
        fetch('/api/ips').then(r => r.json()).then(data => {
            document.getElementById('ipList').innerHTML = data.ips.map(ip => `<div>${ip}</div>`).join('');
        });
        
        // Update stats
        setInterval(() => {
            fetch('/api/status').then(r => r.json()).then(data => {
                document.getElementById('cpuBar').style.width = data.cpu + '%';
                document.getElementById('cpuVal').textContent = data.cpu + '%';
                document.getElementById('ramBar').style.width = data.memory + '%';
                document.getElementById('ramVal').textContent = data.memory + '%';
                if (data.disk) {
                    document.getElementById('diskBar').style.width = data.disk + '%';
                    document.getElementById('diskVal').textContent = data.disk + '%';
                }
            });
        }, 3000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_frames():
    """Generate video frames with detection overlay"""
    global camera
    while True:
        if camera and camera.isOpened():
            ret, frame = camera.read()
            if ret:
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Add detection overlays (placeholders)
                cv2.putText(frame, 'JARVIS VISION', (10, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                time.sleep(0.1)
        else:
            # No camera - yield placeholder
            time.sleep(0.5)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Process command"""
    global should_stop
    should_stop = False
    
    try:
        data = request.json
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'No command'})
        
        print(f"[WEB] Command: {command}")
        
        # Check for stop commands
        if command.lower() in ['stop', 'shut up', 'be quiet', 'cancel']:
            should_stop = True
            return jsonify({'response': 'Stopping, sir.'})
        
        # Process through JARVIS
        if jarvis and hasattr(jarvis, 'process_command'):
            response = jarvis.process_command(command)
            return jsonify({'response': str(response) if response else 'Understood, sir.'})
        
        # Fallback
        from jarvis.core.intent_classifier import classify_intent
        from jarvis.core.intent_handlers import HANDLER_MAP
        
        intent, entities = classify_intent(command)
        handler = HANDLER_MAP.get(intent)
        if handler:
            result = handler(command, entities, {'title': 'sir', 'perception': perception})
            return jsonify({'response': result.response if hasattr(result, 'response') else str(result)})
        
        return jsonify({'response': f"I understood intent: {intent}"})
        
    except Exception as e:
        print(f"[WEB] Error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/stop')
def stop_speaking():
    """Stop any ongoing speech"""
    global should_stop
    should_stop = True
    return jsonify({'status': 'stopped'})

@app.route('/api/ips')
def get_ips():
    """Get local IP addresses"""
    return jsonify({'ips': get_local_ips()})

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        import psutil
        return jsonify({
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
            'status': 'online'
        })
    except:
        return jsonify({'cpu': 0, 'memory': 0, 'status': 'partial'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("   J.A.R.V.I.S. WEB INTERFACE")
    print("="*60)
    
    init_jarvis()
    init_camera()
    
    ips = get_local_ips()
    print("\n   Access URLs:")
    print(f"   Local:   http://localhost:5000")
    for ip in ips:
        if 'LAN:' in ip:
            print(f"   Network: http://{ip.split(': ')[1]}:5000")
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
