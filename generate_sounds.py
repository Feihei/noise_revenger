"""Generate default alert sound WAV files."""

import numpy as np
import wave
import struct
from pathlib import Path


def generate_tone(frequency: float, duration: float, sample_rate: int = 44100,
                  amplitude: float = 0.5) -> bytes:
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    fade_out = np.linspace(1.0, 0.0, int(sample_rate * 0.1))
    tone[-len(fade_out):] *= fade_out
    audio_data = (tone * 32767).astype(np.int16)
    return audio_data.tobytes()


def generate_alert_sound(output_path: str, frequencies: list, durations: list,
                         sample_rate: int = 44100):
    all_samples = b""
    for freq, dur in zip(frequencies, durations):
        all_samples += generate_tone(freq, dur, sample_rate)

    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(all_samples)


def main():
    sounds_dir = Path("sounds")
    sounds_dir.mkdir(exist_ok=True)

    generate_alert_sound(
        str(sounds_dir / "alert_mild.wav"),
        frequencies=[800, 1000],
        durations=[0.15, 0.15],
    )

    generate_alert_sound(
        str(sounds_dir / "alert_medium.wav"),
        frequencies=[600, 900, 1200],
        durations=[0.12, 0.12, 0.12],
    )

    generate_alert_sound(
        str(sounds_dir / "alert_strong.wav"),
        frequencies=[400, 700, 1000, 1400],
        durations=[0.1, 0.1, 0.1, 0.1],
    )

    print("Alert sounds generated successfully.")


if __name__ == "__main__":
    main()
