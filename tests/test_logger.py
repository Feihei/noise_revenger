"""Tests for event logger module."""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import EventLogger
from src.noise_detector.engine import NoiseEvent, NoiseType, NoiseIntensity


class TestEventLogger:
    def test_log_event_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            event = NoiseEvent(
                noise_type=NoiseType.LOW_FREQ_IMPACT,
                intensity=NoiseIntensity.MEDIUM,
                confidence=0.65,
                timestamp=datetime.now().timestamp(),
            )
            logger.log_event(event)

            jsonl_path = Path(tmpdir) / "noise_events.jsonl"
            assert jsonl_path.exists()

            today = datetime.now().strftime("%Y-%m-%d")
            csv_path = Path(tmpdir) / f"noise_events_{today}.csv"
            assert csv_path.exists()

    def test_jsonl_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            event = NoiseEvent(
                noise_type=NoiseType.HIGH_FREQ_FRICTION,
                intensity=NoiseIntensity.STRONG,
                confidence=0.85,
                timestamp=1700000000.0,
            )
            logger.log_event(event)

            jsonl_path = Path(tmpdir) / "noise_events.jsonl"
            with open(jsonl_path, "r", encoding="utf-8") as f:
                line = f.readline()
                record = json.loads(line)

            assert record["noise_type"] == "high_freq_friction"
            assert record["intensity"] == "strong"
            assert record["confidence"] == 0.85

    def test_csv_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            event = NoiseEvent(
                noise_type=NoiseType.LOW_FREQ_IMPACT,
                intensity=NoiseIntensity.MILD,
                confidence=0.3,
                timestamp=datetime.now().timestamp(),
            )
            logger.log_event(event)

            today = datetime.now().strftime("%Y-%m-%d")
            csv_path = Path(tmpdir) / f"noise_events_{today}.csv"
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["noise_type"] == "low_freq_impact"
            assert rows[0]["intensity"] == "mild"

    def test_get_today_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            event = NoiseEvent(
                noise_type=NoiseType.LOW_FREQ_IMPACT,
                intensity=NoiseIntensity.MEDIUM,
                confidence=0.5,
                timestamp=datetime.now().timestamp(),
            )
            logger.log_event(event)
            logger.log_event(event)

            events = logger.get_today_events()
            assert len(events) == 2

    def test_get_today_events_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            events = logger.get_today_events()
            assert events == []

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            events_data = [
                (NoiseType.LOW_FREQ_IMPACT, NoiseIntensity.MILD, 0.3),
                (NoiseType.HIGH_FREQ_FRICTION, NoiseIntensity.MEDIUM, 0.5),
                (NoiseType.LOW_FREQ_IMPACT, NoiseIntensity.STRONG, 0.8),
            ]
            for ntype, intensity, conf in events_data:
                event = NoiseEvent(
                    noise_type=ntype,
                    intensity=intensity,
                    confidence=conf,
                    timestamp=datetime.now().timestamp(),
                )
                logger.log_event(event)

            stats = logger.get_stats()
            assert stats["total"] == 3
            assert stats["low_freq_impact"] == 2
            assert stats["high_freq_friction"] == 1
            assert stats["mild"] == 1
            assert stats["medium"] == 1
            assert stats["strong"] == 1

    def test_get_stats_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            stats = logger.get_stats()
            assert stats == {"total": 0}

    def test_multiple_events_append(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLogger(log_dir=tmpdir)
            for i in range(5):
                event = NoiseEvent(
                    noise_type=NoiseType.LOW_FREQ_IMPACT,
                    intensity=NoiseIntensity.MILD,
                    confidence=0.3,
                    timestamp=datetime.now().timestamp(),
                )
                logger.log_event(event)

            events = logger.get_today_events()
            assert len(events) == 5
