"""Audio file loading and format detection."""

from __future__ import annotations

from pathlib import Path

import numpy as np  # noqa: TC002 (used at runtime in return type)
import soundfile as sf

from sounddifff.types import AudioMetadata

# Formats supported natively via libsndfile
NATIVE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}

# Formats that require ffmpeg
FFMPEG_FORMATS = {".mp3", ".aac", ".m4a", ".wma", ".opus"}


def load_audio(path: str | Path) -> tuple[np.ndarray, AudioMetadata]:
    """Load an audio file and return the signal and metadata.

    Args:
        path: Path to the audio file.

    Returns:
        Tuple of (audio signal as float64 ndarray, metadata).
        Signal is always 2D: (frames, channels). Mono files get shape (frames, 1).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the format is unsupported or requires ffmpeg.
        RuntimeError: If the file cannot be read.
    """
    filepath = Path(path)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    suffix = filepath.suffix.lower()

    if suffix in FFMPEG_FORMATS:
        raise ValueError(
            f"Format '{suffix}' requires ffmpeg, which is not installed or not supported yet. "
            f"Supported formats without ffmpeg: {', '.join(sorted(NATIVE_FORMATS))}"
        )

    if suffix not in NATIVE_FORMATS:
        raise ValueError(
            f"Unsupported audio format: '{suffix}'. "
            f"Supported: {', '.join(sorted(NATIVE_FORMATS | FFMPEG_FORMATS))}"
        )

    try:
        info = sf.info(str(filepath))
    except RuntimeError as e:
        raise RuntimeError(f"Cannot read audio file: {filepath} ({e})") from e

    data, sample_rate = sf.read(str(filepath), dtype="float64", always_2d=True)

    metadata = AudioMetadata(
        path=str(filepath),
        duration=len(data) / sample_rate,
        sample_rate=sample_rate,
        channels=data.shape[1],
        bit_depth=_subtype_to_bits(info.subtype),
        format_name=info.format,
        frames=len(data),
    )

    return data, metadata


def _subtype_to_bits(subtype: str) -> int | None:
    """Convert soundfile subtype string to bit depth."""
    mapping: dict[str, int] = {
        "PCM_16": 16,
        "PCM_24": 24,
        "PCM_32": 32,
        "PCM_S8": 8,
        "PCM_U8": 8,
        "FLOAT": 32,
        "DOUBLE": 64,
    }
    return mapping.get(subtype)


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as M:SS.mmm."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"


def format_channels(n: int) -> str:
    """Format channel count as a human-readable string."""
    if n == 1:
        return "mono"
    if n == 2:
        return "stereo"
    return f"{n}ch"
