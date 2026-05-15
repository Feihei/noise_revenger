"""Audio capture module for real-time microphone input."""

import numpy as np
import sounddevice as sd
import queue
import threading
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class AudioCapture:
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024,
                 channels: int = 1, device_index: Optional[int] = None):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        self._audio_queue: queue.Queue = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._running = False
        self._lock = threading.Lock()

    @staticmethod
    def list_devices() -> list:
        return sd.query_devices()

    @staticmethod
    def get_default_input_device() -> dict:
        return sd.query_devices(kind='input')

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio stream status: {status}")
        self._audio_queue.put(indata.copy())

    def start(self):
        with self._lock:
            if self._running:
                return
            self._stream = sd.InputStream(
                device=self.device_index,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self._audio_callback,
                dtype=np.float32,
            )
            self._stream.start()
            self._running = True
            logger.info(f"Audio capture started: sr={self.sample_rate}, chunk={self.chunk_size}")

    def stop(self):
        with self._lock:
            if not self._running:
                return
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            self._running = False
            logger.info("Audio capture stopped")

    def read_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def read_chunk_blocking(self) -> np.ndarray:
        return self._audio_queue.get()

    @property
    def is_running(self) -> bool:
        return self._running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
