"""Single-file loudness compliance against delivery targets (``sounddifff check``).

Added by Jaime Fernández González (jaimefgdev) in October 2026.

Each preset is an integrated-loudness target with a tolerance and a true-peak ceiling. True peak is measured
as in ITU-R BS.1770-4: the signal is oversampled 4x before taking the peak, because inter-sample peaks can clip
after encoding even when no sample reaches 0 dBFS.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from sounddifff.detection import detect_clipping
from sounddifff.formats import load_audio
from sounddifff.loudness import measure_loudness


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    lufs: float
    tolerance: float
    max_true_peak: float


PRESETS: dict[str, Preset] = {
    p.name: p
    for p in (
        Preset("spotify", "Spotify (music)", -14.0, 1.0, -1.0),
        Preset("youtube", "YouTube", -14.0, 1.0, -1.0),
        Preset("apple-music", "Apple Music", -16.0, 1.0, -1.0),
        Preset("podcast", "Podcasts (Apple Podcasts, Spotify for Podcasters)", -16.0, 1.0, -1.0),
        Preset("ebu-r128", "EBU R 128 broadcast (Europe)", -23.0, 0.5, -1.0),
        Preset("atsc-a85", "ATSC A/85 broadcast (United States)", -24.0, 2.0, -2.0),
    )
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    measured: str
    target: str


@dataclass(frozen=True)
class ComplianceResult:
    path: str
    preset: str
    target_lufs: float
    lufs: float
    true_peak_dbtp: float
    loudness_range: float
    clipping_events: int
    checks: list[Check]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def gain_to_target(self) -> float:
        """Gain (dB) that would bring the file to the preset's loudness target."""
        return round(self.target_lufs - self.lufs, 1)


def true_peak(data: np.ndarray, oversample: int = 4) -> float:
    """True peak in dBTP: the highest absolute value after oversampling (ITU-R BS.1770-4, Annex 2)."""
    if data.size == 0:
        return float("-inf")
    up = resample_poly(np.asarray(data, dtype=np.float64), oversample, 1, axis=0)
    peak = float(np.max(np.abs(up)))
    return round(20 * np.log10(peak), 1) if peak > 0 else float("-inf")


def check_file(
    path: str | Path,
    preset: str = "spotify",
    lufs: float | None = None,
    tolerance: float | None = None,
    max_true_peak: float | None = None,
) -> ComplianceResult:
    """Measure a file and check it against a preset; explicit values override the preset's."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}; available: {', '.join(PRESETS)}")
    p = PRESETS[preset]
    target = p.lufs if lufs is None else lufs
    tol = p.tolerance if tolerance is None else tolerance
    ceiling = p.max_true_peak if max_true_peak is None else max_true_peak

    data, meta = load_audio(path)
    loud = measure_loudness(data, meta.sample_rate)
    tp = true_peak(data)
    clips = detect_clipping(data, meta.sample_rate, Path(path).name)

    checks = [
        Check(
            "loudness",
            bool(abs(loud.lufs - target) <= tol),
            f"{loud.lufs:.1f} LUFS",
            f"{target:.1f} +/- {tol:g} LUFS",
        ),
        Check("true peak", bool(tp <= ceiling), f"{tp:.1f} dBTP", f"<= {ceiling:.1f} dBTP"),
        Check("clipping", not clips, f"{len(clips)} event(s)", "none"),
    ]
    return ComplianceResult(
        path=str(path),
        preset=preset,
        target_lufs=target,
        lufs=float(loud.lufs),
        true_peak_dbtp=float(tp),
        loudness_range=float(loud.loudness_range),
        clipping_events=len(clips),
        checks=checks,
    )


def render_check_terminal(result: ComplianceResult) -> str:
    p = PRESETS[result.preset]
    lines = [f"sounddifff check: {Path(result.path).name} against {p.description}", ""]
    for c in result.checks:
        mark = "PASS" if c.passed else "FAIL"
        lines.append(f"  {mark}  {c.name:<10} {c.measured:<14} target {c.target}")
    lines.append(f"\n  Loudness range: {result.loudness_range:.1f} LU")
    if not result.checks[0].passed:
        lines.append(f"  Gain to reach the target: {result.gain_to_target:+.1f} dB")
    lines.append(f"\n  Result: {'PASS' if result.passed else 'FAIL'}")
    return "\n".join(lines)


def render_check_json(result: ComplianceResult) -> str:
    data = asdict(result)
    data["passed"] = result.passed
    data["gain_to_target"] = result.gain_to_target
    return json.dumps(data, indent=2, ensure_ascii=False)
