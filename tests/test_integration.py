"""Integration tests for the complete noise feedback pipeline."""

import pytest
import numpy as np
import tempfile
import json
import csv
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig, _dict_to_config
from src.noise_detector.engine import NoiseDetector, NoiseType, NoiseIntensity
from src.logger import EventLogger


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


class TestConfigToDetectorIntegration:
    def test_config_creates_working_detector(self):
        config = AppConfig()
        config.detection.cooldown_seconds = 0.0

        detector = NoiseDetector(
            sample_rate=config.sample_rate,
            low_freq_config={
                "enabled": config.detection.low_freq.enabled,
                "freq_range": config.detection.low_freq.freq_range,
                "energy_threshold": config.detection.low_freq.energy_threshold,
                "spectral_centroid_max": config.detection.low_freq.spectral_centroid_max,
            },
            high_freq_config={
                "enabled": config.detection.high_freq.enabled,
                "freq_range": config.detection.high_freq.freq_range,
                "energy_threshold": config.detection.high_freq.energy_threshold,
                "zero_crossing_min": config.detection.high_freq.zero_crossing_min,
            },
            cooldown_seconds=config.detection.cooldown_seconds,
        )

        detector.low_detector.set_background_energy(0.01)
        audio = generate_low_freq_impact(amplitude=0.9)
        event = detector.analyze(audio)
        assert event is not None
        assert event.noise_type == NoiseType.LOW_FREQ_IMPACT


class TestDetectorToLoggerIntegration:
    def test_detected_event_logged_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = NoiseDetector(
                sample_rate=SAMPLE_RATE,
                low_freq_config={"enabled": True, "freq_range": [20, 250],
                               "energy_threshold": 1.5, "spectral_centroid_max": 500.0},
                high_freq_config={"enabled": False},
                cooldown_seconds=0.0,
            )
            detector.low_detector.set_background_energy(0.01)

            event_logger = EventLogger(log_dir=tmpdir)

            audio = generate_low_freq_impact(amplitude=0.9)
            event = detector.analyze(audio)

            assert event is not None
            event_logger.log_event(event)

            events = event_logger.get_today_events()
            assert len(events) == 1
            assert events[0]["noise_type"] == "low_freq_impact"


class TestFullPipeline:
    def test_low_freq_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_data = {
                "audio": {"sample_rate": SAMPLE_RATE, "chunk_size": 1024},
                "detection": {
                    "low_freq": {"enabled": True, "freq_range": [20, 250],
                               "energy_threshold": 1.5, "spectral_centroid_max": 500.0},
                    "high_freq": {"enabled": False},
                    "cooldown_seconds": 0.0,
                    "background_learning_seconds": 0.0,
                },
                "feedback": {"enabled": False},
                "logging": {"level": "INFO"},
            }
            config = _dict_to_config(config_data)
            event_logger = EventLogger(log_dir=tmpdir)

            detector = NoiseDetector(
                sample_rate=config.sample_rate,
                low_freq_config={
                    "enabled": config.detection.low_freq.enabled,
                    "freq_range": config.detection.low_freq.freq_range,
                    "energy_threshold": config.detection.low_freq.energy_threshold,
                    "spectral_centroid_max": config.detection.low_freq.spectral_centroid_max,
                },
                high_freq_config={
                    "enabled": config.detection.high_freq.enabled,
                    "freq_range": config.detection.high_freq.freq_range,
                    "energy_threshold": config.detection.high_freq.energy_threshold,
                    "zero_crossing_min": config.detection.high_freq.zero_crossing_min,
                },
                cooldown_seconds=config.detection.cooldown_seconds,
            )

            for _ in range(5):
                detector.learn_background(generate_silent_chunk(amplitude=0.01))

            loud_impact = generate_low_freq_impact(amplitude=0.9)
            event = detector.analyze(loud_impact)
            assert event is not None
            event_logger.log_event(event)

            silent = generate_silent_chunk()
            silent_event = detector.analyze(silent)
            assert silent_event is None

            stats = event_logger.get_stats()
            assert stats["total"] == 1

    def test_high_freq_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = NoiseDetector(
                sample_rate=SAMPLE_RATE,
                low_freq_config={"enabled": False},
                high_freq_config={"enabled": True, "freq_range": [2000, 8000],
                                "energy_threshold": 1.5, "zero_crossing_min": 0.1},
                cooldown_seconds=0.0,
            )
            detector.high_detector.set_background_energy(0.01)
            event_logger = EventLogger(log_dir=tmpdir)

            friction = generate_high_freq_friction(amplitude=0.8)
            event = detector.analyze(friction)
            assert event is not None
            assert event.noise_type == NoiseType.HIGH_FREQ_FRICTION
            event_logger.log_event(event)

            stats = event_logger.get_stats()
            assert stats["high_freq_friction"] == 1

    def test_cooldown_across_pipeline(self):
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
        event3 = detector.analyze(audio)

        assert event1 is not None
        assert event2 is None
        assert event3 is None

    def test_intensity_propagation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = NoiseDetector(
                sample_rate=SAMPLE_RATE,
                low_freq_config={"enabled": True, "freq_range": [20, 250],
                               "energy_threshold": 1.5, "spectral_centroid_max": 500.0},
                high_freq_config={"enabled": False},
                cooldown_seconds=0.0,
            )
            detector.low_detector.set_background_energy(0.01)
            event_logger = EventLogger(log_dir=tmpdir)

            audio = generate_low_freq_impact(amplitude=0.9)
            event = detector.analyze(audio)
            assert event is not None
            event_logger.log_event(event)

            events = event_logger.get_today_events()
            assert events[0]["intensity"] in ["mild", "medium", "strong"]
