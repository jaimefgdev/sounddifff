"""Pass/fail rules for using sounddifff as a regression check in CI (``--fail-if``).

Added by Jaime Fernández González (jaimefgdev) in October 2026.

A rule set is a comma-separated list. Numeric rules compare the absolute change between the
reference (A) and the comparison (B); flag rules check for problems that only appear in B::

    lufs>1          integrated loudness changed by more than 1 LU
    peak>0.5        true peak changed by more than 0.5 dB
    lra>2           loudness range changed by more than 2 LU
    band>3          any spectral band changed by more than 3 dB
    duration>0.05   duration changed by more than 0.05 s
    correlation<0.9 overall waveform correlation dropped below 0.9
    clipping        B clips (anywhere)
    silence         B has more silent regions than A
    format          sample rate or channel count differ

Example: ``sounddifff ref.wav new.wav --fail-if "lufs>1,peak>0.5,clipping"``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from sounddifff.types import DiffResult

NUMERIC: dict[str, tuple[str, str, Callable[[DiffResult], float]]] = {
    # name: (operator, unit, measured value)
    "lufs": (">", "LU", lambda r: abs(r.loudness.lufs_delta)),
    "peak": (">", "dB", lambda r: abs(r.loudness.peak_delta)),
    "lra": (">", "LU", lambda r: abs(r.loudness.lra_delta)),
    "band": (">", "dB", lambda r: max((abs(b.delta_db) for b in r.spectral.bands), default=0.0)),
    "duration": (">", "s", lambda r: abs(r.metadata.duration_delta)),
    "correlation": ("<", "", lambda r: r.temporal.overall_correlation),
}


def _clipping_in_b(r: DiffResult) -> str | None:
    name_b = Path(r.metadata.file_b.path).name
    clips = [c for c in r.detection.clips if c.file_label == name_b]
    return f"{len(clips)} clipping event(s) in {name_b}" if clips else None


def _new_silence(r: DiffResult) -> str | None:
    a, b = len(r.detection.silence_regions_a), len(r.detection.silence_regions_b)
    return f"silent regions went from {a} to {b}" if b > a else None


def _format_change(r: DiffResult) -> str | None:
    m = r.metadata
    changes = []
    if not m.same_sample_rate:
        changes.append(f"sample rate {m.file_a.sample_rate} -> {m.file_b.sample_rate} Hz")
    if not m.same_channels:
        changes.append(f"channels {m.file_a.channels} -> {m.file_b.channels}")
    return ", ".join(changes) or None


FLAGS: dict[str, Callable[[DiffResult], str | None]] = {
    "clipping": _clipping_in_b,
    "silence": _new_silence,
    "format": _format_change,
}

_RULE = re.compile(r"^\s*([a-z]+)\s*(?:([<>])\s*(\d+(?:\.\d+)?))?\s*$")


@dataclass(frozen=True)
class Rule:
    name: str
    limit: float | None = None

    def __str__(self) -> str:
        if self.limit is None:
            return self.name
        return f"{self.name}{NUMERIC[self.name][0]}{self.limit:g}"


def parse_rules(text: str) -> list[Rule]:
    """Parse ``"lufs>1,clipping"`` into rules. Raises ValueError with a readable message."""
    rules: list[Rule] = []
    for chunk in filter(None, (c.strip() for c in text.split(","))):
        m = _RULE.match(chunk.lower())
        if not m:
            raise ValueError(f"invalid rule {chunk!r}: expected e.g. 'lufs>1' or 'clipping'")
        name, op, value = m.groups()
        if name in FLAGS:
            if op:
                raise ValueError(f"rule {name!r} takes no value")
            rules.append(Rule(name))
        elif name in NUMERIC:
            expected = NUMERIC[name][0]
            if op != expected:
                raise ValueError(
                    f"rule {name!r} needs a limit, written as '{name}{expected}<number>'"
                )
            rules.append(Rule(name, float(value)))
        else:
            known = ", ".join(sorted([*NUMERIC, *FLAGS]))
            raise ValueError(f"unknown rule {name!r}; available: {known}")
    if not rules:
        raise ValueError("no rules given")
    return rules


def check(result: DiffResult, rules: list[Rule]) -> list[str]:
    """Return one message per rule that fails; an empty list means the comparison passes."""
    failures: list[str] = []
    for rule in rules:
        if rule.limit is None:
            reason = FLAGS[rule.name](result)
            if reason:
                failures.append(f"{rule}: {reason}")
            continue
        op, unit, measure = NUMERIC[rule.name]
        value = measure(result)
        broken = value > rule.limit if op == ">" else value < rule.limit
        if broken:
            failures.append(f"{rule}: measured {value:.3g}{' ' + unit if unit else ''}")
    return failures
