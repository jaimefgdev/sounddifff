"""Shared fixtures for sounddifff tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_RATE = 48000


@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures() -> None:
    """Ensure test fixtures exist by running the generator."""
    if not FIXTURES_DIR.exists() or not list(FIXTURES_DIR.glob("*.wav")):
        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "scripts/generate_test_audio.py"],
            check=True,
            cwd=Path(__file__).parent.parent,
        )


@pytest.fixture
def sine_pair() -> tuple[np.ndarray, np.ndarray]:
    """Two identical sine waves."""
    data_a, _ = sf.read(str(FIXTURES_DIR / "sine_a.wav"), dtype="float64", always_2d=True)
    data_b, _ = sf.read(str(FIXTURES_DIR / "sine_b.wav"), dtype="float64", always_2d=True)
    return data_a, data_b


@pytest.fixture
def loudness_pair() -> tuple[np.ndarray, np.ndarray]:
    """Quiet and loud signals."""
    quiet, _ = sf.read(str(FIXTURES_DIR / "quiet.wav"), dtype="float64", always_2d=True)
    loud, _ = sf.read(str(FIXTURES_DIR / "loud.wav"), dtype="float64", always_2d=True)
    return quiet, loud


@pytest.fixture
def clipping_pair() -> tuple[np.ndarray, np.ndarray]:
    """Clean and clipped signals."""
    clean, _ = sf.read(str(FIXTURES_DIR / "clean.wav"), dtype="float64", always_2d=True)
    clipped, _ = sf.read(str(FIXTURES_DIR / "clipped.wav"), dtype="float64", always_2d=True)
    return clean, clipped


@pytest.fixture
def silence_pair() -> tuple[np.ndarray, np.ndarray]:
    """Continuous and silence-inserted signals."""
    continuous, _ = sf.read(str(FIXTURES_DIR / "continuous.wav"), dtype="float64", always_2d=True)
    with_silence, _ = sf.read(
        str(FIXTURES_DIR / "with_silence.wav"), dtype="float64", always_2d=True
    )
    return continuous, with_silence


@pytest.fixture
def length_pair() -> tuple[np.ndarray, np.ndarray]:
    """Short and long signals."""
    short, _ = sf.read(str(FIXTURES_DIR / "short.wav"), dtype="float64", always_2d=True)
    long, _ = sf.read(str(FIXTURES_DIR / "long.wav"), dtype="float64", always_2d=True)
    return short, long


def make_sine(
    freq: float = 440.0,
    duration: float = 1.0,
    amplitude: float = 0.5,
    sample_rate: int = SAMPLE_RATE,
    channels: int = 2,
) -> np.ndarray:
    """Generate a sine wave for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    mono = amplitude * np.sin(2 * np.pi * freq * t)
    if channels == 1:
        return mono.reshape(-1, 1)
    return np.column_stack([mono] * channels)
