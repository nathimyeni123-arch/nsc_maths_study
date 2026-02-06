"""Timer module for timed exams."""

import time
import threading
from typing import Callable, Optional


class ExamTimer:
    """Timer for mock exams with callback support."""

    def __init__(self, duration_minutes: int, warning_callback: Optional[Callable] = None):
        """
        Initialize the timer.

        Args:
            duration_minutes: Total exam duration in minutes
            warning_callback: Optional callback for time warnings
        """
        self.duration_seconds = duration_minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.warning_callback = warning_callback
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._warnings_given = set()

    def start(self):
        """Start the timer."""
        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

    def pause(self):
        """Pause the timer."""
        self._paused = True

    def resume(self):
        """Resume the timer."""
        self._paused = False

    def stop(self):
        """Stop the timer."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _countdown(self):
        """Internal countdown method."""
        last_tick = time.time()

        while self._running and self.remaining_seconds > 0:
            if not self._paused:
                current_time = time.time()
                elapsed = current_time - last_tick

                if elapsed >= 1:
                    self.remaining_seconds -= int(elapsed)
                    last_tick = current_time

                    # Check for warning times
                    self._check_warnings()

            time.sleep(0.1)  # Small sleep to prevent busy waiting

    def _check_warnings(self):
        """Check and trigger time warnings."""
        if not self.warning_callback:
            return

        warning_times = [
            (30 * 60, "30 minutes remaining"),
            (15 * 60, "15 minutes remaining"),
            (5 * 60, "5 minutes remaining - please start finishing up"),
            (1 * 60, "1 minute remaining!"),
        ]

        for seconds, message in warning_times:
            if self.remaining_seconds <= seconds and seconds not in self._warnings_given:
                self._warnings_given.add(seconds)
                self.warning_callback(message, self.remaining_seconds)

    @property
    def is_expired(self) -> bool:
        """Check if time has expired."""
        return self.remaining_seconds <= 0

    @property
    def is_running(self) -> bool:
        """Check if timer is running."""
        return self._running and not self._paused

    def get_remaining(self) -> int:
        """Get remaining seconds."""
        return max(0, self.remaining_seconds)

    def get_elapsed(self) -> int:
        """Get elapsed seconds."""
        return self.duration_seconds - self.remaining_seconds

    def format_remaining(self) -> str:
        """Format remaining time as string."""
        seconds = self.get_remaining()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def get_progress(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.duration_seconds == 0:
            return 100
        elapsed = self.duration_seconds - self.remaining_seconds
        return (elapsed / self.duration_seconds) * 100


class SimpleTimer:
    """Simple non-threaded timer for tracking elapsed time."""

    def __init__(self):
        """Initialize the timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        self.end_time = None

    def stop(self):
        """Stop the timer."""
        self.end_time = time.time()

    def get_elapsed_seconds(self) -> int:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0

        end = self.end_time or time.time()
        return int(end - self.start_time)

    def get_elapsed_minutes(self) -> int:
        """Get elapsed time in minutes."""
        return self.get_elapsed_seconds() // 60

    def format_elapsed(self) -> str:
        """Format elapsed time as string."""
        seconds = self.get_elapsed_seconds()
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
