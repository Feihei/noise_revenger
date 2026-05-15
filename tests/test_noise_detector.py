"""Tests for noise detection modules."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.noise_detector.low_freq import LowFreqDetector
from src.noise_detector.high_freq import HighFreqDetector
from src.noise_detector.engine import NoiseDetector, NoiseEvent, NoiseType, NoiseIntensity


SAMPLE_RATE = 44100


def generate_low_freq_impact(duration=0.1, frequency=80, amplitude=0.8):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    signal = amplitude * np.sin(2 * np.pi * frequency * t)
    signal *= np.exp(-t * 20)
    return signal.astype(np.float32)


def generate_high_freq_friction(duration=0.1, frequency=4000, amplitude=0.6):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    signal = amplitude * np.sin(2 * np.pi * frequency * t)
    noise = 0.1 * np.random.randn(len(t)).astype(np.float32)
    return (signal + noise).astype(np.float32)


def generate_silent_chunk(duration=0.1, amplitude=0.0001):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    return (amplitude * np.random.randn(len(t))).astype(np.float32)


class TestLowFreqDetector:
    def test_detects_low_freq_impact(self):
        detector = LowFreqDetector(
            sample_rate=SAMPLE_RATE,
            freq_range=(20, 250),
            energy_threshold=1.5,
            spectral_centroid_max=500.0,
        )
        detector.set_background_energy(0.01)
        audio = generate_low_freq_impact(amplitude=0.9)
        result = detector.analyze(audio)
        assert result["detected"] is True
        assert result["confidence"] > 0.0

    def test_does_not_detect_silent(self):
        detector = LowFreqDetector(sample_rate=SAMPLE_RATE)
        detector.set_background_energy(1.0)
        audio = generate_silent_chunk()
        result = detector.analyze(audio)
        assert result["detected"] is False

    def test_empty_chunk(self):
        detector = LowFreqDetector(sample_rate=SAMPLE_RATE)
        result = detector.analyze(np.array([], dtype=np.float32))
        assert result["detected"] is False
        assert result["confidence"] == 0.0

    def test_update_background(self):
        detector = LowFreqDetector(sample_rate=SAMPLE_RATE)
        initial_energy = detector._background_energy
        audio = generate_silent_chunk(amplitude=0.5)
        detector.update_background(audio)
        assert detector._background_energy != initial_energy

    def test_spectral_centroid_calculation(self):
        detector = LowFreqDetector(sample_rate=SAMPLE_RATE)
        detector.set_background_energy(0.01)
        audio = generate_low_freq_impact(frequency=60, amplitude=0.9)
        result = detector.analyze(audio)
        assert "spectral_centroid" in result
        assert result["spectral_centroid"] < 500.0


class TestHighFreqDetector:
    def test_detects_high_freq_friction(self):
        detector = HighFreqDetector(
            sample_rate=SAMPLE_RATE,
            freq_range=(2000, 8000),
            energy_threshold=1.5,
            zero_crossing_min=0.1,
        )
        detector.set_background_energy(0.01)
        audio = generate_high_freq_friction(frequency=4000, amplitude=0.8)
        result = detector.analyze(audio)
        assert result["detected"] is True
        assert result["confidence"] > 0.0

    def test_does_not_detect_silent(self):
        detector = HighFreqDetector(sample_rate=SAMPLE_RATE)
        silent = generate_silent_chunk()
        for _ in range(10):
            detector.update_background(generate_silent_chunk())
        result = detector.analyze(silent)
        assert result["detected"] is False

    def test_empty_chunk(self):
        detector = HighFreqDetector(sample_rate=SAMPLE_RATE)
        result = detector.analyze(np.array([], dtype=np.float32))
        assert result["detected"] is False

    def test_zero_crossing_rate(self):
        rate = HighFreqDetector._compute_zero_crossing_rate(
            np.array([1.0, -1.0, 1.0, -1.0], dtype=np.float32)
        )
        assert rate == 1.0

    def test_update_background(self):
        detector = HighFreqDetector(sample_rate=SAMPLE_RATE)
        initial_energy = detector._background_energy
        audio = generate_high_freq_friction(amplitude=0.3)
        detector.update_background(audio)
        assert detector._background_energy != initial_energy


class TestNoiseDetectorEngine:
    def test_detects_low_freq_event(self):
        detector = NoiseDetector(
            sample_rate=SAMPLE_RATE,
            low_freq_config={"enabled": True, "freq_range": [20, 250],
                           "energy_threshold": 1.5, "spectral_centroid_max": 500.0},
            high_freq_config={"enabled": False},
            cooldown_seconds=0.0,
        )
        detector.low_detector.set_background_energy(0.01)
        audio = generate_low_freq_impact(amplitude=0.9)
        event = detector.analyze(audio)
        assert event is not None
        assert event.noise_type == NoiseType.LOW_FREQ_IMPACT

    def test_detects_high_freq_event(self):
        detector = NoiseDetector(
            sample_rate=SAMPLE_RATE,
            low_freq_config={"enabled": False},
            high_freq_config={"enabled": True, "freq_range": [2000, 8000],
                            "energy_threshold": 1.5, "zero_crossing_min": 0.1},
            cooldown_seconds=0.0,
        )
        detector.high_detector.set_background_energy(0.01)
        audio = generate_high_freq_friction(amplitude=0.8)
        event = detector.analyze(audio)
        assert event is not None
        assert event.noise_type == NoiseType.HIGH_FREQ_FRICTION

    def test_cooldown_prevents_rapid_triggers(self):
        detector = NoiseDetector(
            sample_rate=SAMPLE_RATE,
            low_freq_config={"enabled": True, "freq_range": [20, 250],
                           "energy_threshold": 1.5, "spectral_centroid_max": 500.0},
            high_freq_config={"enabled": False},
            cooldown_seconds=10.0,
        )
        detector.low_detector.set_background_energy(0.01)
        audio = generate_low_freq_impact(amplitude=0.9)
        event1 = detector.analyze(audio)
        event2 = detector.analyze(audio)
        assert event1 is not None
        assert event2 is None

    def test_no_event_for_silent_audio(self):
        detector = NoiseDetector(
            sample_rate=SAMPLE_RATE,
            low_freq_config={"enabled": True, "freq_range": [20, 250],
                           "energy_threshold": 3.0, "spectral_centroid_max": 500.0},
            high_freq_config={"enabled": True, "freq_range": [2000, 8000],
                            "energy_threshold": 2.5, "zero_crossing_min": 0.3},
            cooldown_seconds=0.0,
        )
        for _ in range(10):
            detector.learn_background(generate_silent_chunk())
        audio = generate_silent_chunk()
        event = detector.analyze(audio)
        assert event is None

    def test_intensity_classification(self):
        assert NoiseDetector._classify_intensity(0.2) == NoiseIntensity.MILD
        assert NoiseDetector._classify_intensity(0.5) == NoiseIntensity.MEDIUM
        assert NoiseDetector._classify_intensity(0.8) == NoiseIntensity.STRONG

    def test_learn_background(self):
        detector = NoiseDetector(
            sample_rate=SAMPLE_RATE,
            low_freq_config={"enabled": True, "freq_range": [20, 250],
                           "energy_threshold": 3.0, "spectral_centroid_max": 500.0},
            high_freq_config={"enabled": True, "freq_range": [2000, 8000],
                            "energy_threshold": 2.5, "zero_crossing_min": 0.3},
        )
        audio = generate_silent_chunk(amplitude=0.3)
        detector.learn_background(audio)
        assert detector.low_detector._background_energy != 1.0


class TestNoiseEvent:
    def test_event_repr(self):
        event = NoiseEvent(
            noise_type=NoiseType.LOW_FREQ_IMPACT,
            intensity=NoiseIntensity.MEDIUM,
            confidence=0.75,
            timestamp=1000000.0,
        )
        repr_str = repr(event)
        assert "low_freq_impact" in repr_str
        assert "medium" in repr_str
