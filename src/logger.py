"""Logging and event recording module."""

import logging
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

from .noise_detector.engine import NoiseEvent


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("noise_revenger")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class EventLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._events_file = self.log_dir / "noise_events.jsonl"
        self._daily_file = self._get_daily_csv_path()

    def _get_daily_csv_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"noise_events_{today}.csv"

    def log_event(self, event: NoiseEvent):
        record = {
            "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
            "noise_type": event.noise_type.value,
            "intensity": event.intensity.value,
            "confidence": round(event.confidence, 4),
        }
        self._append_jsonl(record)
        self._append_csv(record)

    def _append_jsonl(self, record: dict):
        with open(self._events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _append_csv(self, record: dict):
        file_exists = self._daily_file.exists()
        with open(self._daily_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "noise_type", "intensity", "confidence"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

    def get_today_events(self) -> list:
        path = self._daily_file
        if not path.exists():
            return []
        events = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
        return events

    def get_stats(self) -> dict:
        events = self.get_today_events()
        if not events:
            return {"total": 0}

        stats = {
            "total": len(events),
            "low_freq_impact": 0,
            "high_freq_friction": 0,
            "mild": 0,
            "medium": 0,
            "strong": 0,
        }
        for e in events:
            if e["noise_type"] == "low_freq_impact":
                stats["low_freq_impact"] += 1
            elif e["noise_type"] == "high_freq_friction":
                stats["high_freq_friction"] += 1
            stats[e["intensity"]] = stats.get(e["intensity"], 0) + 1
        return stats
