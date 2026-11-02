"""
SIGNMIRROR – Gesture Recognition Engine
=========================================
Uses MediaPipe Hands to extract 21 3-D landmarks per hand, then
applies geometric heuristics to classify the hand pose into one of
the supported sign-language gestures.

Supported gestures
------------------
  HELLO      – All five fingers extended, palm open and facing camera.
  YES        – Thumbs-up (fist with thumb pointing upward).
  NO         – Index finger extended and wagging; other fingers closed.
  OK         – Thumb-tip touching index-tip ring; middle/ring/pinky extended.
  THANK YOU  – Flat open palm, fingers together (not spread).

A rolling stability buffer ensures that a gesture is only reported
after it has been detected consistently for STABILITY_FRAMES consecutive
frames, eliminating noisy single-frame false positives.
"""

from __future__ import annotations

import math
from collections import deque
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

from config import (
    MAX_NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    STABILITY_FRAMES,
)

# ── MediaPipe shorthand ────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


# ── Helper math ─────────────────────────────────────────────────

def _distance(a, b) -> float:
    """Euclidean distance between two landmarks (x, y, z)."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def _angle_between(a, b, c) -> float:
    """
    Angle (in degrees) at point *b* formed by segments ba and bc.
    Each argument is a MediaPipe landmark with .x, .y, .z attributes.
    """
    ba = np.array([a.x - b.x, a.y - b.y, a.z - b.z])
    bc = np.array([c.x - b.x, c.y - b.y, c.z - b.z])
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return math.degrees(math.acos(cos_angle))


# ── Finger-state helpers ────────────────────────────────────────

# MediaPipe hand landmark indices
# Thumb:  1-CMC, 2-MCP, 3-IP, 4-TIP
# Index:  5-MCP, 6-PIP, 7-DIP, 8-TIP
# Middle: 9-MCP, 10-PIP, 11-DIP, 12-TIP
# Ring:   13-MCP, 14-PIP, 15-DIP, 16-TIP
# Pinky:  17-MCP, 18-PIP, 19-DIP, 20-TIP

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]  # proximal joints (or IP for thumb)
FINGER_MCPS = [2, 5, 9, 13, 17]


def _is_finger_extended(landmarks, finger_idx: int) -> bool:
    """
    Return True if the given finger is extended (straightened out).

    For the thumb (finger_idx == 0) we use a lateral distance test
    instead of a vertical tip-vs-pip test, because the thumb's axis
    differs from the other four fingers.

    For fingers 1-4 we check whether the tip is farther from the
    wrist (landmark 0) than the PIP joint – a reliable proxy for
    "extended" in a wide range of hand orientations.
    """
    lm = landmarks

    if finger_idx == 0:  # Thumb
        # Thumb is "extended" when its tip is far from the index MCP
        return _distance(lm[4], lm[5]) > _distance(lm[3], lm[5]) * 1.1
    else:
        tip = FINGER_TIPS[finger_idx]
        pip = FINGER_PIPS[finger_idx]
        mcp = FINGER_MCPS[finger_idx]
        # Tip should be farther from the MCP along the finger's
        # natural axis.  We compare tip-to-wrist vs pip-to-wrist as
        # a robust orientation-agnostic check.
        wrist = lm[0]
        return _distance(lm[tip], wrist) > _distance(lm[pip], wrist)


def _extended_fingers(landmarks) -> List[bool]:
    """Return a 5-element list [thumb, index, middle, ring, pinky]."""
    return [_is_finger_extended(landmarks, i) for i in range(5)]


def _fingers_spread(landmarks) -> bool:
    """True when adjacent finger tips are reasonably far apart."""
    tips = [landmarks[i] for i in FINGER_TIPS[1:]]  # index … pinky
    dists = [_distance(tips[i], tips[i + 1]) for i in range(len(tips) - 1)]
    avg_spread = sum(dists) / len(dists)
    # Compare to palm size (wrist → middle-MCP)
    palm_size = _distance(landmarks[0], landmarks[9])
    return avg_spread > palm_size * 0.25


def _fingers_together(landmarks) -> bool:
    """True when adjacent finger tips are close together (not spread)."""
    tips = [landmarks[i] for i in FINGER_TIPS[1:]]
    dists = [_distance(tips[i], tips[i + 1]) for i in range(len(tips) - 1)]
    avg_spread = sum(dists) / len(dists)
    palm_size = _distance(landmarks[0], landmarks[9])
    return avg_spread < palm_size * 0.35


# ── Gesture classification ──────────────────────────────────────

def _classify_gesture(landmarks) -> Optional[str]:
    """
    Classify a single hand's landmarks into a gesture label.
    Returns None if no known gesture is detected.
    """
    ext = _extended_fingers(landmarks)
    thumb, index, middle, ring, pinky = ext
    num_extended = sum(ext)

    # ── OK: thumb tip touches index tip; middle, ring, pinky extended ──
    thumb_index_dist = _distance(landmarks[4], landmarks[8])
    palm_size = _distance(landmarks[0], landmarks[9])
    if thumb_index_dist < palm_size * 0.25 and middle and ring and pinky:
        return "OK"

    # ── YES: thumbs-up – only thumb extended, fist otherwise ──
    if thumb and not index and not middle and not ring and not pinky:
        return "YES"

    # ── NO: only index finger extended ──
    if not thumb and index and not middle and not ring and not pinky:
        return "NO"

    # ── HELLO: all fingers extended AND spread ──
    if num_extended == 5 and _fingers_spread(landmarks):
        return "HELLO"

    # ── THANK YOU: all fingers extended AND together (flat palm) ──
    if num_extended >= 4 and _fingers_together(landmarks):
        return "THANK YOU"

    return None


# ── Public recogniser class ─────────────────────────────────────

class GestureRecognizer:
    """
    High-level API consumed by main.py.

    Usage
    -----
        recognizer = GestureRecognizer()
        while True:
            frame = camera.read()
            gesture, annotated, hand_landmarks = recognizer.process(frame)
    """

    def __init__(self):
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_NUM_HANDS,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        # Rolling stability buffer
        self._buffer: deque = deque(maxlen=STABILITY_FRAMES)
        self._stable_gesture: Optional[str] = None

    # ── core processing ─────────────────────────────────────────

    def process(
        self, frame: np.ndarray
    ) -> Tuple[Optional[str], np.ndarray, list]:
        """
        Process a single BGR video frame.

        Returns
        -------
        gesture : str | None
            The stable gesture name, or None.
        annotated : np.ndarray
            The frame (unchanged – drawing is done by ui_mirror).
        all_hand_landmarks : list
            List of mediapipe NormalizedLandmarkList objects (one per hand).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)

        all_hand_landmarks: list = []
        raw_gesture: Optional[str] = None

        if results.multi_hand_landmarks:
            all_hand_landmarks = results.multi_hand_landmarks
            # Classify the first detected hand
            lm = results.multi_hand_landmarks[0].landmark
            raw_gesture = _classify_gesture(lm)

        # ── temporal smoothing ──────────────────────────────────
        self._buffer.append(raw_gesture)

        if len(self._buffer) == STABILITY_FRAMES and len(set(self._buffer)) == 1:
            self._stable_gesture = self._buffer[0]
        elif raw_gesture is None:
            # If no gesture is seen at all, clear stable after full buffer of None
            if all(g is None for g in self._buffer):
                self._stable_gesture = None

        return self._stable_gesture, frame, all_hand_landmarks

    # ── cleanup ─────────────────────────────────────────────────

    def close(self):
        self._hands.close()
