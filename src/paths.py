"""Path utilities for handling both development and PyInstaller frozen environments."""

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Get the base directory of the application.

    In development: returns the project root directory.
    In frozen (PyInstaller) mode: returns the directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def get_config_path(config_filename: str = "settings.yaml") -> Path:
    """Get the path to a configuration file."""
    return get_base_dir() / "config" / config_filename


def get_sounds_path(filename: str) -> Path:
    """Get the path to a sound file."""
    return get_base_dir() / "sounds" / filename


def get_logs_dir(subdir: str = "") -> Path:
    """Get the path to the logs directory."""
    path = get_base_dir() / "logs"
    if subdir:
        path = path / subdir
    return path
