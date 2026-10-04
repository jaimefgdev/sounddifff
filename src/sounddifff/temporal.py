"""Temporal analysis: waveform correlation and segment detection."""

from __future__ import annotations

import numpy as np

from sounddifff.types import Segment, SegmentKind, TemporalComparison


def compute_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Compute normalized cross-correlation between two signals.

    Args:
        a: First signal (1D).
        b: Second signal (1D).

    Returns:
        Correlation coefficient in range [-1, 1].
    """
    if len(a) == 0 or len(b) == 0:
        return 0.0

    # Truncate to same length for direct comparison
    min_len = min(len(a), len(b))
    a = a[:min_len]
    b = b[:min_len]

    a_norm = a - np.mean(a)
    b_norm = b - np.mean(b)

    denom = np.sqrt(np.sum(a_norm**2) * np.sum(b_norm**2))
    if denom < 1e-10:
        return 0.0

    return float(np.sum(a_norm * b_norm) / denom)


def detect_segments(
    data_a: np.ndarray,
    data_b: np.ndarray,
    sample_rate: int,
    window_seconds: float = 2.0,
    similarity_threshold: float = 0.9,
) -> list[Segment]:
    """Detect similar, added, or changed segments between two signals.

    Uses windowed cross-correlation to compare chunks of audio.

    Args:
        data_a: First audio signal (mono, 1D).
        data_b: Second audio signal (mono, 1D).
        sample_rate: Sample rate in Hz.
        window_seconds: Analysis window size in seconds.
        similarity_threshold: Correlation threshold for "similar".

    Returns:
        List of Segment objects describing the comparison.
    """
    window_size = int(window_seconds * sample_rate)
    if window_size == 0:
        return []

    len_a = len(data_a)
    len_b = len(data_b)
    max_len = max(len_a, len_b)

    segments: list[Segment] = []
    pos = 0

    while pos < max_len:
        end = min(pos + window_size, max_len)
        start_time = pos / sample_rate
        end_time = end / sample_rate

        chunk_a = data_a[pos:end] if pos < len_a else np.array([])
        chunk_b = data_b[pos:end] if pos < len_b else np.array([])

        if len(chunk_a) == 0 and len(chunk_b) > 0:
            segments.append(
                Segment(kind=SegmentKind.ADDED, start_time=start_time, end_time=end_time)
            )
        elif len(chunk_a) > 0 and len(chunk_b) == 0:
            segments.append(
                Segment(kind=SegmentKind.REMOVED, start_time=start_time, end_time=end_time)
            )
        elif len(chunk_a) > 0 and len(chunk_b) > 0:
            corr = compute_correlation(chunk_a, chunk_b)
            if corr >= similarity_threshold:
                segments.append(
                    Segment(
                        kind=SegmentKind.SIMILAR,
                        start_time=start_time,
                        end_time=end_time,
                        correlation=round(corr, 3),
                    )
                )
            else:
                segments.append(
                    Segment(
                        kind=SegmentKind.CHANGED,
                        start_time=start_time,
                        end_time=end_time,
                        correlation=round(corr, 3),
                    )
                )

        pos = end

    return _merge_adjacent_segments(segments)


def _merge_adjacent_segments(segments: list[Segment]) -> list[Segment]:
    """Merge adjacent segments of the same kind."""
    if not segments:
        return []

    merged: list[Segment] = [segments[0]]

    for seg in segments[1:]:
        prev = merged[-1]
        if prev.kind == seg.kind:
            # Merge: extend the previous segment
            correlations = [c for c in [prev.correlation, seg.correlation] if c is not None]
            avg_corr = round(sum(correlations) / len(correlations), 3) if correlations else None
            merged[-1] = Segment(
                kind=prev.kind,
                start_time=prev.start_time,
                end_time=seg.end_time,
                correlation=avg_corr,
                time_shift=prev.time_shift,
            )
        else:
            merged.append(seg)

    return merged


def compare_temporal(
    data_a: np.ndarray,
    data_b: np.ndarray,
    sample_rate: int,
) -> TemporalComparison:
    """Compare temporal structure between two audio signals.

    Args:
        data_a: First audio signal, shape (frames, channels).
        data_b: Second audio signal, shape (frames, channels).
        sample_rate: Sample rate in Hz.

    Returns:
        TemporalComparison with segment analysis and overall correlation.
    """
    # Mix to mono
    mono_a = np.mean(data_a, axis=1)
    mono_b = np.mean(data_b, axis=1)

    # Overall correlation
    overall = compute_correlation(mono_a, mono_b)

    # Segment detection
    segments = detect_segments(mono_a, mono_b, sample_rate)

    return TemporalComparison(
        segments=segments,
        overall_correlation=round(overall, 3),
    )
