"""Detection: clipping and silence analysis."""

from __future__ import annotations

import numpy as np

from sounddifff.types import ClipEvent, DetectionResult, SilenceRegion


def detect_clipping(
    data: np.ndarray,
    sample_rate: int,
    file_label: str,
    threshold: float = 0.99,
    min_consecutive: int = 2,
) -> list[ClipEvent]:
    """Detect clipping events in an audio signal.

    Clipping is defined as consecutive samples at or above the threshold.

    Args:
        data: Audio signal, shape (frames, channels).
        sample_rate: Sample rate in Hz.
        file_label: Label for this file (used in output).
        threshold: Amplitude threshold for clipping detection.
        min_consecutive: Minimum consecutive samples to count as clipping.

    Returns:
        List of ClipEvent objects.
    """
    clips: list[ClipEvent] = []

    for channel in range(data.shape[1]):
        channel_data = np.abs(data[:, channel])
        is_clipping = channel_data >= threshold

        # Find runs of consecutive clipping samples
        changes = np.diff(is_clipping.astype(int))
        starts = np.where(changes == 1)[0] + 1
        ends = np.where(changes == -1)[0] + 1

        # Handle edge cases
        if is_clipping[0]:
            starts = np.concatenate([[0], starts])
        if is_clipping[-1]:
            ends = np.concatenate([ends, [len(channel_data)]])

        for start, end in zip(starts, ends, strict=True):
            count = end - start
            if count >= min_consecutive:
                timestamp = start / sample_rate
                clips.append(
                    ClipEvent(
                        file_label=file_label,
                        timestamp=round(timestamp, 3),
                        channel=channel,
                        sample_count=int(count),
                    )
                )

    return clips


def detect_silence(
    data: np.ndarray,
    sample_rate: int,
    file_label: str,
    threshold_db: float = -60.0,
    min_duration: float = 0.1,
) -> list[SilenceRegion]:
    """Detect regions of silence in an audio signal.

    Silence is defined as RMS energy below the threshold for at least min_duration.

    Args:
        data: Audio signal, shape (frames, channels).
        sample_rate: Sample rate in Hz.
        file_label: Label for this file (used in output).
        threshold_db: RMS threshold in dB for silence.
        min_duration: Minimum duration in seconds for a silence region.

    Returns:
        List of SilenceRegion objects.
    """
    # Mix to mono for silence detection
    mono = np.mean(data, axis=1)

    # Compute RMS in short windows
    window_size = int(0.01 * sample_rate)  # 10ms windows
    if window_size == 0:
        return []

    threshold_linear = 10 ** (threshold_db / 20.0)
    min_samples = int(min_duration * sample_rate)

    # Compute per-window RMS
    n_windows = len(mono) // window_size
    if n_windows == 0:
        return []

    truncated = mono[: n_windows * window_size].reshape(n_windows, window_size)
    rms_values = np.sqrt(np.mean(truncated**2, axis=1))
    is_silent = rms_values < threshold_linear

    # Find runs of silence
    regions: list[SilenceRegion] = []
    changes = np.diff(is_silent.astype(int))
    starts = np.where(changes == 1)[0] + 1
    ends = np.where(changes == -1)[0] + 1

    if is_silent[0]:
        starts = np.concatenate([[0], starts])
    if is_silent[-1]:
        ends = np.concatenate([ends, [n_windows]])

    for start, end in zip(starts, ends, strict=True):
        sample_start = start * window_size
        sample_end = end * window_size
        duration_samples = sample_end - sample_start

        if duration_samples >= min_samples:
            regions.append(
                SilenceRegion(
                    file_label=file_label,
                    start_time=round(sample_start / sample_rate, 3),
                    end_time=round(sample_end / sample_rate, 3),
                )
            )

    return regions


def compare_detection(
    data_a: np.ndarray,
    data_b: np.ndarray,
    sample_rate_a: int,
    sample_rate_b: int,
    file_a_name: str,
    file_b_name: str,
) -> DetectionResult:
    """Run clipping and silence detection on both files.

    Args:
        data_a: First audio signal.
        data_b: Second audio signal.
        sample_rate_a: Sample rate of first signal.
        sample_rate_b: Sample rate of second signal.
        file_a_name: Display name for first file.
        file_b_name: Display name for second file.

    Returns:
        DetectionResult with clips and silence regions.
    """
    clips_a = detect_clipping(data_a, sample_rate_a, file_a_name)
    clips_b = detect_clipping(data_b, sample_rate_b, file_b_name)

    silence_a = detect_silence(data_a, sample_rate_a, file_a_name)
    silence_b = detect_silence(data_b, sample_rate_b, file_b_name)

    return DetectionResult(
        clips=clips_a + clips_b,
        silence_regions_a=silence_a,
        silence_regions_b=silence_b,
    )
