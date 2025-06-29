from flask import Flask, render_template, jsonify, request
import cv2
import mediapipe as mp
import time
import threading
import os
import platform
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pyttsx3
import speech_recognition as sr
import logging
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # Add CORS to prevent cross-origin issues

# MediaPipe Hands setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Global variables for gesture control
gesture_thread = None
voice_thread = None
cap = None
is_running = False
mode = "gesture"  # Default mode: gesture only (options: "gesture", "voice", "both")
mode_lock = threading.Lock()

# Command queue for browser communication
command_queue = []
queue_lock = threading.Lock()

# Voice recognition setup
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Text-to-speech engine
engine = pyttsx3.init()

# Track previous actions to prevent repeats
prev_action = None
last_action_time = time.time()

def speak(text):
    engine.say(text)
    try:
        engine.runAndWait()
    except RuntimeError:
        # Wait a moment and try again, or skip
        time.sleep(0.5)
        try:
            engine.runAndWait()
        except:
            pass

def adjust_volume(change):
    """Add volume command to queue"""
    with queue_lock:
        if change > 0:
            command_queue.append('volume_up')
        else:
            command_queue.append('volume_down')

def detect_gesture(landmarks):
    """Process hand landmarks to detect gestures"""
    global prev_action, last_action_time, mode

    with mode_lock:
        current_mode = mode
        
    if current_mode == "voice":
        return

    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]

    # Play/Pause (Thumb & Index Close)
    if thumb_tip.y < index_tip.y and abs(thumb_tip.x - index_tip.x) < 0.1:
        if prev_action != 'play_pause' or (time.time() - last_action_time > 1.5):
            with queue_lock:
                command_queue.append('play_pause')
            speak("Play Pause")
            prev_action = 'play_pause'
            last_action_time = time.time()
            logging.info("Gesture detected: Play/Pause")

    # Volume Up (Thumb Up)
    elif thumb_tip.y < wrist.y - 0.05:
        if prev_action != 'volume_up' or (time.time() - last_action_time > 1.5):
            adjust_volume(1)
            speak("Volume Up")
            prev_action = 'volume_up'
            last_action_time = time.time()
            logging.info("Gesture detected: Volume Up")

    # Volume Down (Thumb Down)
    elif thumb_tip.y > wrist.y + 0.05:
        if prev_action != 'volume_down' or (time.time() - last_action_time > 1.5):
            adjust_volume(-1)
            speak("Volume Down")
            prev_action = 'volume_down'
            last_action_time = time.time()
            logging.info("Gesture detected: Volume Down")

    # Skip Forward (Index + Middle Up)
    elif index_tip.y < wrist.y - 0.1 and middle_tip.y < wrist.y - 0.1:
        if prev_action != 'skip_forward' or (time.time() - last_action_time > 1.5):
            with queue_lock:
                command_queue.append('skip_forward')
            speak("Skip Forward")
            prev_action = 'skip_forward'
            last_action_time = time.time()
            logging.info("Gesture detected: Skip Forward")

    # Skip Backward (Only Index Up)
    elif index_tip.y < wrist.y - 0.1 and middle_tip.y > wrist.y:
        if prev_action != 'skip_backward' or (time.time() - last_action_time > 1.5):
            with queue_lock:
                command_queue.append('skip_backward')
            speak("Skip Backward")
            prev_action = 'skip_backward'
            last_action_time = time.time()
            logging.info("Gesture detected: Skip Backward")

def recognize_voice():
    """Voice recognition thread function"""
    global mode
    while is_running:
        with mode_lock:
            current_mode = mode
            
        # Skip if in gesture-only mode
        if current_mode == "gesture":
            time.sleep(1)
            continue
        
        logging.info(f"Voice recognition active (Mode: {current_mode})")
        
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                logging.info("Listening for voice command...")
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)
                
                try:
                    command = recognizer.recognize_google(audio).lower()
                    logging.info(f"Voice Command recognized: {command}")

                    with mode_lock:
                        if "play" in command or "pause" in command:
                            with queue_lock:
                                command_queue.append('play_pause')
                            speak("Play Pause")
                            logging.info("Voice command executed: play/pause")

                        elif "volume up" in command or "increase" in command:
                            adjust_volume(1)
                            speak("Volume Up")
                            logging.info("Voice command executed: volume up")

                        elif "volume down" in command or "decrease" in command:
                            adjust_volume(-1)
                            speak("Volume Down")
                            logging.info("Voice command executed: volume down")

                        elif "skip forward" in command or "forward" in command:
                            with queue_lock:
                                command_queue.append('skip_forward')
                            speak("Skip Forward")
                            logging.info("Voice command executed: skip forward")

                        elif "skip backward" in command or "back" in command:
                            with queue_lock:
                                command_queue.append('skip_backward')
                            speak("Skip Backward")
                            logging.info("Voice command executed: skip backward")

                        elif "gesture mode" in command:
                            mode = "gesture"
                            speak("Switched to Gesture Mode")
                            logging.info("Switched to Gesture Mode")

                        elif "voice mode" in command:
                            mode = "voice"
                            speak("Switched to Voice Mode")
                            logging.info("Switched to Voice Mode")

                        elif "both modes" in command:
                            mode = "both"
                            speak("Switched to Both Modes")
                            logging.info("Switched to Both Modes")

                        elif "exit" in command or "quit" in command:
                            speak("Exiting")
                            stop_gesture_control()
                
                except sr.UnknownValueError:
                    logging.info("Could not understand the command")
                except sr.RequestError as e:
                    logging.error(f"Speech recognition error: {e}")

        except sr.WaitTimeoutError:
            logging.info("Listening timed out")
        except Exception as e:
            logging.error(f"Voice recognition error: {e}")
            time.sleep(1)  # Prevent tight loop if there's a persistent error

def process_frames():
    """Process webcam frames for gesture detection"""
    global cap, is_running
    
    # Initialize the MediaPipe hands model
    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
        while is_running and cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    detect_gesture(hand_landmarks.landmark)

            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imshow('Gesture Control', image)

            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                speak("Exiting")
                break

    # Clean up
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

def start_gesture_control():
    """Start gesture and voice control threads"""
    global gesture_thread, voice_thread, cap, is_running, mode, prev_action, last_action_time, command_queue
    
    if is_running:
        return False
        
    is_running = True
    mode = "gesture"  # Default to gesture mode
    prev_action = None
    last_action_time = time.time()
    command_queue = []
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Start gesture processing thread
    gesture_thread = threading.Thread(target=process_frames)
    gesture_thread.daemon = True
    gesture_thread.start()
    
    # Start voice recognition thread
    voice_thread = threading.Thread(target=recognize_voice)
    voice_thread.daemon = True
    voice_thread.start()
    
    speak("Gesture control started")
    logging.info("Gesture control started")
    return True

def stop_gesture_control():
    """Stop all control threads"""
    global is_running
    
    if not is_running:
        return False
    
    is_running = False
    logging.info("Stopping gesture control...")
    
    # Wait for threads to finish
    if gesture_thread and gesture_thread.is_alive():
        gesture_thread.join(timeout=1.0)
        
    if voice_thread and voice_thread.is_alive():
        voice_thread.join(timeout=1.0)
    
    # Release webcam
    if cap is not None:
        cap.release()
    
    cv2.destroyAllWindows()
    speak("Gesture control stopped")
    logging.info("Gesture control stopped")
    return True

# Flask routes - updated to match JavaScript expectations
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gesture/start', methods=['POST'])
def start_gesture():
    result = start_gesture_control()
    return jsonify({'status': 'Gesture control started' if result else 'Already running'})

@app.route('/api/gesture/stop', methods=['POST'])
def stop_gesture():
    result = stop_gesture_control()
    return jsonify({'status': 'Gesture control stopped' if result else 'Not running'})

@app.route('/api/gesture/commands', methods=['GET'])
def get_commands():
    """Return any pending commands and clear the queue"""
    with queue_lock:
        commands = command_queue.copy()
        command_queue.clear()
    return jsonify({'commands': commands})

@app.route('/api/gesture/mode', methods=['POST'])
def set_mode():
    global mode
    new_mode = request.json.get('mode')
    
    logging.info(f"Mode change request: {new_mode}")
    
    if new_mode in ["gesture", "voice", "both"]:
        with mode_lock:
            mode = new_mode
        speak(f"Switched to {new_mode} mode")
        logging.info(f"Mode changed to {new_mode}")
        return jsonify({'status': f'Mode changed to {new_mode}'})
    else:
        logging.warning(f"Invalid mode requested: {new_mode}")
        return jsonify({'status': 'Invalid mode'})

@app.route('/api/gesture/status', methods=['GET'])
def get_status():
    """Return current system status"""
    return jsonify({
        'running': is_running,
        'mode': mode
    })

# Keep the original endpoints for backward compatibility
@app.route('/start_gesture', methods=['POST'])
def start_gesture_alt():
    return start_gesture()

@app.route('/stop_gesture', methods=['POST'])
def stop_gesture_alt():
    return stop_gesture()

@app.route('/get_commands', methods=['GET'])
def get_commands_alt():
    return get_commands()

@app.route('/set_mode', methods=['POST'])
def set_mode_alt():
    return set_mode()

@app.route('/get_status', methods=['GET'])
def get_status_alt():
    return get_status()

if __name__ == '__main__':
    app.run(debug=True)