"""Example: batch compare matching files across two directories.

Usage:
    python examples/batch_compare.py dir_a/ dir_b/
"""

from __future__ import annotations

import sys
from pathlib import Path

from sounddifff.core import diff
from sounddifff.formats import NATIVE_FORMATS


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python batch_compare.py <dir_a> <dir_b>")
        sys.exit(1)

    dir_a = Path(sys.argv[1])
    dir_b = Path(sys.argv[2])

    if not dir_a.is_dir() or not dir_b.is_dir():
        print("Both arguments must be directories")
        sys.exit(1)

    files_a = {f.name for f in dir_a.iterdir() if f.suffix.lower() in NATIVE_FORMATS}
    files_b = {f.name for f in dir_b.iterdir() if f.suffix.lower() in NATIVE_FORMATS}

    common = sorted(files_a & files_b)
    only_a = sorted(files_a - files_b)
    only_b = sorted(files_b - files_a)

    if only_a:
        print(f"Only in {dir_a}: {', '.join(only_a)}")
    if only_b:
        print(f"Only in {dir_b}: {', '.join(only_b)}")

    for name in common:
        print(f"\n{'=' * 60}")
        print(f"Comparing: {name}")
        print("=" * 60)

        result = diff(dir_a / name, dir_b / name)
        print(f"  LUFS:        {result.loudness.lufs_delta:+.1f} dB")
        print(f"  Peak:        {result.loudness.peak_delta:+.1f} dB")
        print(f"  Correlation: {result.temporal.overall_correlation:.3f}")
        print(f"  Clips:       {len(result.detection.clips)}")


if __name__ == "__main__":
    main()
