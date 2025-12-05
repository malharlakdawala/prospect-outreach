"""Rate limiting for external API calls."""

import time
import threading


class RateLimiter:
    def __init__(self, calls_per_minute: int = 30):
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0.0
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last_call = time.time()
