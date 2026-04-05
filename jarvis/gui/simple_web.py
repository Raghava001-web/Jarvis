"""
JARVIS Simple Web Interface - HTTP API
No WebSocket complexity - just simple HTTP requests
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
jarvis_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(jarvis_root))

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Global JARVIS instance
jarvis = None
perception = None

def init_jarvis():
    """Initialize JARVIS core"""
    global jarvis, perception
    try:
        from jarvis.core.jarvis_ultimate import JARVISUltimate
        jarvis = JARVISUltimate()
        perception = jarvis.perception
        print("[API] JARVIS Ultimate initialized")
        return True
    except Exception as e:
        print(f"[API] JARVIS init error: {e}")
        # Try simpler initialization
        try:
            from jarvis.core.perception import PerceptionLayer
            from jarvis.core.intent_classifier import classify_intent
            from jarvis.core.intent_handlers import HANDLER_MAP
            perception = PerceptionLayer()
            print("[API] Basic components initialized")
            return True
        except Exception as e2:
            print(f"[API] Basic init error: {e2}")
            return False

# Simple HTML interface
SIMPLE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
            color: #00d4ff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 0 0 20px #00d4ff;
        }
        .status {
            text-align: center;
            padding: 10px;
            background: rgba(0,212,255,0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status.listening { background: rgba(255,100,0,0.3); color: #ff9500; }
        .chat-box {
            background: rgba(0,40,60,0.5);
            border: 1px solid #00d4ff;
            border-radius: 15px;
            padding: 20px;
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .message {
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 10px;
            max-width: 80%;
        }
        .message.user {
            background: rgba(0,212,255,0.2);
            margin-left: auto;
            text-align: right;
        }
        .message.jarvis {
            background: rgba(255,149,0,0.2);
            border-left: 3px solid #ff9500;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            background: rgba(0,40,60,0.8);
            border: 1px solid #00d4ff;
            border-radius: 10px;
            color: #00d4ff;
            font-size: 16px;
        }
        input::placeholder { color: rgba(0,212,255,0.5); }
        button {
            padding: 15px 25px;
            background: rgba(0,212,255,0.3);
            border: 1px solid #00d4ff;
            border-radius: 10px;
            color: #00d4ff;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover { background: rgba(0,212,255,0.5); }
        button.listening { background: rgba(255,100,0,0.5); border-color: #ff9500; color: #ff9500; }
        .quick-btns {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        .quick-btn {
            padding: 10px 15px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>J.A.R.V.I.S.</h1>
        <div class="status" id="status">🟢 Ready - Click mic or type to speak</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message jarvis">Good day, sir. JARVIS online and ready.</div>
        </div>
        
        <div class="input-area">
            <input type="text" id="input" placeholder="Type a command..." onkeypress="if(event.key==='Enter')send()">
            <button onclick="send()">Send</button>
            <button id="micBtn" onclick="toggleMic()">🎤 Speak</button>
        </div>
        
        <div class="quick-btns">
            <button class="quick-btn" onclick="quickCmd('what time is it')">🕐 Time</button>
            <button class="quick-btn" onclick="quickCmd('weather')">🌤️ Weather</button>
            <button class="quick-btn" onclick="quickCmd('news')">📰 News</button>
            <button class="quick-btn" onclick="quickCmd('system status')">📊 System</button>
            <button class="quick-btn" onclick="quickCmd('tell me a joke')">😂 Joke</button>
            <button class="quick-btn" onclick="quickCmd('play music')">🎵 Music</button>
        </div>
    </div>

    <script>
        const chatBox = document.getElementById('chatBox');
        const input = document.getElementById('input');
        const status = document.getElementById('status');
        const micBtn = document.getElementById('micBtn');
        
        let recognition = null;
        let isListening = false;
        
        // Initialize speech recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                isListening = true;
                status.textContent = '🔴 Listening...';
                status.className = 'status listening';
                micBtn.className = 'listening';
                micBtn.textContent = '🔴 Listening';
            };
            
            recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                input.value = transcript;
                
                if (event.results[event.results.length - 1].isFinal) {
                    send();
                }
            };
            
            recognition.onend = () => {
                isListening = false;
                status.textContent = '🟢 Ready';
                status.className = 'status';
                micBtn.className = '';
                micBtn.textContent = '🎤 Speak';
            };
            
            recognition.onerror = (e) => {
                console.log('Speech error:', e.error);
                status.textContent = '⚠️ Mic error: ' + e.error;
            };
        }
        
        function toggleMic() {
            if (!recognition) {
                alert('Speech recognition not supported. Use Chrome.');
                return;
            }
            
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
        
        function addMessage(text, isUser) {
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'jarvis');
            div.textContent = text;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function send() {
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            input.value = '';
            status.textContent = '⏳ Processing...';
            
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: text})
            })
            .then(r => r.json())
            .then(data => {
                addMessage(data.response || data.error, false);
                status.textContent = '🟢 Ready';
                
                // Speak the response
                if (data.response && 'speechSynthesis' in window) {
                    const utter = new SpeechSynthesisUtterance(data.response);
                    utter.rate = 1.1;
                    utter.pitch = 0.9;
                    speechSynthesis.speak(utter);
                }
            })
            .catch(e => {
                addMessage('Connection error. Is JARVIS running?', false);
                status.textContent = '🔴 Error';
            });
        }
        
        function quickCmd(cmd) {
            input.value = cmd;
            send();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(SIMPLE_HTML)

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Process a command and return response"""
    try:
        data = request.json
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'No command provided'})
        
        print(f"[API] Command: {command}")
        
        # Process command through JARVIS
        if jarvis and hasattr(jarvis, 'process_command'):
            response = jarvis.process_command(command)
            return jsonify({'response': response})
        
        # Fallback: use intent classifier and handlers directly
        try:
            from jarvis.core.intent_classifier import classify_intent
            from jarvis.core.intent_handlers import HANDLER_MAP
            
            intent, entities = classify_intent(command)
            print(f"[API] Intent: {intent}, Entities: {entities}")
            
            handler = HANDLER_MAP.get(intent)
            if handler:
                context = {'title': 'sir', 'perception': perception}
                result = handler(command, entities, context)
                return jsonify({'response': result.response if hasattr(result, 'response') else str(result)})
            else:
                # Use AI for conversation
                try:
                    from jarvis.core.knowledge import KnowledgeLayer
                    knowledge = KnowledgeLayer()
                    response = knowledge.answer_question(command)
                    return jsonify({'response': response})
                except:
                    return jsonify({'response': f"I understood: {intent}. How can I help further?"})
        
        except Exception as e:
            print(f"[API] Handler error: {e}")
            return jsonify({'response': f"Processing: {command}"})
            
    except Exception as e:
        print(f"[API] Error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        import psutil
        return jsonify({
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'status': 'online'
        })
    except:
        return jsonify({'status': 'online'})

def run_server(port=5000):
    """Run the Flask server"""
    print(f"\n{'='*60}")
    print("   J.A.R.V.I.S. SIMPLE WEB INTERFACE")
    print(f"{'='*60}")
    print(f"\n   Open in browser: http://localhost:{port}")
    print(f"\n   Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    print("[API] Initializing JARVIS...")
    init_jarvis()
    run_server(5000)
