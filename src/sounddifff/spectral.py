"""Spectral analysis: frequency band energy comparison."""

from __future__ import annotations

import numpy as np

from sounddifff.types import SpectralBand, SpectralComparison

# Default frequency bands
DEFAULT_BANDS: list[tuple[str, float, float]] = [
    ("Low", 20.0, 250.0),
    ("Mid", 250.0, 4000.0),
    ("High", 4000.0, 20000.0),
]


def compute_band_energy(
    data: np.ndarray,
    sample_rate: int,
    bands: list[tuple[str, float, float]] | None = None,
) -> list[tuple[str, float, float, float]]:
    """Compute average energy per frequency band.

    Args:
        data: Audio signal, shape (frames, channels).
        sample_rate: Sample rate in Hz.
        bands: List of (name, low_hz, high_hz) tuples. Defaults to low/mid/high.

    Returns:
        List of (name, low_hz, high_hz, energy_db) tuples.
    """
    if bands is None:
        bands = DEFAULT_BANDS

    # Mix to mono for spectral analysis
    mono = np.mean(data, axis=1)

    # Compute FFT
    n_fft = len(mono)
    spectrum = np.fft.rfft(mono)
    magnitudes = np.abs(spectrum) / n_fft
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)

    results: list[tuple[str, float, float, float]] = []
    for name, low_hz, high_hz in bands:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        band_magnitudes = magnitudes[mask]

        if len(band_magnitudes) == 0:
            energy_db = -np.inf
        else:
            rms = np.sqrt(np.mean(band_magnitudes**2))
            energy_db = 20 * np.log10(rms) if rms > 0 else -np.inf

        results.append((name, low_hz, high_hz, float(energy_db)))

    return results


def compare_spectral(
    data_a: np.ndarray,
    data_b: np.ndarray,
    sample_rate_a: int,
    sample_rate_b: int,
    bands: list[tuple[str, float, float]] | None = None,
) -> SpectralComparison:
    """Compare spectral energy between two audio signals.

    Args:
        data_a: First audio signal.
        data_b: Second audio signal.
        sample_rate_a: Sample rate of first signal.
        sample_rate_b: Sample rate of second signal.
        bands: Optional custom frequency bands.

    Returns:
        SpectralComparison with per-band energy deltas.
    """
    energy_a = compute_band_energy(data_a, sample_rate_a, bands)
    energy_b = compute_band_energy(data_b, sample_rate_b, bands)

    spectral_bands: list[SpectralBand] = []
    for (name, low, high, db_a), (_, _, _, db_b) in zip(energy_a, energy_b, strict=True):
        spectral_bands.append(
            SpectralBand(
                name=name,
                low_hz=low,
                high_hz=high,
                energy_db_a=round(db_a, 1),
                energy_db_b=round(db_b, 1),
            )
        )

    return SpectralComparison(bands=spectral_bands)
