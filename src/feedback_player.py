"""Feedback audio player module for playing alert sounds."""

import pygame
import logging
from pathlib import Path
from typing import Optional

from .paths import get_sounds_path

logger = logging.getLogger(__name__)


class FeedbackPlayer:
    def __init__(self, sounds: dict, volume: float = 1.0):
        self.sounds = sounds
        self.volume = max(0.0, min(1.0, volume))
        self._initialized = False

    def _init_mixer(self):
        if not self._initialized:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            self._initialized = True
            logger.info("Audio mixer initialized")

    def play(self, intensity: str) -> bool:
        self._init_mixer()

        sound_path_str = self.sounds.get(intensity)
        if sound_path_str is None:
            logger.warning(f"No sound configured for intensity: {intensity}")
            return False

        path = Path(sound_path_str)
        if not path.is_absolute():
            path = get_sounds_path(path.name)

        if not path.exists():
            logger.warning(f"Sound file not found: {path}")
            return False

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self.volume)
            sound.play()
            logger.info(f"Playing alert sound: {path} (intensity={intensity})")
            return True
        except Exception as e:
            logger.error(f"Failed to play sound: {e}")
            return False

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self.volume)

    def stop(self):
        if self._initialized:
            pygame.mixer.stop()

    def quit(self):
        if self._initialized:
            pygame.mixer.quit()
            self._initialized = False
