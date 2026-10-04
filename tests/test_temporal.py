"""Tests for temporal analysis."""

from __future__ import annotations

import numpy as np

from sounddifff.temporal import compare_temporal, compute_correlation, detect_segments
from sounddifff.types import SegmentKind
from tests.conftest import SAMPLE_RATE, make_sine


class TestComputeCorrelation:
    def test_identical_signals_have_correlation_one(self) -> None:
        signal = np.sin(np.linspace(0, 10, 1000))
        assert abs(compute_correlation(signal, signal) - 1.0) < 0.001

    def test_inverted_signal_has_negative_correlation(self) -> None:
        signal = np.sin(np.linspace(0, 10, 1000))
        assert compute_correlation(signal, -signal) < -0.99

    def test_uncorrelated_signals_near_zero(self) -> None:
        rng = np.random.default_rng(42)
        a = rng.normal(size=10000)
        b = rng.normal(size=10000)
        assert abs(compute_correlation(a, b)) < 0.1

    def test_empty_signals_return_zero(self) -> None:
        assert compute_correlation(np.array([]), np.array([])) == 0.0

    def test_different_lengths_truncates(self) -> None:
        a = np.sin(np.linspace(0, 10, 1000))
        b = np.sin(np.linspace(0, 10, 500))
        corr = compute_correlation(a, b)
        assert -1 <= corr <= 1


class TestDetectSegments:
    def test_identical_signals_all_similar(self) -> None:
        signal = np.sin(np.linspace(0, 20, SAMPLE_RATE * 2))
        segments = detect_segments(signal, signal, SAMPLE_RATE)
        assert all(s.kind == SegmentKind.SIMILAR for s in segments)

    def test_different_signals_detected(self) -> None:
        rng = np.random.default_rng(42)
        a = rng.normal(size=SAMPLE_RATE * 2)
        b = rng.normal(size=SAMPLE_RATE * 2)
        segments = detect_segments(a, b, SAMPLE_RATE)
        assert any(s.kind in (SegmentKind.CHANGED, SegmentKind.ADDED) for s in segments)

    def test_longer_b_shows_added(self) -> None:
        a = np.sin(np.linspace(0, 10, SAMPLE_RATE * 2))
        b = np.sin(np.linspace(0, 15, SAMPLE_RATE * 3))
        segments = detect_segments(a, b, SAMPLE_RATE)
        assert any(s.kind == SegmentKind.ADDED for s in segments)


class TestCompareTemporal:
    def test_identical_has_high_correlation(self) -> None:
        signal = make_sine(freq=440.0, duration=2.0)
        result = compare_temporal(signal, signal, SAMPLE_RATE)
        assert result.overall_correlation > 0.99

    def test_returns_segments(self) -> None:
        signal = make_sine(freq=440.0, duration=2.0)
        result = compare_temporal(signal, signal, SAMPLE_RATE)
        assert len(result.segments) > 0
