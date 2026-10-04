"""Basic audio comparison example.

Usage:
    python examples/basic_comparison.py file_a.wav file_b.wav
"""

from __future__ import annotations

import sys

from sounddifff.core import diff
from sounddifff.report import render
from sounddifff.types import OutputFormat


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python basic_comparison.py <file_a> <file_b>")
        sys.exit(1)

    result = diff(sys.argv[1], sys.argv[2])

    # Print terminal output
    print(render(result, OutputFormat.TERMINAL))

    # Access specific values programmatically
    print(f"\nLUFS delta: {result.loudness.lufs_delta:+.1f} dB")
    print(f"Overall correlation: {result.temporal.overall_correlation:.3f}")
    print(f"Clipping events: {len(result.detection.clips)}")


if __name__ == "__main__":
    main()
