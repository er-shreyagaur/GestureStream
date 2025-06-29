# 🎥 GestureStream - Touchless Video Controller

**GestureStream** is a smart, hands-free video player that allows users to control video playback using real-time **hand gestures**, **voice commands**, or **both simultaneously**. It is built with a Flask backend, powered by MediaPipe for gesture recognition, and uses the browser as the playback interface.

---

## 🚀 Features

- 🖐️ Real-time Gesture Control (via webcam)
- 🎤 Voice Command Support (via microphone)
- 🔄 **Hybrid Mode:** Gesture and Voice together
- 🎬 Play/Pause, Volume, Skip, and Navigation
- 🔊 Audio Feedback via Text-to-Speech
- 🌐 Web-based interface using HTML, CSS, JavaScript
- 🔄 Live Status Indicator and Command Notifications

---

## 🛠️ Tech Stack

| Layer       | Tools Used                      |
|-------------|----------------------------------|
| Frontend    | HTML, CSS, JavaScript            |
| Backend     | Python Flask, MediaPipe, PyCaw   |
| Audio Input | SpeechRecognition, Pyttsx3       |
| Styling     | Custom Dark-Themed CSS           |
| Interaction | REST APIs via Fetch/AJAX         |

---

## ⚙️ How It Works

1. User launches the interface and selects a mode:
   - **Gesture Mode**
   - **Voice Mode**
   - **Both Modes**

2. On clicking **Start Gesture Control**, the backend activates webcam and/or mic input.

3. Gesture recognition and voice processing run in parallel threads.

4. Based on the user input, playback commands are identified and sent to the frontend via API.

5. The active video responds (play, pause, volume change, skip, etc.).

---

## 🎮 Supported Commands

### 🖐️ Gesture Commands:
| Gesture                     | Action            |
|-----------------------------|-------------------|
| Thumb + Index Finger Touch  | Play / Pause      |
| Thumb Up                    | Volume Up         |
| Thumb Down                  | Volume Down       |
| Index + Middle Finger Up    | Skip Forward      |
| Only Index Finger Up        | Skip Backward     |

### 🎤 Voice Commands:
| Voice Input                 | Action            |
|-----------------------------|-------------------|
| "play" or "pause"           | Play / Pause      |
| "volume up", "increase"     | Volume Up         |
| "volume down", "decrease"   | Volume Down       |
| "skip forward", "forward"   | Skip Forward      |
| "skip backward", "back"     | Skip Backward     |

---

## 📦 Requirements

Make sure the following are installed:

- Python 3.x
- Flask
- OpenCV (`cv2`)
- MediaPipe
- PyCaw
- SpeechRecognition
- PyAudio
- pyttsx3
- Flask-CORS

Install them via:

` ```bash
pip install flask opencv-python mediapipe pycaw SpeechRecognition pyttsx3 flask-cors`

## 🌟 Future Enhancements
- On-Screen Gesture Icons/Animations – Visual indicators to show detected gestures.

- Mobile/Tablet Support – Make the UI fully responsive across devices.

- Advanced Gesture Training – Incorporate custom gesture recognition models.

- Full Voice-Driven Navigation – Use voice to browse, play, and manage videos without gestures.
