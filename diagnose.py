"""Diagnostic script to test audio capture and detection."""

import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config
from src.audio_capture import AudioCapture
from src.noise_detector.low_freq import LowFreqDetector
from src.noise_detector.high_freq import HighFreqDetector


def main():
    config = load_config()
    
    print("=" * 60)
    print("Noise Revenger - Audio Diagnostic Tool")
    print("=" * 60)
    
    print(f"\nConfig: sample_rate={config.sample_rate}, chunk_size={config.chunk_size}")
    
    print("\nAvailable audio devices:")
    devices = AudioCapture.list_devices()
    for i, dev in enumerate(devices):
        print(f"  [{i}] {dev['name']} (inputs={dev['max_input_channels']}, outputs={dev['max_output_channels']})")
    
    default_input = AudioCapture.get_default_input_device()
    print(f"\nDefault input device: {default_input['name']}")
    
    print("\nStarting audio capture...")
    print("Make some noise (clap, stomp, drag chair) to test detection!")
    print("Press Ctrl+C to stop.\n")
    
    capture = AudioCapture(
        sample_rate=config.sample_rate,
        chunk_size=config.chunk_size,
        channels=config.channels,
        device_index=config.input_device_index,
    )
    
    low_detector = LowFreqDetector(
        sample_rate=config.sample_rate,
        freq_range=tuple(config.detection.low_freq.freq_range),
        energy_threshold=config.detection.low_freq.energy_threshold,
        spectral_centroid_max=config.detection.low_freq.spectral_centroid_max,
    )
    
    high_detector = HighFreqDetector(
        sample_rate=config.sample_rate,
        freq_range=tuple(config.detection.high_freq.freq_range),
        energy_threshold=config.detection.high_freq.energy_threshold,
        zero_crossing_min=config.detection.high_freq.zero_crossing_min,
    )
    
    capture.start()
    
    chunk_count = 0
    learning_chunks = 20
    
    try:
        while True:
            chunk = capture.read_chunk(timeout=1.0)
            if chunk is None:
                print("[WARN] No audio data received!")
                continue
            
            audio = chunk.flatten()
            rms = np.sqrt(np.mean(audio ** 2))
            
            if chunk_count < learning_chunks:
                low_detector.update_background(audio)
                high_detector.update_background(audio)
                if chunk_count % 5 == 0:
                    print(f"Learning background... ({chunk_count}/{learning_chunks}) RMS={rms:.6f}")
                chunk_count += 1
                continue
            
            low_result = low_detector.analyze(audio)
            high_result = high_detector.analyze(audio)
            
            if chunk_count % 10 == 0:
                print(f"RMS={rms:.6f} | Low: energy={low_result['normalized_energy']:.2f}, "
                      f"centroid={low_result['spectral_centroid']:.0f}Hz, "
                      f"detected={low_result['detected']}")
                print(f"         High: energy={high_result['normalized_energy']:.2f}, "
                      f"zcr={high_result['zero_crossing_rate']:.3f}, "
                      f"detected={high_result['detected']}")
            
            if low_result["detected"]:
                print(f"\n*** LOW FREQ IMPACT DETECTED! confidence={low_result['confidence']:.2f} ***\n")
            
            if high_result["detected"]:
                print(f"\n*** HIGH FREQ FRICTION DETECTED! confidence={high_result['confidence']:.2f} ***\n")
            
            chunk_count += 1
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        capture.stop()


if __name__ == "__main__":
    main()