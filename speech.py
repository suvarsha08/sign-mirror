"""
SIGNMIRROR – Asynchronous Text-to-Speech Engine
=================================================
Runs pyttsx3 on a dedicated background thread so the main
camera / UI loop is never blocked by audio playback.

Features:
  • Per-word cooldown timer prevents the same word being spoken
    repeatedly in rapid succession.
  • Thread-safe queue for word submission.
  • Graceful start / stop with no dangling threads.
  • Automatic fallback if pyttsx3 cannot initialise (e.g. no
    audio drivers on the host machine).
"""

from __future__ import annotations

import threading
import time
import queue

from config import SPEECH_COOLDOWN_SECONDS, SPEECH_RATE


class SpeechEngine:
    """Non-blocking TTS wrapper."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False
        self._muted = False

        # Cooldown bookkeeping: {word: last_spoken_timestamp}
        self._last_spoken: dict[str, float] = {}

        # Try importing pyttsx3 – it may fail on some systems
        self._engine = None
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", SPEECH_RATE)
        except Exception as exc:
            print(f"[SpeechEngine] pyttsx3 init failed ({exc}). "
                  "TTS will be disabled.")

    # ── public API ──────────────────────────────────────────────

    def start(self):
        """Spin up the background worker thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the worker to exit and wait for it to finish."""
        self._running = False
        # Push a sentinel so the blocking .get() wakes up
        self._queue.put(None)
        if self._thread is not None:
            self._thread.join(timeout=3)

    def speak(self, word: str):
        """
        Submit *word* for speaking.

        The request is silently dropped when:
          • TTS is muted
          • The engine failed to initialise
          • The same word was spoken less than COOLDOWN seconds ago
        """
        if self._muted or self._engine is None:
            return

        now = time.time()
        last = self._last_spoken.get(word, 0.0)
        if now - last < SPEECH_COOLDOWN_SECONDS:
            return  # still in cooldown

        self._last_spoken[word] = now
        self._queue.put(word)

    def toggle_mute(self) -> bool:
        """Toggle mute state. Returns the new muted flag."""
        self._muted = not self._muted
        return self._muted

    @property
    def is_muted(self) -> bool:
        return self._muted

    # ── private worker ──────────────────────────────────────────

    def _worker(self):
        """Background loop: pull words off the queue and speak them."""
        while self._running:
            try:
                word = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if word is None:        # sentinel → exit
                break

            try:
                self._engine.say(word)
                self._engine.runAndWait()
            except Exception as exc:
                print(f"[SpeechEngine] Error speaking '{word}': {exc}")
