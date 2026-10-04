"""Core orchestration: run the full comparison pipeline."""

from __future__ import annotations

from pathlib import Path

from sounddifff.detection import compare_detection
from sounddifff.formats import load_audio
from sounddifff.loudness import compare_loudness
from sounddifff.spectral import compare_spectral
from sounddifff.temporal import compare_temporal
from sounddifff.types import DiffResult, MetadataComparison


def diff(
    path_a: str | Path,
    path_b: str | Path,
) -> DiffResult:
    """Compare two audio files and return a structured diff.

    Args:
        path_a: Path to the first (reference) audio file.
        path_b: Path to the second (comparison) audio file.

    Returns:
        DiffResult containing all analysis results.

    Raises:
        FileNotFoundError: If either file does not exist.
        ValueError: If either file format is unsupported.
    """
    data_a, meta_a = load_audio(path_a)
    data_b, meta_b = load_audio(path_b)

    metadata = MetadataComparison(file_a=meta_a, file_b=meta_b)

    warnings: list[str] = []
    if not metadata.same_sample_rate:
        warnings.append(
            f"Sample rate mismatch: {meta_a.sample_rate} Hz vs {meta_b.sample_rate} Hz. "
            "Comparison accuracy may be reduced."
        )
    if not metadata.same_channels:
        warnings.append(
            f"Channel count mismatch: {meta_a.channels} vs {meta_b.channels}. "
            "Comparison will use mixed-to-mono signals where needed."
        )

    loudness = compare_loudness(data_a, data_b, meta_a.sample_rate, meta_b.sample_rate)
    spectral = compare_spectral(data_a, data_b, meta_a.sample_rate, meta_b.sample_rate)
    temporal = compare_temporal(data_a, data_b, meta_a.sample_rate)

    file_a_name = Path(meta_a.path).name
    file_b_name = Path(meta_b.path).name
    detection = compare_detection(
        data_a, data_b, meta_a.sample_rate, meta_b.sample_rate, file_a_name, file_b_name
    )

    return DiffResult(
        metadata=metadata,
        loudness=loudness,
        spectral=spectral,
        temporal=temporal,
        detection=detection,
        warnings=warnings,
    )
