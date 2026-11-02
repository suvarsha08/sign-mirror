"""
SIGNMIRROR – Smart Mirror HUD Overlay
=======================================
Renders a futuristic Heads-Up Display on top of the webcam feed:
  • Top header bar with title, live clock, and FPS badge.
  • Custom hand-skeleton visualisation with glowing joints.
  • Bottom recognition deck with state indicator and large gesture text.
  • Side panel cheatsheet of available gestures.
  • Keyboard shortcut hints.

All drawing is done with OpenCV primitives (rectangles, circles,
putText, lines) – no external image assets required.
"""

from __future__ import annotations

import time
from typing import List, Optional

import cv2
import numpy as np

from config import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_PURPLE,
    COLOR_BG,
    COLOR_CARD,
    COLOR_DARK_OVERLAY,
    COLOR_GRAY,
    COLOR_LANDMARK_DOT,
    COLOR_LANDMARK_LINE,
    COLOR_SUCCESS,
    COLOR_TEXT_LAVENDER,
    COLOR_TEXT_WHITE,
    COLOR_WARNING,
    FONT_SCALE_GESTURE_LARGE,
    FONT_SCALE_HUD,
    FONT_SCALE_SMALL,
    FONT_SCALE_SUBTITLE,
    FONT_SCALE_TITLE,
    FOOTER_HEIGHT,
    GESTURE_LABELS,
    HEADER_HEIGHT,
    SIDE_PANEL_WIDTH,
)

# MediaPipe hand connections (pairs of landmark indices)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle  (fixed: was 5→9)
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring    (fixed: was 9→13)
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17),             # Palm cross-connections
]

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD = cv2.FONT_HERSHEY_DUPLEX


class SmartMirrorUI:
    """Renders the HUD overlay onto each video frame."""

    def __init__(self):
        self._show_hud_guide = True
        self._fps_buffer: list[float] = []
        self._last_time = time.time()

    # ── Public API ──────────────────────────────────────────────

    def render(
        self,
        frame: np.ndarray,
        gesture: Optional[str],
        hand_landmarks_list: list,
        is_muted: bool,
    ) -> np.ndarray:
        """
        Draw the full HUD on *frame* and return the composited image.
        """
        h, w = frame.shape[:2]

        # Calculate FPS
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        fps = 1.0 / dt if dt > 0 else 0
        self._fps_buffer.append(fps)
        if len(self._fps_buffer) > 30:
            self._fps_buffer.pop(0)
        avg_fps = sum(self._fps_buffer) / len(self._fps_buffer)

        # Draw hand skeleton(s)
        for hand_lms in hand_landmarks_list:
            self._draw_hand_skeleton(frame, hand_lms, w, h)

        # Overlay panels
        self._draw_header(frame, w, avg_fps)
        self._draw_footer(frame, w, h, gesture, is_muted)

        if self._show_hud_guide:
            self._draw_side_panel(frame, w, h, gesture)

        self._draw_controls_hint(frame, w, h)

        return frame

    def toggle_hud(self) -> bool:
        self._show_hud_guide = not self._show_hud_guide
        return self._show_hud_guide

    # ── Hand skeleton ───────────────────────────────────────────

    def _draw_hand_skeleton(self, frame, hand_lms, w, h):
        """Draw coloured bones and glowing joint dots."""
        lm = hand_lms.landmark
        pts = [(int(l.x * w), int(l.y * h)) for l in lm]

        # Draw bones (connecting lines)
        for i, j in HAND_CONNECTIONS:
            cv2.line(frame, pts[i], pts[j], COLOR_LANDMARK_LINE, 2, cv2.LINE_AA)

        # Draw joints – outer glow then inner dot
        for px, py in pts:
            cv2.circle(frame, (px, py), 6, COLOR_LANDMARK_LINE, -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 4, COLOR_LANDMARK_DOT, -1, cv2.LINE_AA)

        # Fingertip extra glow
        for tip_idx in [4, 8, 12, 16, 20]:
            px, py = pts[tip_idx]
            cv2.circle(frame, (px, py), 9, (*COLOR_ACCENT_CYAN[:2], COLOR_ACCENT_CYAN[2]), 1, cv2.LINE_AA)

    # ── Header bar ──────────────────────────────────────────────

    def _draw_header(self, frame, w, fps):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, HEADER_HEIGHT), COLOR_DARK_OVERLAY, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Accent line at bottom of header
        cv2.line(frame, (0, HEADER_HEIGHT), (w, HEADER_HEIGHT), COLOR_ACCENT_CYAN, 2)

        # Title
        cv2.putText(frame, "SIGNMIRROR", (20, 35),
                    FONT_BOLD, FONT_SCALE_TITLE, COLOR_ACCENT_CYAN, 2, cv2.LINE_AA)
        cv2.putText(frame, "AI-POWERED VISUAL COMMUNICATION", (20, 58),
                    FONT, FONT_SCALE_SUBTITLE, COLOR_TEXT_LAVENDER, 1, cv2.LINE_AA)

        # Live clock
        clock_str = time.strftime("%H:%M:%S")
        clock_size = cv2.getTextSize(clock_str, FONT, FONT_SCALE_HUD, 1)[0]
        cx = w - clock_size[0] - 120
        cv2.putText(frame, clock_str, (cx, 42),
                    FONT, FONT_SCALE_HUD, COLOR_TEXT_WHITE, 1, cv2.LINE_AA)

        # FPS badge
        fps_str = f"FPS {int(fps)}"
        fps_w = cv2.getTextSize(fps_str, FONT, FONT_SCALE_SMALL, 1)[0][0]
        bx = w - fps_w - 25
        cv2.rectangle(frame, (bx - 8, 18), (bx + fps_w + 8, 48),
                      COLOR_SUCCESS if fps > 20 else COLOR_WARNING, -1)
        cv2.rectangle(frame, (bx - 8, 18), (bx + fps_w + 8, 48),
                      COLOR_TEXT_WHITE, 1)
        cv2.putText(frame, fps_str, (bx, 40),
                    FONT, FONT_SCALE_SMALL, COLOR_TEXT_WHITE, 1, cv2.LINE_AA)

    # ── Footer / recognition deck ───────────────────────────────

    def _draw_footer(self, frame, w, h, gesture, is_muted):
        fy = h - FOOTER_HEIGHT
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, fy), (w, h), COLOR_DARK_OVERLAY, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Accent line at top of footer
        cv2.line(frame, (0, fy), (w, fy), COLOR_ACCENT_CYAN, 2)

        if gesture:
            # State badge: Detected
            badge = f"DETECTED"
            cv2.putText(frame, badge, (25, fy + 30),
                        FONT, FONT_SCALE_HUD, COLOR_SUCCESS, 2, cv2.LINE_AA)

            # Large gesture text
            cv2.putText(frame, gesture, (25, fy + 80),
                        FONT_BOLD, FONT_SCALE_GESTURE_LARGE,
                        COLOR_TEXT_WHITE, 3, cv2.LINE_AA)

            # Glow underline
            gw = cv2.getTextSize(gesture, FONT_BOLD, FONT_SCALE_GESTURE_LARGE, 3)[0][0]
            cv2.line(frame, (25, fy + 88), (25 + gw, fy + 88), COLOR_ACCENT_CYAN, 2)
        else:
            # Neutral state
            cv2.putText(frame, "Show a sign to the camera...", (25, fy + 55),
                        FONT, FONT_SCALE_HUD, COLOR_GRAY, 1, cv2.LINE_AA)

        # Mute indicator (right side of footer)
        mute_label = "MUTED" if is_muted else "SPEAKER ON"
        mute_color = COLOR_WARNING if is_muted else COLOR_SUCCESS
        ml_w = cv2.getTextSize(mute_label, FONT, FONT_SCALE_SMALL, 1)[0][0]
        mx = w - ml_w - 30
        # Speaker icon (small circle + lines)
        cv2.circle(frame, (mx - 18, fy + 55), 8, mute_color, 2, cv2.LINE_AA)
        cv2.putText(frame, mute_label, (mx, fy + 60),
                    FONT, FONT_SCALE_SMALL, mute_color, 1, cv2.LINE_AA)

    # ── Side panel (gesture cheatsheet) ─────────────────────────

    def _draw_side_panel(self, frame, w, h, current_gesture):
        px = w - SIDE_PANEL_WIDTH
        py_start = HEADER_HEIGHT + 15
        panel_h = len(GESTURE_LABELS) * 42 + 60

        overlay = frame.copy()
        cv2.rectangle(overlay, (px, py_start), (w, py_start + panel_h),
                      COLOR_DARK_OVERLAY, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Border
        cv2.rectangle(frame, (px, py_start), (w, py_start + panel_h),
                      COLOR_ACCENT_PURPLE, 1)

        # Panel title
        cv2.putText(frame, "GESTURE GUIDE", (px + 15, py_start + 28),
                    FONT_BOLD, FONT_SCALE_HUD, COLOR_ACCENT_PURPLE, 1, cv2.LINE_AA)
        cv2.line(frame, (px + 15, py_start + 35), (w - 15, py_start + 35),
                 COLOR_ACCENT_PURPLE, 1)

        # List gestures
        for i, label in enumerate(GESTURE_LABELS):
            y = py_start + 60 + i * 42
            is_active = (label == current_gesture)
            dot_color = COLOR_SUCCESS if is_active else COLOR_GRAY
            text_color = COLOR_TEXT_WHITE if is_active else COLOR_TEXT_LAVENDER

            # Status dot
            cv2.circle(frame, (px + 22, y - 4), 5, dot_color, -1, cv2.LINE_AA)
            if is_active:
                cv2.circle(frame, (px + 22, y - 4), 8, dot_color, 1, cv2.LINE_AA)

            # Label
            cv2.putText(frame, label, (px + 38, y),
                        FONT, FONT_SCALE_HUD, text_color, 1, cv2.LINE_AA)

    # ── Controls hint ───────────────────────────────────────────

    def _draw_controls_hint(self, frame, w, h):
        hints = "Q:Quit  M:Mute  H:Guide  C:Camera"
        ht_w = cv2.getTextSize(hints, FONT, FONT_SCALE_SMALL, 1)[0][0]
        hx = (w - ht_w) // 2
        hy = h - 8
        cv2.putText(frame, hints, (hx, hy),
                    FONT, FONT_SCALE_SMALL, COLOR_GRAY, 1, cv2.LINE_AA)
