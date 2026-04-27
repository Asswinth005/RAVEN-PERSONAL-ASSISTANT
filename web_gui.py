"""
FRIDAY Web GUI — Flask + SocketIO
Iron Man-inspired real-time dashboard.
"""
import json
import datetime
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import config
from brain import RavenBrain
from automation import RavenAutomation
from router import CommandRouter

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Initialize RAVEN core systems
brain = RavenBrain()
automation = RavenAutomation()
router = CommandRouter(automation)

# Optional voice
try:
    from voice import RavenVoice
    voice = RavenVoice()
    VOICE_ENABLED = True
except Exception as e:
    print(f"[{config.ASSISTANT_NAME}] Voice module not loaded: {e}")
    voice = None
    VOICE_ENABLED = False


@app.route('/')
def index():
    return render_template('index.html',
                         assistant_name=config.ASSISTANT_NAME,
                         boss_name=config.BOSS_NAME)


@app.route('/api/system', methods=['GET'])
def system_info():
    return jsonify(automation.get_system_info())


@app.route('/api/processes', methods=['GET'])
def processes():
    return jsonify(automation.get_running_processes(15))


@app.route('/api/diagnostics', methods=['GET'])
def diagnostics():
    return jsonify(automation.get_diagnostics())


@app.route('/api/reminders', methods=['GET'])
def reminders():
    # Return only active (untriggered) reminders
    active = [r for r in automation.reminders if not r.get("triggered")]
    return jsonify(active)


@socketio.on('connect')
def handle_connect():
    print(f"[{config.ASSISTANT_NAME}] Client connected")
    emit('friday_message', {
        'type': 'system',
        'content': f'{config.ASSISTANT_NAME} online. All systems operational, {config.BOSS_NAME}.',
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
    })


@socketio.on('user_message')
def handle_message(data):
    try:
        user_input = data.get('message', '').strip()
        if not user_input:
            return

        # Emit user message back for display
        emit('friday_message', {
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })

        # Try routing to automation first
        handled, result = router.try_route(user_input)

        if handled:
            if result == "__RESET__":
                result = brain.reset_conversation()

            response = result

            # Also pass through AI for a witty response alongside the data
            if len(result) > 20:
                ai_comment = brain.think(
                    user_input,
                    system_context=f"System automation result: {result[:500]}"
                )
                response = f"{result}\n\n💬 {ai_comment}"
        else:
            # Pure AI conversation
            response = brain.think(user_input)

        # Speak the response (if voice enabled)
        if voice and VOICE_ENABLED:
            # Only speak a short version
            speak_text = str(response)[:200].split('\n')[0]
            voice.speak(speak_text)

        emit('friday_message', {
            'type': 'assistant',
            'content': response,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
    except Exception as e:
        print(f"Error in handle_message: {e}")
        import traceback
        traceback.print_exc()
        emit('friday_message', {
            'type': 'system',
            'content': f'⚠️ Internal System Error: {str(e)}',
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })


@socketio.on('voice_input')
def handle_voice():
    """Handle voice input request from the web GUI."""
    if not voice or not VOICE_ENABLED:
        emit('friday_message', {
            'type': 'system',
            'content': 'Voice module is not available. Please check microphone and dependencies.',
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
        return

    emit('friday_message', {
        'type': 'system',
        'content': '🎤 Listening...',
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
    })

    def listen_async():
        text = voice.listen(timeout=7, phrase_time_limit=15)
        if text:
            socketio.emit('voice_result', {'text': text})
            # Process the voice input like a regular message
            handle_message({'message': text})
        else:
            socketio.emit('friday_message', {
                'type': 'system',
                'content': "Didn't catch that. Try again?",
                'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
            })

    threading.Thread(target=listen_async, daemon=True).start()


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[{config.ASSISTANT_NAME}] Client disconnected")


def run_web():
    """Start the web GUI server."""
    print(f"\n{'='*50}")
    print(f"  {config.ASSISTANT_NAME} Web Interface")
    print(f"  http://{config.WEB_HOST}:{config.WEB_PORT}")
    print(f"{'='*50}\n")
    socketio.run(app, host=config.WEB_HOST, port=config.WEB_PORT,
                 debug=True, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_web()
