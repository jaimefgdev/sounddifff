"""Folder comparison: ``sounddifff dir_a/ dir_b/`` pairs files by relative path and diffs each pair.

Added by Jaime Fernández González (jaimefgdev) in October 2026.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from sounddifff.core import diff
from sounddifff.thresholds import check

if TYPE_CHECKING:
    from sounddifff.thresholds import Rule
    from sounddifff.types import DiffResult

AUDIO_EXTENSIONS = {".wav", ".flac", ".ogg", ".aiff", ".aif", ".mp3", ".m4a", ".aac"}


@dataclass
class PairResult:
    name: str
    result: DiffResult | None = None
    error: str | None = None
    failures: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.error:
            return "error"
        return "fail" if self.failures else "ok"


@dataclass
class BatchResult:
    pairs: list[PairResult]
    only_in_a: list[str]
    only_in_b: list[str]

    @property
    def failed(self) -> bool:
        return any(p.status != "ok" for p in self.pairs)


def _audio_files(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    }


def compare_dirs(
    dir_a: str | Path, dir_b: str | Path, rules: list[Rule] | None = None
) -> BatchResult:
    files_a, files_b = _audio_files(Path(dir_a)), _audio_files(Path(dir_b))
    pairs: list[PairResult] = []
    for name in sorted(files_a.keys() & files_b.keys()):
        pair = PairResult(name)
        try:
            pair.result = diff(files_a[name], files_b[name])
            pair.failures = check(pair.result, rules or [])
        except (ValueError, RuntimeError, OSError) as e:
            pair.error = str(e)
        pairs.append(pair)
    return BatchResult(
        pairs=pairs,
        only_in_a=sorted(files_a.keys() - files_b.keys()),
        only_in_b=sorted(files_b.keys() - files_a.keys()),
    )


def render_batch_terminal(batch: BatchResult) -> str:
    lines = [f"sounddifff: {len(batch.pairs)} file pair(s) compared", ""]
    header = f"  {'status':<6}  {'file':<40} {'dLUFS':>7} {'dPeak':>7} {'corr':>6}"
    lines += [header, "  " + "-" * (len(header) - 2)]
    for p in batch.pairs:
        if p.result is None:
            lines.append(f"  {'ERROR':<6}  {p.name:<40} {p.error}")
            continue
        r = p.result
        lines.append(
            f"  {p.status.upper():<6}  {p.name:<40} {r.loudness.lufs_delta:>+7.1f} "
            f"{r.loudness.peak_delta:>+7.1f} {r.temporal.overall_correlation:>6.3f}"
        )
        lines += [f"          - {f}" for f in p.failures]
    if batch.only_in_a:
        lines += ["", "  Only in the first folder:"] + [f"    {n}" for n in batch.only_in_a]
    if batch.only_in_b:
        lines += ["", "  Only in the second folder:"] + [f"    {n}" for n in batch.only_in_b]
    return "\n".join(lines)


def render_batch_json(batch: BatchResult) -> str:
    from sounddifff.report import render_json

    pairs = []
    for p in batch.pairs:
        item: dict[str, object] = {"file": p.name, "status": p.status, "failures": p.failures}
        if p.result is not None:
            item["diff"] = json.loads(render_json(p.result))
        if p.error:
            item["error"] = p.error
        pairs.append(item)
    data = {"pairs": pairs, "only_in_a": batch.only_in_a, "only_in_b": batch.only_in_b}
    return json.dumps(data, indent=2, ensure_ascii=False)
