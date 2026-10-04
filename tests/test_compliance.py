"""Tests for `sounddifff check` (added by jaimefgdev, October 2026)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from click.testing import CliRunner

from sounddifff.cli import check_cmd
from sounddifff.compliance import PRESETS, check_file, true_peak

FIXTURES = Path(__file__).parent / "fixtures"
RATE = 48000


def _tone_at(tmp_path: Path, lufs_target: float, seconds: float = 5.0) -> Path:
    """Stereo 1 kHz tone scaled to an exact integrated loudness."""
    import pyloudnorm as pyln

    t = np.arange(int(RATE * seconds)) / RATE
    tone = 0.1 * np.sin(2 * np.pi * 1000 * t)
    data = np.column_stack([tone, tone])
    data = pyln.normalize.loudness(data, pyln.Meter(RATE).integrated_loudness(data), lufs_target)
    path = tmp_path / f"tone_{lufs_target}.wav"
    sf.write(path, data, RATE, subtype="FLOAT")
    return path


class TestTruePeak:
    def test_finds_inter_sample_peaks(self) -> None:
        # A sine at fs/4 with a 45 degree phase: samples sit at ±0.707, the waveform peaks at 1.0.
        n = np.arange(4800)
        data = np.sin(2 * np.pi * n / 4 + np.pi / 4).reshape(-1, 1)
        sample_peak = 20 * np.log10(np.max(np.abs(data)))
        assert sample_peak == pytest.approx(-3.0, abs=0.1)
        assert true_peak(data) == pytest.approx(0.0, abs=0.3)

    def test_silence(self) -> None:
        assert true_peak(np.zeros((100, 2))) == float("-inf")


class TestCheckFile:
    def test_on_target_passes(self, tmp_path: Path) -> None:
        result = check_file(_tone_at(tmp_path, -14.0), "spotify")
        assert result.passed
        assert result.lufs == pytest.approx(-14.0, abs=0.2)

    def test_too_loud_fails_and_suggests_gain(self, tmp_path: Path) -> None:
        result = check_file(_tone_at(tmp_path, -10.0), "spotify")
        assert not result.passed
        assert [c.name for c in result.checks if not c.passed] == ["loudness"]
        assert result.gain_to_target == pytest.approx(-4.0, abs=0.2)

    def test_overrides_beat_the_preset(self, tmp_path: Path) -> None:
        path = _tone_at(tmp_path, -10.0)
        assert check_file(path, "spotify", lufs=-10.0).passed

    def test_clipping_fails(self) -> None:
        result = check_file(FIXTURES / "clipped.wav", "spotify")
        failed = {c.name for c in result.checks if not c.passed}
        assert {"clipping", "true peak"} <= failed

    def test_unknown_preset(self) -> None:
        with pytest.raises(ValueError, match="unknown preset"):
            check_file(FIXTURES / "clean.wav", "tiktok")

    def test_presets_have_sane_values(self) -> None:
        for p in PRESETS.values():
            assert -30 < p.lufs < -5 and 0 < p.tolerance <= 2 and p.max_true_peak <= 0


class TestCheckCLI:
    def test_pass_exit_0(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(
            check_cmd, [str(_tone_at(tmp_path, -23.0)), "--preset", "ebu-r128"]
        )
        assert result.exit_code == 0, result.output
        assert "Result: PASS" in result.output

    def test_fail_exit_3_json(self) -> None:
        result = CliRunner().invoke(check_cmd, [str(FIXTURES / "clipped.wav"), "--format", "json"])
        assert result.exit_code == 3
        data = json.loads(result.output)
        assert data["passed"] is False and data["preset"] == "spotify"
