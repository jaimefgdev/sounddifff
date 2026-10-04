"""Tests for output formatting."""

from __future__ import annotations

import json

from sounddifff.report import render_json, render_terminal
from sounddifff.types import (
    AudioMetadata,
    ClipEvent,
    DetectionResult,
    DiffResult,
    LoudnessComparison,
    LoudnessResult,
    MetadataComparison,
    Segment,
    SegmentKind,
    SpectralBand,
    SpectralComparison,
    TemporalComparison,
)


def _make_result() -> DiffResult:
    """Create a sample DiffResult for testing."""
    return DiffResult(
        metadata=MetadataComparison(
            file_a=AudioMetadata(
                path="/tmp/a.wav",
                duration=10.0,
                sample_rate=48000,
                channels=2,
                bit_depth=16,
                format_name="WAV",
                frames=480000,
            ),
            file_b=AudioMetadata(
                path="/tmp/b.wav",
                duration=10.0,
                sample_rate=48000,
                channels=2,
                bit_depth=16,
                format_name="WAV",
                frames=480000,
            ),
        ),
        loudness=LoudnessComparison(
            file_a=LoudnessResult(lufs=-14.2, true_peak_dbtp=-1.1, loudness_range=8.2),
            file_b=LoudnessResult(lufs=-12.8, true_peak_dbtp=-0.3, loudness_range=6.4),
        ),
        spectral=SpectralComparison(
            bands=[
                SpectralBand("Low", 20, 250, -30.0, -29.2),
                SpectralBand("Mid", 250, 4000, -25.0, -24.7),
                SpectralBand("High", 4000, 20000, -35.0, -33.1),
            ]
        ),
        temporal=TemporalComparison(
            segments=[
                Segment(SegmentKind.SIMILAR, 0.0, 10.0, correlation=0.98),
            ],
            overall_correlation=0.98,
        ),
        detection=DetectionResult(
            clips=[ClipEvent("b.wav", 5.123, 0, 3)],
            silence_regions_a=[],
            silence_regions_b=[],
        ),
    )


class TestRenderTerminal:
    def test_contains_file_names(self) -> None:
        output = render_terminal(_make_result())
        assert "a.wav" in output
        assert "b.wav" in output

    def test_contains_lufs(self) -> None:
        output = render_terminal(_make_result())
        assert "LUFS" in output

    def test_contains_clipping_warning(self) -> None:
        output = render_terminal(_make_result())
        assert "Clipping" in output


class TestRenderJSON:
    def test_is_valid_json(self) -> None:
        output = render_json(_make_result())
        data = json.loads(output)
        assert "metadata" in data
        assert "loudness" in data
        assert "spectral" in data

    def test_contains_lufs_values(self) -> None:
        output = render_json(_make_result())
        data = json.loads(output)
        assert data["loudness"]["file_a"]["lufs"] == -14.2

    def test_segments_have_kind(self) -> None:
        output = render_json(_make_result())
        data = json.loads(output)
        assert data["temporal"]["segments"][0]["kind"] == "similar"
