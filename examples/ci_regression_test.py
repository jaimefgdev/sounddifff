"""Example: use sounddifff in a CI pipeline for audio regression testing.

Usage:
    python examples/ci_regression_test.py reference.wav output.wav

Exit codes:
    0: All thresholds passed
    1: One or more thresholds exceeded
"""

from __future__ import annotations

import sys

from sounddifff.core import diff


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python ci_regression_test.py <reference> <output>")
        sys.exit(1)

    result = diff(sys.argv[1], sys.argv[2])

    # Define thresholds
    max_lufs_delta = 0.5
    max_peak_delta = 0.3
    min_correlation = 0.95

    failures: list[str] = []

    if abs(result.loudness.lufs_delta) > max_lufs_delta:
        failures.append(
            f"LUFS delta {result.loudness.lufs_delta:+.1f} dB exceeds threshold {max_lufs_delta}"
        )

    if abs(result.loudness.peak_delta) > max_peak_delta:
        failures.append(
            f"Peak delta {result.loudness.peak_delta:+.1f} dB exceeds threshold {max_peak_delta}"
        )

    if result.temporal.overall_correlation < min_correlation:
        failures.append(
            f"Correlation {result.temporal.overall_correlation:.3f} "
            f"below threshold {min_correlation}"
        )

    if result.detection.clips:
        failures.append(f"Clipping detected: {len(result.detection.clips)} events")

    if failures:
        print("FAIL: Audio regression test failed")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("PASS: Audio matches reference within thresholds")
        sys.exit(0)


if __name__ == "__main__":
    main()
