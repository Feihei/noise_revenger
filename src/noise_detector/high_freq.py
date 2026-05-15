"""High frequency friction noise detector (e.g., chair dragging, furniture scraping)."""

import numpy as np
from scipy.fft import rfft, rfftfreq
from typing import Tuple


class HighFreqDetector:
    def __init__(self, sample_rate: int, freq_range: Tuple[int, int] = (2000, 8000),
                 energy_threshold: float = 2.5, zero_crossing_min: float = 0.3):
        self.sample_rate = sample_rate
        self.freq_low = freq_range[0]
        self.freq_high = freq_range[1]
        self.energy_threshold = energy_threshold
        self.zero_crossing_min = zero_crossing_min
        self._background_energy = 1.0

    def set_background_energy(self, energy: float):
        self._background_energy = max(energy, 1e-10)

    @staticmethod
    def _compute_zero_crossing_rate(audio: np.ndarray) -> float:
        if len(audio) < 2:
            return 0.0
        zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio))))
        return zero_crossings / (len(audio) - 1)

    def analyze(self, audio_chunk: np.ndarray) -> dict:
        n = len(audio_chunk)
        if n == 0:
            return {"detected": False, "confidence": 0.0, "energy_ratio": 0.0}

        spectrum = np.abs(rfft(audio_chunk))
        freqs = rfftfreq(n, d=1.0 / self.sample_rate)

        high_mask = (freqs >= self.freq_low) & (freqs <= self.freq_high)
        high_energy = np.sum(spectrum[high_mask] ** 2)

        total_energy = np.sum(spectrum ** 2)
        energy_ratio = high_energy / (total_energy + 1e-10)

        zero_crossing_rate = self._compute_zero_crossing_rate(audio_chunk)

        normalized_energy = high_energy / self._background_energy
        exceeds_threshold = normalized_energy > self.energy_threshold
        zcr_high = zero_crossing_rate > self.zero_crossing_min
        energy_concentrated = energy_ratio > 0.1

        detected = bool(exceeds_threshold and (zcr_high or energy_ratio > 0.2))
        confidence = min(1.0, normalized_energy / (self.energy_threshold * 2))

        return {
            "detected": detected,
            "confidence": float(confidence),
            "energy_ratio": float(energy_ratio),
            "normalized_energy": float(normalized_energy),
            "zero_crossing_rate": float(zero_crossing_rate),
        }

    def update_background(self, audio_chunk: np.ndarray):
        n = len(audio_chunk)
        if n == 0:
            return
        spectrum = np.abs(rfft(audio_chunk))
        freqs = rfftfreq(n, d=1.0 / self.sample_rate)
        high_mask = (freqs >= self.freq_low) & (freqs <= self.freq_high)
        high_energy = np.sum(spectrum[high_mask] ** 2)
        alpha = 0.01
        self._background_energy = (1 - alpha) * self._background_energy + alpha * high_energy
