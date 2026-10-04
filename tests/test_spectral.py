"""Tests for spectral analysis."""

from __future__ import annotations

import numpy as np

from sounddifff.spectral import compare_spectral, compute_band_energy
from tests.conftest import SAMPLE_RATE, make_sine


class TestComputeBandEnergy:
    def test_440hz_has_energy_in_mid_band(self) -> None:
        signal = make_sine(freq=440.0, amplitude=0.5)
        bands = compute_band_energy(signal, SAMPLE_RATE)

        # 440 Hz falls in the mid band (250-4000 Hz)
        mid = next(b for b in bands if b[0] == "Mid")
        low = next(b for b in bands if b[0] == "Low")
        high = next(b for b in bands if b[0] == "High")

        assert mid[3] > low[3]  # More energy in mid than low
        assert mid[3] > high[3]  # More energy in mid than high

    def test_100hz_has_energy_in_low_band(self) -> None:
        signal = make_sine(freq=100.0, amplitude=0.5)
        bands = compute_band_energy(signal, SAMPLE_RATE)

        low = next(b for b in bands if b[0] == "Low")
        mid = next(b for b in bands if b[0] == "Mid")

        assert low[3] > mid[3]

    def test_10khz_has_energy_in_high_band(self) -> None:
        signal = make_sine(freq=10000.0, amplitude=0.5)
        bands = compute_band_energy(signal, SAMPLE_RATE)

        high = next(b for b in bands if b[0] == "High")
        low = next(b for b in bands if b[0] == "Low")

        assert high[3] > low[3]

    def test_custom_bands(self) -> None:
        signal = make_sine(freq=1000.0, amplitude=0.5)
        custom = [("Sub", 20.0, 80.0), ("Full", 80.0, 20000.0)]
        bands = compute_band_energy(signal, SAMPLE_RATE, bands=custom)
        assert len(bands) == 2
        assert bands[0][0] == "Sub"
        assert bands[1][0] == "Full"

    def test_silence_has_very_low_energy(self) -> None:
        silence = np.zeros((SAMPLE_RATE, 2))
        bands = compute_band_energy(silence, SAMPLE_RATE)
        for _, _, _, energy in bands:
            assert energy < -100 or energy == float("-inf")


class TestCompareSpectral:
    def test_identical_signals_have_zero_delta(self) -> None:
        signal = make_sine(freq=440.0, amplitude=0.5)
        result = compare_spectral(signal, signal, SAMPLE_RATE, SAMPLE_RATE)

        for band in result.bands:
            assert abs(band.delta_db) < 0.1

    def test_added_highs_show_positive_delta(self) -> None:
        base = make_sine(freq=440.0, amplitude=0.5, duration=2.0)
        with_highs = base + make_sine(freq=10000.0, amplitude=0.3, duration=2.0)

        result = compare_spectral(base, with_highs, SAMPLE_RATE, SAMPLE_RATE)
        high = next(b for b in result.bands if b.name == "High")
        assert high.delta_db > 0
