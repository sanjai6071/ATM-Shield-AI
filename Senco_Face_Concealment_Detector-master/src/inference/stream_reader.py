import time
import queue
import threading
import cv2
from typing import Optional, Union, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("StreamReader")

class ResilientStreamReader:
    """Threaded video/RTSP reader with auto-reconnection and zero-latency frame dropping."""

    def __init__(self, source: Union[int, str], reconnect_interval: int = 5, 
                 buffer_size: int = 1, resolution: Optional[Tuple[int, int]] = None):
        self.source = source
        self.reconnect_interval = reconnect_interval
        self.buffer_size = buffer_size
        self.resolution = tuple(resolution) if resolution else None
        
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.running = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> "ResilientStreamReader":
        self.running = True
        self._connect()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream reader started for source: {self.source}")
        return self

    def _connect(self):
        logger.info(f"Attempting to open video source: {self.source}...")
        if isinstance(self.source, str) and self.source.isdigit():
            self.cap = cv2.VideoCapture(int(self.source))
        else:
            self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            logger.warning(f"Failed to open source {self.source}. Reconnect worker will retry.")
        else:
            logger.info(f"Successfully connected to source {self.source}")

    def _capture_loop(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(self.reconnect_interval)
                self._connect()
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Video file reached end or RTSP disconnected
                if isinstance(self.source, str) and not self.source.startswith("rtsp://") and not self.source.startswith("http"):
                    logger.info("Video playback completed.")
                    self.running = False
                    break
                logger.warning("Stream frame read failed. Reconnecting...")
                if self.cap:
                    self.cap.release()
                time.sleep(self.reconnect_interval)
                self._connect()
                continue

            if self.resolution:
                frame = cv2.resize(frame, self.resolution, interpolation=cv2.INTER_LINEAR)

            # Drop stale frame if queue is full to ensure real-time latency
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            try:
                self.frame_queue.put(frame, timeout=0.05)
            except queue.Full:
                pass

    def read(self, timeout: float = 0.5):
        """Reads latest frame from the queue."""
        try:
            return True, self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return False, None

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        logger.info("Stream reader stopped.")
