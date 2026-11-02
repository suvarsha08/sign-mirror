"""
SIGNMIRROR – Main Application Entry Point
===========================================
Orchestrates the webcam loop, gesture recogniser, TTS engine,
and Smart Mirror UI overlay.

Usage
-----
    python main.py

Keyboard Shortcuts
------------------
    Q  –  Quit
    M  –  Toggle mute / unmute TTS
    H  –  Toggle gesture guide panel
    C  –  Swap to the next camera index (cycles 0 → 1 → 2 → 0)
"""

import sys
import cv2

from config import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    KEY_CAMERA_SWAP,
    KEY_HUD_TOGGLE,
    KEY_MUTE_TOGGLE,
    KEY_QUIT,
)
from gesture_recognition import GestureRecognizer
from speech import SpeechEngine
from ui_mirror import SmartMirrorUI


def open_camera(index: int) -> cv2.VideoCapture:
    """Try to open a camera at *index*; fall back to index 0."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened() and index != 0:
        print(f"[SIGNMIRROR] Camera {index} unavailable, falling back to 0.")
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[SIGNMIRROR] ERROR: No camera found. Exiting.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    return cap


def main():
    print("=" * 55)
    print("  SIGNMIRROR – AI-Powered Visual Communication System")
    print("=" * 55)

    camera_idx = CAMERA_INDEX
    cap = open_camera(camera_idx)

    recognizer = GestureRecognizer()
    speech = SpeechEngine()
    ui = SmartMirrorUI()

    speech.start()
    print("[SIGNMIRROR] Running. Press Q to quit.")

    last_spoken_gesture = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[SIGNMIRROR] Lost camera feed.")
                break

            # Mirror the frame so it feels like looking in a mirror
            frame = cv2.flip(frame, 1)

            # ── Gesture recognition ─────────────────────────────
            gesture, frame, hand_landmarks = recognizer.process(frame)

            # ── Text-to-speech ──────────────────────────────────
            if gesture and gesture != last_spoken_gesture:
                speech.speak(gesture)
                last_spoken_gesture = gesture
            elif gesture is None:
                last_spoken_gesture = None

            # ── Render HUD ──────────────────────────────────────
            frame = ui.render(frame, gesture, hand_landmarks, speech.is_muted)

            cv2.imshow("SIGNMIRROR", frame)

            # ── Key handling ────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key == KEY_QUIT:
                break
            elif key == KEY_MUTE_TOGGLE:
                muted = speech.toggle_mute()
                print(f"[SIGNMIRROR] TTS {'muted' if muted else 'unmuted'}.")
            elif key == KEY_HUD_TOGGLE:
                vis = ui.toggle_hud()
                print(f"[SIGNMIRROR] Gesture guide {'shown' if vis else 'hidden'}.")
            elif key == KEY_CAMERA_SWAP:
                camera_idx = (camera_idx + 1) % 3
                cap.release()
                cap = open_camera(camera_idx)
                print(f"[SIGNMIRROR] Switched to camera {camera_idx}.")

    except KeyboardInterrupt:
        print("\n[SIGNMIRROR] Interrupted by user.")

    finally:
        print("[SIGNMIRROR] Shutting down...")
        speech.stop()
        recognizer.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[SIGNMIRROR] Goodbye!")


if __name__ == "__main__":
    main()
