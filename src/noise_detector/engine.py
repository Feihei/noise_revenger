"""Main noise detection engine combining low and high frequency detectors."""

import numpy as np
import time
import logging
from enum import Enum
from typing import Optional

from .low_freq import LowFreqDetector
from .high_freq import HighFreqDetector

logger = logging.getLogger(__name__)


class NoiseType(Enum):
    LOW_FREQ_IMPACT = "low_freq_impact"
    HIGH_FREQ_FRICTION = "high_freq_friction"


class NoiseIntensity(Enum):
    MILD = "mild"
    MEDIUM = "medium"
    STRONG = "strong"


class NoiseEvent:
    def __init__(self, noise_type: NoiseType, intensity: NoiseIntensity,
                 confidence: float, timestamp: float):
        self.noise_type = noise_type
        self.intensity = intensity
        self.confidence = confidence
        self.timestamp = timestamp

    def __repr__(self):
        return (f"NoiseEvent(type={self.noise_type.value}, "
                f"intensity={self.intensity.value}, "
                f"confidence={self.confidence:.2f})")


class NoiseDetector:
    def __init__(self, sample_rate: int, low_freq_config: dict,
                 high_freq_config: dict, cooldown_seconds: float = 5.0):
        self.low_detector = LowFreqDetector(
            sample_rate=sample_rate,
            freq_range=tuple(low_freq_config.get("freq_range", [20, 250])),
            energy_threshold=low_freq_config.get("energy_threshold", 3.0),
            spectral_centroid_max=low_freq_config.get("spectral_centroid_max", 500.0),
        )
        self.high_detector = HighFreqDetector(
            sample_rate=sample_rate,
            freq_range=tuple(high_freq_config.get("freq_range", [2000, 8000])),
            energy_threshold=high_freq_config.get("energy_threshold", 2.5),
            zero_crossing_min=high_freq_config.get("zero_crossing_min", 0.3),
        )
        self.cooldown_seconds = cooldown_seconds
        self._last_trigger_time = 0.0
        self._low_enabled = low_freq_config.get("enabled", True)
        self._high_enabled = high_freq_config.get("enabled", True)

    def analyze(self, audio_chunk: np.ndarray) -> Optional[NoiseEvent]:
        now = time.time()
        if now - self._last_trigger_time < self.cooldown_seconds:
            return None

        event = None

        if self._low_enabled:
            low_result = self.low_detector.analyze(audio_chunk)
            if low_result["detected"]:
                intensity = self._classify_intensity(low_result["confidence"])
                event = NoiseEvent(
                    noise_type=NoiseType.LOW_FREQ_IMPACT,
                    intensity=intensity,
                    confidence=low_result["confidence"],
                    timestamp=now,
                )

        if event is None and self._high_enabled:
            high_result = self.high_detector.analyze(audio_chunk)
            if high_result["detected"]:
                intensity = self._classify_intensity(high_result["confidence"])
                event = NoiseEvent(
                    noise_type=NoiseType.HIGH_FREQ_FRICTION,
                    intensity=intensity,
                    confidence=high_result["confidence"],
                    timestamp=now,
                )

        if event is not None:
            self._last_trigger_time = now
            logger.info(f"Noise detected: {event}")

        return event

    def learn_background(self, audio_chunk: np.ndarray):
        if self._low_enabled:
            self.low_detector.update_background(audio_chunk)
        if self._high_enabled:
            self.high_detector.update_background(audio_chunk)

    @staticmethod
    def _classify_intensity(confidence: float) -> NoiseIntensity:
        if confidence < 0.4:
            return NoiseIntensity.MILD
        elif confidence < 0.7:
            return NoiseIntensity.MEDIUM
        else:
            return NoiseIntensity.STRONG
