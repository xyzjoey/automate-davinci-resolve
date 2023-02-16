import time


class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.interval = 0

    def reset(self, seconds):
        self.start_time = time.time()
        self.interval = seconds

    def expired(self):
        return (time.time() - self.start_time) >= self.interval
