"""Tests for configuration management module."""

import pytest
import yaml
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    AppConfig, DetectionConfig, LowFreqConfig, HighFreqConfig,
    FeedbackConfig, FeedbackSounds, LoggingConfig,
    load_config, save_config, _dict_to_config, _config_to_dict
)


class TestDefaultConfig:
    def test_default_app_config(self):
        config = AppConfig()
        assert config.sample_rate == 44100
        assert config.chunk_size == 1024
        assert config.channels == 1
        assert config.input_device_index is None

    def test_default_detection_config(self):
        config = AppConfig()
        assert config.detection.low_freq.enabled is True
        assert config.detection.low_freq.freq_range == [20, 250]
        assert config.detection.low_freq.energy_threshold == 3.0
        assert config.detection.high_freq.freq_range == [2000, 8000]
        assert config.detection.cooldown_seconds == 5.0

    def test_default_feedback_config(self):
        config = AppConfig()
        assert config.feedback.enabled is True
        assert config.feedback.volume == 1.0
        assert config.feedback.sounds.mild == "sounds/alert_mild.wav"

    def test_default_logging_config(self):
        config = AppConfig()
        assert config.logging.level == "INFO"
        assert config.logging.save_audio_clips is False


class TestConfigSerialization:
    def test_config_to_dict(self):
        config = AppConfig()
        data = _config_to_dict(config)
        assert "audio" in data
        assert "detection" in data
        assert "feedback" in data
        assert "logging" in data
        assert data["audio"]["sample_rate"] == 44100

    def test_dict_to_config_roundtrip(self):
        config = AppConfig()
        data = _config_to_dict(config)
        restored = _dict_to_config(data)
        assert restored.sample_rate == config.sample_rate
        assert restored.detection.cooldown_seconds == config.detection.cooldown_seconds
        assert restored.feedback.volume == config.feedback.volume

    def test_dict_to_config_with_custom_values(self):
        data = {
            "audio": {"sample_rate": 48000, "chunk_size": 2048, "channels": 2},
            "detection": {
                "low_freq": {"energy_threshold": 5.0},
                "high_freq": {"energy_threshold": 4.0},
                "cooldown_seconds": 10.0,
            },
            "feedback": {"volume": 0.8},
            "logging": {"level": "DEBUG"},
        }
        config = _dict_to_config(data)
        assert config.sample_rate == 48000
        assert config.chunk_size == 2048
        assert config.detection.low_freq.energy_threshold == 5.0
        assert config.detection.cooldown_seconds == 10.0
        assert config.feedback.volume == 0.8
        assert config.logging.level == "DEBUG"


class TestConfigFileIO:
    def test_save_and_load_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)

        original = AppConfig()
        original.sample_rate = 48000
        original.detection.cooldown_seconds = 15.0
        save_config(original, config_path)

        loaded = load_config(config_path)
        assert loaded.sample_rate == 48000
        assert loaded.detection.cooldown_seconds == 15.0

        config_path.unlink()

    def test_load_nonexistent_config_returns_default(self):
        config = load_config(Path("nonexistent_path.yaml"))
        assert isinstance(config, AppConfig)
        assert config.sample_rate == 44100

    def test_save_config_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "config.yaml"
            save_config(AppConfig(), config_path)
            assert config_path.exists()

    def test_load_default_settings_yaml(self):
        config = load_config(Path("config/settings.yaml"))
        assert isinstance(config, AppConfig)
        assert config.sample_rate == 44100
        assert config.detection.low_freq.enabled is True
