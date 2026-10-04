"""Loudness analysis: integrated LUFS, true peak, loudness range."""

from __future__ import annotations

import numpy as np
import pyloudnorm as pyln

from sounddifff.types import LoudnessComparison, LoudnessResult


def measure_loudness(data: np.ndarray, sample_rate: int) -> LoudnessResult:
    """Measure loudness metrics for an audio signal.

    Args:
        data: Audio signal, shape (frames, channels).
        sample_rate: Sample rate in Hz.

    Returns:
        LoudnessResult with LUFS, true peak, and loudness range.
    """
    meter = pyln.Meter(sample_rate)

    # pyloudnorm expects (samples, channels) which is what we have
    lufs = meter.integrated_loudness(data)

    # True peak: find the maximum absolute sample value across all channels,
    # convert to dBTP. This is a simplified true peak (sample peak).
    # Full ITU-R BS.1770 true peak requires 4x oversampling, but sample peak
    # is a reasonable approximation for comparison purposes.
    peak_linear = np.max(np.abs(data))
    true_peak_dbtp = 20 * np.log10(peak_linear) if peak_linear > 0 else -np.inf

    # Loudness range (LRA): difference between the 95th and 10th percentile
    # of short-term loudness measurements
    lra = _compute_loudness_range(data, sample_rate)

    return LoudnessResult(
        lufs=round(lufs, 1),
        true_peak_dbtp=round(float(true_peak_dbtp), 1),
        loudness_range=round(lra, 1),
    )


def compare_loudness(
    data_a: np.ndarray,
    data_b: np.ndarray,
    sample_rate_a: int,
    sample_rate_b: int,
) -> LoudnessComparison:
    """Compare loudness between two audio signals.

    Args:
        data_a: First audio signal.
        data_b: Second audio signal.
        sample_rate_a: Sample rate of first signal.
        sample_rate_b: Sample rate of second signal.

    Returns:
        LoudnessComparison with measurements for both files.
    """
    result_a = measure_loudness(data_a, sample_rate_a)
    result_b = measure_loudness(data_b, sample_rate_b)
    return LoudnessComparison(file_a=result_a, file_b=result_b)


def _compute_loudness_range(data: np.ndarray, sample_rate: int) -> float:
    """Compute loudness range (LRA) using short-term loudness measurements.

    Uses 3-second windows with 2-second overlap per EBU R128.
    """
    window_size = int(3.0 * sample_rate)
    hop_size = int(1.0 * sample_rate)  # 2s overlap = 1s hop
    meter = pyln.Meter(sample_rate)

    if len(data) < window_size:
        return 0.0

    short_term_levels: list[float] = []
    for start in range(0, len(data) - window_size + 1, hop_size):
        window = data[start : start + window_size]
        level = meter.integrated_loudness(window)
        if np.isfinite(level):
            short_term_levels.append(level)

    if len(short_term_levels) < 2:
        return 0.0

    levels = np.array(short_term_levels)

    # Gate: exclude windows below absolute threshold (-70 LUFS)
    levels = levels[levels > -70.0]
    if len(levels) < 2:
        return 0.0

    # LRA: difference between 95th and 10th percentiles
    p95 = float(np.percentile(levels, 95))
    p10 = float(np.percentile(levels, 10))
    return max(0.0, p95 - p10)
