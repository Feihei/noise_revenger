"""Low frequency impact noise detector (e.g., footsteps, heavy objects dropping)."""

import numpy as np
from scipy.fft import rfft, rfftfreq
from typing import Tuple


class LowFreqDetector:
    def __init__(self, sample_rate: int, freq_range: Tuple[int, int] = (20, 250),
                 energy_threshold: float = 3.0, spectral_centroid_max: float = 500.0):
        self.sample_rate = sample_rate
        self.freq_low = freq_range[0]
        self.freq_high = freq_range[1]
        self.energy_threshold = energy_threshold
        self.spectral_centroid_max = spectral_centroid_max
        self._background_energy = 1.0

    def set_background_energy(self, energy: float):
        self._background_energy = max(energy, 1e-10)

    def analyze(self, audio_chunk: np.ndarray) -> dict:
        n = len(audio_chunk)
        if n == 0:
            return {"detected": False, "confidence": 0.0, "energy_ratio": 0.0}

        spectrum = np.abs(rfft(audio_chunk))
        freqs = rfftfreq(n, d=1.0 / self.sample_rate)

        low_mask = (freqs >= self.freq_low) & (freqs <= self.freq_high)
        low_energy = np.sum(spectrum[low_mask] ** 2)

        total_energy = np.sum(spectrum ** 2)
        energy_ratio = low_energy / (total_energy + 1e-10)

        spectral_centroid = np.sum(freqs * spectrum) / (np.sum(spectrum) + 1e-10)

        normalized_energy = low_energy / self._background_energy
        exceeds_threshold = normalized_energy > self.energy_threshold
        centroid_low = spectral_centroid < self.spectral_centroid_max
        energy_concentrated = energy_ratio > 0.15

        detected = bool(exceeds_threshold and (centroid_low or energy_ratio > 0.25))
        confidence = min(1.0, normalized_energy / (self.energy_threshold * 2))

        return {
            "detected": detected,
            "confidence": float(confidence),
            "energy_ratio": float(energy_ratio),
            "normalized_energy": float(normalized_energy),
            "spectral_centroid": float(spectral_centroid),
        }

    def update_background(self, audio_chunk: np.ndarray):
        n = len(audio_chunk)
        if n == 0:
            return
        spectrum = np.abs(rfft(audio_chunk))
        freqs = rfftfreq(n, d=1.0 / self.sample_rate)
        low_mask = (freqs >= self.freq_low) & (freqs <= self.freq_high)
        low_energy = np.sum(spectrum[low_mask] ** 2)
        alpha = 0.01
        self._background_energy = (1 - alpha) * self._background_energy + alpha * low_energy
