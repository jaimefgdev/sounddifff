"""Data types for sounddifff analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats."""

    TERMINAL = "terminal"
    JSON = "json"
    HTML = "html"


class SegmentKind(Enum):
    """Classification of a segment comparison."""

    SIMILAR = "similar"
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True)
class AudioMetadata:
    """Basic audio file metadata."""

    path: str
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int | None
    format_name: str
    frames: int


@dataclass(frozen=True)
class MetadataComparison:
    """Comparison of metadata between two audio files."""

    file_a: AudioMetadata
    file_b: AudioMetadata

    @property
    def duration_delta(self) -> float:
        return self.file_b.duration - self.file_a.duration

    @property
    def same_duration(self) -> bool:
        return abs(self.duration_delta) < 0.001

    @property
    def same_sample_rate(self) -> bool:
        return self.file_a.sample_rate == self.file_b.sample_rate

    @property
    def same_channels(self) -> bool:
        return self.file_a.channels == self.file_b.channels


@dataclass(frozen=True)
class LoudnessResult:
    """Loudness measurement for a single file."""

    lufs: float
    true_peak_dbtp: float
    loudness_range: float


@dataclass(frozen=True)
class LoudnessComparison:
    """Comparison of loudness between two files."""

    file_a: LoudnessResult
    file_b: LoudnessResult

    @property
    def lufs_delta(self) -> float:
        return self.file_b.lufs - self.file_a.lufs

    @property
    def peak_delta(self) -> float:
        return self.file_b.true_peak_dbtp - self.file_a.true_peak_dbtp

    @property
    def lra_delta(self) -> float:
        return self.file_b.loudness_range - self.file_a.loudness_range


@dataclass(frozen=True)
class SpectralBand:
    """Energy measurement for a frequency band."""

    name: str
    low_hz: float
    high_hz: float
    energy_db_a: float
    energy_db_b: float

    @property
    def delta_db(self) -> float:
        noise_floor = -100.0
        a = max(self.energy_db_a, noise_floor)
        b = max(self.energy_db_b, noise_floor)
        return b - a


@dataclass(frozen=True)
class SpectralComparison:
    """Comparison of spectral energy across frequency bands."""

    bands: list[SpectralBand]


@dataclass(frozen=True)
class Segment:
    """A detected segment in the comparison."""

    kind: SegmentKind
    start_time: float
    end_time: float
    correlation: float | None = None
    time_shift: float | None = None

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass(frozen=True)
class TemporalComparison:
    """Comparison of temporal structure between two files."""

    segments: list[Segment]
    overall_correlation: float


@dataclass(frozen=True)
class ClipEvent:
    """A detected clipping event."""

    file_label: str
    timestamp: float
    channel: int
    sample_count: int


@dataclass(frozen=True)
class SilenceRegion:
    """A detected region of silence."""

    file_label: str
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass(frozen=True)
class DetectionResult:
    """Results from clipping and silence detection."""

    clips: list[ClipEvent]
    silence_regions_a: list[SilenceRegion]
    silence_regions_b: list[SilenceRegion]


@dataclass(frozen=True)
class DiffResult:
    """Complete result of comparing two audio files."""

    metadata: MetadataComparison
    loudness: LoudnessComparison
    spectral: SpectralComparison
    temporal: TemporalComparison
    detection: DetectionResult
    warnings: list[str] = field(default_factory=list)
