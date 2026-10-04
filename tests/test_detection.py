"""Tests for clipping and silence detection."""

from __future__ import annotations

import numpy as np

from sounddifff.detection import compare_detection, detect_clipping, detect_silence
from tests.conftest import SAMPLE_RATE


class TestDetectClipping:
    def test_detects_clipped_signal(self) -> None:
        # Create a signal that clips
        t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
        clipped = np.clip(1.5 * np.sin(2 * np.pi * 440 * t), -1.0, 1.0)
        data = np.column_stack([clipped, clipped])

        clips = detect_clipping(data, SAMPLE_RATE, "test.wav")
        assert len(clips) > 0

    def test_no_clipping_in_clean_signal(self) -> None:
        t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
        clean = 0.5 * np.sin(2 * np.pi * 440 * t)
        data = np.column_stack([clean, clean])

        clips = detect_clipping(data, SAMPLE_RATE, "test.wav")
        assert len(clips) == 0

    def test_clip_has_correct_file_label(self) -> None:
        t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
        clipped = np.clip(2.0 * np.sin(2 * np.pi * 440 * t), -1.0, 1.0)
        data = np.column_stack([clipped, clipped])

        clips = detect_clipping(data, SAMPLE_RATE, "my_file.wav")
        assert all(c.file_label == "my_file.wav" for c in clips)

    def test_custom_threshold(self) -> None:
        t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
        signal = 0.8 * np.sin(2 * np.pi * 440 * t)
        data = np.column_stack([signal, signal])

        # Should not clip with default threshold
        clips_default = detect_clipping(data, SAMPLE_RATE, "test.wav")
        assert len(clips_default) == 0

        # Should clip with lower threshold
        clips_low = detect_clipping(data, SAMPLE_RATE, "test.wav", threshold=0.7)
        assert len(clips_low) > 0


class TestDetectSilence:
    def test_detects_silence_region(self) -> None:
        # 1 second of tone, 0.5 seconds of silence, 1 second of tone
        t = np.linspace(0, 2.5, int(SAMPLE_RATE * 2.5), endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        signal[SAMPLE_RATE : int(SAMPLE_RATE * 1.5)] = 0.0
        data = np.column_stack([signal, signal])

        regions = detect_silence(data, SAMPLE_RATE, "test.wav")
        assert len(regions) > 0
        assert any(r.duration >= 0.4 for r in regions)

    def test_no_silence_in_continuous_signal(self) -> None:
        t = np.linspace(0, 2, SAMPLE_RATE * 2, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        data = np.column_stack([signal, signal])

        regions = detect_silence(data, SAMPLE_RATE, "test.wav")
        assert len(regions) == 0

    def test_short_silence_below_minimum_ignored(self) -> None:
        t = np.linspace(0, 2, SAMPLE_RATE * 2, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        # Very short silence (10ms) should be ignored with default min_duration (100ms)
        short_silence = int(0.01 * SAMPLE_RATE)
        signal[SAMPLE_RATE : SAMPLE_RATE + short_silence] = 0.0
        data = np.column_stack([signal, signal])

        regions = detect_silence(data, SAMPLE_RATE, "test.wav", min_duration=0.1)
        assert len(regions) == 0


class TestCompareDetection:
    def test_returns_combined_results(self) -> None:
        t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
        clean = 0.5 * np.sin(2 * np.pi * 440 * t)
        clipped = np.clip(1.5 * np.sin(2 * np.pi * 440 * t), -1.0, 1.0)

        data_a = np.column_stack([clean, clean])
        data_b = np.column_stack([clipped, clipped])

        result = compare_detection(data_a, data_b, SAMPLE_RATE, SAMPLE_RATE, "a.wav", "b.wav")
        assert len(result.clips) > 0
        assert any(c.file_label == "b.wav" for c in result.clips)
