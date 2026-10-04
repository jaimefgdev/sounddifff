"""Tests for loudness analysis."""

from __future__ import annotations

import numpy as np

from sounddifff.loudness import compare_loudness, measure_loudness
from tests.conftest import SAMPLE_RATE, make_sine


class TestMeasureLoudness:
    def test_louder_signal_has_higher_lufs(self) -> None:
        quiet = make_sine(amplitude=0.1)
        loud = make_sine(amplitude=0.8)

        result_quiet = measure_loudness(quiet, SAMPLE_RATE)
        result_loud = measure_loudness(loud, SAMPLE_RATE)

        assert result_loud.lufs > result_quiet.lufs

    def test_louder_signal_has_higher_peak(self) -> None:
        quiet = make_sine(amplitude=0.1)
        loud = make_sine(amplitude=0.8)

        result_quiet = measure_loudness(quiet, SAMPLE_RATE)
        result_loud = measure_loudness(loud, SAMPLE_RATE)

        assert result_loud.true_peak_dbtp > result_quiet.true_peak_dbtp

    def test_identical_signals_have_same_lufs(self) -> None:
        signal = make_sine(amplitude=0.5)
        r1 = measure_loudness(signal, SAMPLE_RATE)
        r2 = measure_loudness(signal, SAMPLE_RATE)
        assert r1.lufs == r2.lufs

    def test_silence_has_negative_inf_lufs(self) -> None:
        silence = np.zeros((SAMPLE_RATE, 2))
        result = measure_loudness(silence, SAMPLE_RATE)
        assert result.lufs == float("-inf") or result.lufs < -70

    def test_peak_never_exceeds_zero(self) -> None:
        signal = make_sine(amplitude=0.99)
        result = measure_loudness(signal, SAMPLE_RATE)
        assert result.true_peak_dbtp <= 0.0


class TestCompareLoudness:
    def test_delta_is_positive_when_b_louder(self) -> None:
        quiet = make_sine(amplitude=0.1)
        loud = make_sine(amplitude=0.8)

        comparison = compare_loudness(quiet, loud, SAMPLE_RATE, SAMPLE_RATE)
        assert comparison.lufs_delta > 0

    def test_delta_is_zero_for_identical(self) -> None:
        signal = make_sine(amplitude=0.5)
        comparison = compare_loudness(signal, signal, SAMPLE_RATE, SAMPLE_RATE)
        assert comparison.lufs_delta == 0.0

    def test_delta_is_negative_when_b_quieter(self) -> None:
        loud = make_sine(amplitude=0.8)
        quiet = make_sine(amplitude=0.1)

        comparison = compare_loudness(loud, quiet, SAMPLE_RATE, SAMPLE_RATE)
        assert comparison.lufs_delta < 0
