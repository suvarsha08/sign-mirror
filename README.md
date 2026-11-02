# SIGNMIRROR 🪞✋

**AI-Powered Visual Communication System**

Real-time sign-language gesture recognition using your webcam. SIGNMIRROR detects hand gestures via MediaPipe, displays the recognised word on a futuristic Smart Mirror HUD, and speaks it aloud using text-to-speech.

---

## ✨ Features

| Feature | Description |
|---|---|
| **5 Gestures** | HELLO, YES, NO, OK, THANK YOU |
| **Real-Time Detection** | 30+ FPS with MediaPipe hand tracking |
| **Smart Mirror HUD** | Cyberpunk-styled overlay with live clock, FPS badge, gesture guide |
| **Text-to-Speech** | Non-blocking async speech with per-word cooldown |
| **Mirror Mode** | Video is flipped so the display feels like a mirror |
| **Keyboard Controls** | Mute, toggle HUD guide, swap cameras |

---

## 🖥️ Requirements

- **Python 3.9 – 3.12** (recommended: 3.11)
- A working **webcam**
- **Windows 10/11** (also works on macOS / Linux)

---

## 🚀 Installation (Windows)

### Step 1 – Install Python

If you don't have Python installed:

1. Download **Python 3.11** from [python.org/downloads](https://www.python.org/downloads/)
2. **Important**: Check ✅ *"Add Python to PATH"* during installation
3. Verify in a terminal:
   ```
   python --version
   ```

### Step 2 – Clone / Download this project

Place the `sign mirror` folder anywhere on your Desktop (or wherever you prefer).

### Step 3 – Create a virtual environment (recommended)

Open a terminal in the project folder:

```powershell
cd "C:\Users\YOUR_USERNAME\Desktop\sign mirror"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note**: If you get a PowerShell execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Step 4 – Install dependencies

```powershell
pip install -r requirements.txt
```

### Step 5 – Run the application

```powershell
python main.py
```

A window titled **SIGNMIRROR** will open showing your webcam feed with the HUD overlay.

---

## 🎮 Keyboard Controls

| Key | Action |
|-----|--------|
| `Q` | Quit the application |
| `M` | Toggle mute / unmute text-to-speech |
| `H` | Toggle the gesture guide side panel |
| `C` | Cycle to the next camera (0 → 1 → 2 → 0) |

---

## ✋ How to Perform Each Gesture

| Gesture | How to do it |
|---------|-------------|
| **HELLO** | Open palm, all 5 fingers extended **and spread wide** |
| **YES** | Closed fist with **only thumb** pointing up (thumbs-up) |
| **NO** | Closed fist with **only index finger** pointing up |
| **OK** | Thumb tip touching index tip (circle), middle/ring/pinky extended |
| **THANK YOU** | All fingers extended but **kept together** (flat palm) |

> 💡 Hold each gesture steadily for about half a second for reliable detection.

---

## 📁 Project Structure

```
sign mirror/
├── main.py                  # Application entry point & webcam loop
├── config.py                # All configuration constants
├── gesture_recognition.py   # MediaPipe hand detection & gesture classifier
├── speech.py                # Async text-to-speech engine
├── ui_mirror.py             # Smart Mirror HUD overlay renderer
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── assets/
    └── gesture_guide.txt    # Text-based gesture reference
```

---

## 🧩 Adding New Gestures

1. Open [`gesture_recognition.py`](gesture_recognition.py).
2. Add a new rule inside the `_classify_gesture()` function using the finger extension helpers (`_extended_fingers`, `_fingers_spread`, `_distance`, etc.).
3. Add the label to `GESTURE_LABELS` and `GESTURE_ICONS` in [`config.py`](config.py).
4. That's it – the HUD and speech engine will pick up the new gesture automatically.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'cv2'` | Run `pip install opencv-python` |
| `ModuleNotFoundError: No module named 'mediapipe'` | Run `pip install mediapipe` |
| Camera window is black | Try pressing `C` to swap cameras, or check webcam permissions |
| pyttsx3 error on init | Audio drivers may be missing; TTS will be disabled but detection still works |
| PowerShell blocks venv activation | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| Low FPS | Close other webcam apps; reduce `CAMERA_WIDTH`/`CAMERA_HEIGHT` in `config.py` |

---

## 🎓 College Ideathon Demo Tips

1. **Lighting** – Face a bright light source. Avoid sitting with a window behind you.
2. **Background** – A plain wall gives the cleanest landmark tracking.
3. **Webcam height** – Position camera at chest-to-face level.
4. **Practice** – Run through all 5 gestures a few times before the demo.
5. **Wow factor** – Start with the HUD visible (press `H` if hidden), show the live FPS and clock, then demonstrate each gesture one by one.
6. **Narrate** – Explain the architecture: "MediaPipe extracts 21 3D landmarks per hand, we classify with geometric heuristics, and speak via threaded TTS."

---

## 📄 License

This project is for educational / hackathon purposes.

---

*Built with ❤️ using OpenCV, MediaPipe, and pyttsx3.*
