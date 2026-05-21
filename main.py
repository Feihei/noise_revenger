"""Noise Revenger - Real-time noise feedback system main entry point."""

import sys
import time
import signal
import logging
import argparse
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, AppConfig
from src.audio_capture import AudioCapture
from src.noise_detector.engine import NoiseDetector
from src.feedback_player import FeedbackPlayer
from src.logger import setup_logging, EventLogger
from src.gui import NoiseRevengerGUI
from src.paths import get_logs_dir

logger = logging.getLogger(__name__)


class NoiseRevenger:
    def __init__(self, config: AppConfig):
        self.config = config
        self._running = False

        setup_logging(
            level=config.logging.level,
            log_file=str(get_logs_dir() / "noise_revenger.log")
        )

        self.capture = AudioCapture(
            sample_rate=config.sample_rate,
            chunk_size=config.chunk_size,
            channels=config.channels,
            device_index=config.input_device_index,
        )

        self.detector = NoiseDetector(
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

        sounds = {
            "mild": config.feedback.sounds.mild,
            "medium": config.feedback.sounds.medium,
            "strong": config.feedback.sounds.strong,
        }
        self.player = FeedbackPlayer(
            sounds=sounds,
            volume=config.feedback.volume,
        )

        self.event_logger = EventLogger(log_dir=str(get_logs_dir()))

    def _learn_background(self, duration: float):
        logger.info(f"Learning background noise for {duration} seconds...")
        start = time.time()
        chunks_collected = 0
        while time.time() - start < duration:
            chunk = self.capture.read_chunk(timeout=1.0)
            if chunk is not None:
                self.detector.learn_background(chunk.flatten())
                chunks_collected += 1
        logger.info(f"Background learning complete. Collected {chunks_collected} chunks.")

    def _handle_noise_event(self, event):
        self.event_logger.log_event(event)
        if self.config.feedback.enabled:
            delay_ms = self.config.feedback.delay
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            self.player.play(event.intensity.value)

    def run(self):
        self._running = True
        logger.info("Noise Revenger starting...")

        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, lambda s, f: (self.stop(), original_sigint(s, f) if original_sigint else None))
        signal.signal(signal.SIGTERM, lambda s, f: (self.stop(), original_sigterm(s, f) if original_sigterm else None))

        try:
            self.capture.start()
            self._learn_background(self.config.detection.background_learning_seconds)

            logger.info("Monitoring started. Waiting for noise events...")

            while self._running:
                chunk = self.capture.read_chunk(timeout=1.0)
                if chunk is None:
                    continue

                audio_data = chunk.flatten()
                event = self.detector.analyze(audio_data)
                if event is not None:
                    self._handle_noise_event(event)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._cleanup()

    def stop(self):
        logger.info("Stopping Noise Revenger...")
        self._running = False

    def _cleanup(self):
        self.capture.stop()
        self.player.quit()
        logger.info("Noise Revenger stopped")


def run_cli(config: AppConfig):
    app = NoiseRevenger(config)
    app.run()


def run_gui(config: AppConfig):
    gui = NoiseRevengerGUI(config)
    gui.run()


def main():
    parser = argparse.ArgumentParser(description="Noise Revenger - Real-time noise feedback system")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch with graphical user interface",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch in command-line mode (no GUI)",
    )
    args = parser.parse_args()

    config = load_config()

    if args.cli:
        run_cli(config)
    else:
        run_gui(config)


if __name__ == "__main__":
    main()
