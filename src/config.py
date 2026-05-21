"""Configuration management module for Noise Revenger."""

import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

from .paths import get_config_path


@dataclass
class LowFreqConfig:
    enabled: bool = True
    freq_range: list = field(default_factory=lambda: [20, 250])
    energy_threshold: float = 3.0
    spectral_centroid_max: float = 500.0
    window_size: float = 0.1


@dataclass
class HighFreqConfig:
    enabled: bool = True
    freq_range: list = field(default_factory=lambda: [2000, 8000])
    energy_threshold: float = 2.5
    zero_crossing_min: float = 0.3
    window_size: float = 0.05


@dataclass
class DetectionConfig:
    low_freq: LowFreqConfig = field(default_factory=LowFreqConfig)
    high_freq: HighFreqConfig = field(default_factory=HighFreqConfig)
    cooldown_seconds: float = 5.0
    background_learning_seconds: float = 10.0


@dataclass
class FeedbackSounds:
    mild: str = "sounds/alert_mild.wav"
    medium: str = "sounds/alert_medium.wav"
    strong: str = "sounds/alert_strong.wav"


@dataclass
class FeedbackConfig:
    enabled: bool = True
    output_device_index: Optional[int] = None
    sounds: FeedbackSounds = field(default_factory=FeedbackSounds)
    volume: float = 1.0
    delay: int = 2000


@dataclass
class LoggingConfig:
    level: str = "INFO"
    save_audio_clips: bool = False
    clips_dir: str = "logs/clips"


@dataclass
class AppConfig:
    sample_rate: int = 44100
    chunk_size: int = 1024
    channels: int = 1
    input_device_index: Optional[int] = None
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    if config_path is None:
        config_path = get_config_path()

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return _dict_to_config(data)
    return AppConfig()


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    if config_path is None:
        config_path = get_config_path()

    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = _config_to_dict(config)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def _dict_to_config(data: dict) -> AppConfig:
    audio_section = data.get("audio", {})
    audio_keys = ["sample_rate", "chunk_size", "channels", "input_device_index"]
    audio_data = {k: audio_section.get(k) for k in audio_keys if k in audio_section}

    detection_data = data.get("detection", {})
    low_freq_data = detection_data.get("low_freq", {})
    high_freq_data = detection_data.get("high_freq", {})

    feedback_data = data.get("feedback", {})
    sounds_data = feedback_data.get("sounds", {})

    logging_data = data.get("logging", {})

    return AppConfig(
        sample_rate=audio_data.get("sample_rate", 44100),
        chunk_size=audio_data.get("chunk_size", 1024),
        channels=audio_data.get("channels", 1),
        input_device_index=audio_data.get("input_device_index"),
        detection=DetectionConfig(
            low_freq=LowFreqConfig(
                enabled=low_freq_data.get("enabled", True),
                freq_range=low_freq_data.get("freq_range", [20, 250]),
                energy_threshold=low_freq_data.get("energy_threshold", 3.0),
                spectral_centroid_max=low_freq_data.get("spectral_centroid_max", 500.0),
                window_size=low_freq_data.get("window_size", 0.1),
            ),
            high_freq=HighFreqConfig(
                enabled=high_freq_data.get("enabled", True),
                freq_range=high_freq_data.get("freq_range", [2000, 8000]),
                energy_threshold=high_freq_data.get("energy_threshold", 2.5),
                zero_crossing_min=high_freq_data.get("zero_crossing_min", 0.3),
                window_size=high_freq_data.get("window_size", 0.05),
            ),
            cooldown_seconds=detection_data.get("cooldown_seconds", 5.0),
            background_learning_seconds=detection_data.get("background_learning_seconds", 10.0),
        ),
        feedback=FeedbackConfig(
            enabled=feedback_data.get("enabled", True),
            output_device_index=feedback_data.get("output_device_index"),
            sounds=FeedbackSounds(
                mild=sounds_data.get("mild", "sounds/alert_mild.wav"),
                medium=sounds_data.get("medium", "sounds/alert_medium.wav"),
                strong=sounds_data.get("strong", "sounds/alert_strong.wav"),
            ),
            volume=feedback_data.get("volume", 1.0),
            delay=feedback_data.get("delay", 2000),
        ),
        logging=LoggingConfig(
            level=logging_data.get("level", "INFO"),
            save_audio_clips=logging_data.get("save_audio_clips", False),
            clips_dir=logging_data.get("clips_dir", "logs/clips"),
        ),
    )


def _config_to_dict(config: AppConfig) -> dict:
    return {
        "audio": {
            "sample_rate": config.sample_rate,
            "chunk_size": config.chunk_size,
            "channels": config.channels,
            "input_device_index": config.input_device_index,
        },
        "detection": {
            "low_freq": {
                "enabled": config.detection.low_freq.enabled,
                "freq_range": config.detection.low_freq.freq_range,
                "energy_threshold": config.detection.low_freq.energy_threshold,
                "spectral_centroid_max": config.detection.low_freq.spectral_centroid_max,
                "window_size": config.detection.low_freq.window_size,
            },
            "high_freq": {
                "enabled": config.detection.high_freq.enabled,
                "freq_range": config.detection.high_freq.freq_range,
                "energy_threshold": config.detection.high_freq.energy_threshold,
                "zero_crossing_min": config.detection.high_freq.zero_crossing_min,
                "window_size": config.detection.high_freq.window_size,
            },
            "cooldown_seconds": config.detection.cooldown_seconds,
            "background_learning_seconds": config.detection.background_learning_seconds,
        },
        "feedback": {
            "enabled": config.feedback.enabled,
            "output_device_index": config.feedback.output_device_index,
            "sounds": {
                "mild": config.feedback.sounds.mild,
                "medium": config.feedback.sounds.medium,
                "strong": config.feedback.sounds.strong,
            },
            "volume": config.feedback.volume,
            "delay": config.feedback.delay,
        },
        "logging": {
            "level": config.logging.level,
            "save_audio_clips": config.logging.save_audio_clips,
            "clips_dir": config.logging.clips_dir,
        },
    }
