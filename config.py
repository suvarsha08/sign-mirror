"""
SIGNMIRROR – Configuration Settings
====================================
Central place for every tunable constant: colours, detection thresholds,
speech cooldowns, UI layout values, and gesture labels.
"""

# ──────────────────────────── Camera ────────────────────────────
CAMERA_INDEX = 0                # Default webcam index (0 = built-in)
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# ──────────────────────────── MediaPipe ─────────────────────────
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6

# ──────────────────────────── Gesture Logic ─────────────────────
# Number of consecutive identical frames needed before a gesture
# is accepted (eliminates single-frame noise).
STABILITY_FRAMES = 5

# ──────────────────────────── Speech ────────────────────────────
SPEECH_COOLDOWN_SECONDS = 2.5   # Minimum gap between TTS triggers
SPEECH_RATE = 160               # Words-per-minute for pyttsx3

# ──────────────────────────── Colour Palette (BGR for OpenCV) ───
# NOTE: OpenCV uses BGR order, NOT RGB.
COLOR_BG           = (26, 15, 15)       # Obsidian Navy
COLOR_CARD         = (75, 27, 30)       # Deep Royal Slate
COLOR_ACCENT_CYAN  = (212, 182, 6)     # Electric Cyan
COLOR_ACCENT_PURPLE = (246, 92, 139)   # Vivid Purple
COLOR_SUCCESS      = (129, 185, 16)    # Emerald Green
COLOR_WARNING      = (0, 191, 255)     # Amber / Gold
COLOR_TEXT_WHITE    = (255, 255, 255)   # Crisp White
COLOR_TEXT_LAVENDER = (253, 181, 196)  # Lavender
COLOR_GRAY         = (160, 160, 160)   # Neutral Gray
COLOR_DARK_OVERLAY  = (40, 35, 50)     # Semi-transparent panel fill

# Hand skeleton drawing colours
COLOR_LANDMARK_DOT  = (212, 182, 6)    # Cyan dots on joints
COLOR_LANDMARK_LINE = (246, 92, 139)   # Purple connecting bones

# ──────────────────────────── UI Layout ─────────────────────────
HEADER_HEIGHT = 70
FOOTER_HEIGHT = 110
SIDE_PANEL_WIDTH = 280

# Font scales (OpenCV putText uses float scale factors)
FONT_SCALE_TITLE = 0.85
FONT_SCALE_SUBTITLE = 0.5
FONT_SCALE_GESTURE_LARGE = 1.8
FONT_SCALE_SMALL = 0.45
FONT_SCALE_HUD = 0.55

# ──────────────────────────── Gesture Labels ────────────────────
GESTURE_LABELS = ["HELLO", "YES", "NO", "OK", "THANK YOU"]

# Emoji-style indicators shown beside each gesture in the HUD
GESTURE_ICONS = {
    "HELLO":     "👋",
    "YES":       "👍",
    "NO":        "✋",
    "OK":        "👌",
    "THANK YOU": "🙏",
}

# ──────────────────────────── Key Bindings ──────────────────────
KEY_QUIT        = ord('q')
KEY_MUTE_TOGGLE = ord('m')
KEY_HUD_TOGGLE  = ord('h')
KEY_CAMERA_SWAP = ord('c')
