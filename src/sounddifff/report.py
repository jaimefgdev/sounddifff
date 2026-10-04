"""Output formatting: terminal, JSON, and HTML reports."""

from __future__ import annotations

import io
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from sounddifff import __version__
from sounddifff.formats import format_channels, format_duration
from sounddifff.types import DiffResult, OutputFormat, SegmentKind

# Long files can clip thousands of times; reports list the first ones and count the rest.
MAX_LISTED_ISSUES = 20


def render(
    result: DiffResult,
    fmt: OutputFormat,
    output_path: str | None = None,
    no_color: bool = False,
) -> str:
    """Render a DiffResult in the specified format.

    Args:
        result: The comparison result to render.
        fmt: Output format (terminal, json, html).
        output_path: Optional path to write the output file (for HTML).
        no_color: Disable colored terminal output.

    Returns:
        The rendered output as a string.
    """
    if fmt == OutputFormat.JSON:
        return render_json(result)
    elif fmt == OutputFormat.HTML:
        html = render_html(result)
        if output_path:
            Path(output_path).write_text(html)
        return html
    else:
        return render_terminal(result, no_color=no_color)


def render_terminal(result: DiffResult, no_color: bool = False) -> str:
    """Render a colored terminal report using rich."""
    console = Console(record=True, width=90, file=io.StringIO(), no_color=no_color)
    meta = result.metadata

    file_a = Path(meta.file_a.path).name
    file_b = Path(meta.file_b.path).name

    console.print()
    console.print(f"[bold]sounddifff:[/bold] {file_a} vs {file_b}")
    console.print()

    # Warnings
    for warning in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")
    if result.warnings:
        console.print()

    # Metadata
    _print_metadata_section(console, meta)
    console.print()

    # Loudness
    _print_loudness_section(console, result)
    console.print()

    # Spectral
    _print_spectral_section(console, result)
    console.print()

    # Segments
    _print_segments_section(console, result)
    console.print()

    # Issues
    _print_issues_section(console, result)

    return console.export_text()


def _print_metadata_section(console: Console, meta: Any) -> None:
    """Print the metadata comparison section."""
    dur_a = format_duration(meta.file_a.duration)
    dur_b = format_duration(meta.file_b.duration)
    dur_note = "(no change)" if meta.same_duration else f"({meta.duration_delta:+.3f}s)"

    sr_a = f"{meta.file_a.sample_rate} Hz"
    sr_b = f"{meta.file_b.sample_rate} Hz"
    sr_note = "(no change)" if meta.same_sample_rate else "(MISMATCH)"

    ch_a = format_channels(meta.file_a.channels)
    ch_b = format_channels(meta.file_b.channels)
    ch_note = "(no change)" if meta.same_channels else "(MISMATCH)"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(width=12)
    table.add_column(width=12, justify="right")
    table.add_column(width=3, justify="center")
    table.add_column(width=12)
    table.add_column(width=16)

    table.add_row("Duration", dur_a, "->", dur_b, dur_note)
    table.add_row("Sample Rate", sr_a, "->", sr_b, sr_note)
    table.add_row("Channels", ch_a, "->", ch_b, ch_note)

    console.print(table)


def _print_loudness_section(console: Console, result: DiffResult) -> None:
    """Print the loudness comparison section."""
    loud = result.loudness
    console.print("[bold]Loudness (integrated)[/bold]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(width=14)
    table.add_column(width=10, justify="right")
    table.add_column(width=3, justify="center")
    table.add_column(width=10, justify="right")
    table.add_column(width=14)

    delta_color = "red" if loud.lufs_delta > 0 else "green" if loud.lufs_delta < 0 else "white"
    table.add_row(
        "  LUFS",
        f"{loud.file_a.lufs:.1f}",
        "->",
        f"{loud.file_b.lufs:.1f}",
        f"[{delta_color}]({loud.lufs_delta:+.1f} dB)[/{delta_color}]",
    )

    peak_color = "red" if loud.peak_delta > 0 else "green" if loud.peak_delta < 0 else "white"
    table.add_row(
        "  Peak dBTP",
        f"{loud.file_a.true_peak_dbtp:.1f}",
        "->",
        f"{loud.file_b.true_peak_dbtp:.1f}",
        f"[{peak_color}]({loud.peak_delta:+.1f} dB)[/{peak_color}]",
    )

    lra_color = "yellow" if abs(loud.lra_delta) > 2 else "white"
    table.add_row(
        "  LRA",
        f"{loud.file_a.loudness_range:.1f}",
        "->",
        f"{loud.file_b.loudness_range:.1f}",
        f"[{lra_color}]({loud.lra_delta:+.1f} LU)[/{lra_color}]",
    )

    console.print(table)


def _print_spectral_section(console: Console, result: DiffResult) -> None:
    """Print the spectral comparison section."""
    console.print("[bold]Spectral[/bold]")

    for band in result.spectral.bands:
        hz_label = _format_hz_range(band.low_hz, band.high_hz)
        delta = band.delta_db
        color = "red" if delta > 1 else "green" if delta < -1 else "white"
        console.print(f"  {band.name:<6} ({hz_label})  [{color}]{delta:+.1f} dB avg[/{color}]")


def _print_segments_section(console: Console, result: DiffResult) -> None:
    """Print the segment comparison section."""
    console.print("[bold]Segments[/bold]")

    for seg in result.temporal.segments:
        start = format_duration(seg.start_time)
        end = format_duration(seg.end_time)
        time_range = f"  {start}-{end}"

        if seg.kind == SegmentKind.SIMILAR:
            corr_str = f"(correlation: {seg.correlation:.2f})" if seg.correlation else ""
            shift_str = f", shifted {seg.time_shift:+.1f}s" if seg.time_shift else ""
            console.print(f"{time_range}  [green]similar[/green] {corr_str}{shift_str}")
        elif seg.kind == SegmentKind.ADDED:
            dur = seg.duration
            console.print(f"{time_range}  [cyan]ADDED[/cyan] (new content, {dur:.1f}s)")
        elif seg.kind == SegmentKind.REMOVED:
            dur = seg.duration
            console.print(f"{time_range}  [red]REMOVED[/red] ({dur:.1f}s)")
        elif seg.kind == SegmentKind.CHANGED:
            corr_str = f"(correlation: {seg.correlation:.2f})" if seg.correlation else ""
            console.print(f"{time_range}  [yellow]CHANGED[/yellow] {corr_str}")


def _print_issues_section(console: Console, result: DiffResult) -> None:
    """Print the issues section (clipping, silence)."""
    issues = result.detection
    has_issues = bool(issues.clips)

    if not has_issues:
        console.print("[green]No issues detected.[/green]")
        return

    console.print("[bold]Issues[/bold]")
    for clip in issues.clips[:MAX_LISTED_ISSUES]:
        ts = format_duration(clip.timestamp)
        ch = f"ch{clip.channel}" if clip.channel > 0 else ""
        console.print(
            f"  [red]Clipping[/red] in {clip.file_label} at {ts} "
            f"({clip.sample_count} samples) {ch}"
        )
    hidden = len(issues.clips) - MAX_LISTED_ISSUES
    if hidden > 0:
        console.print(f"  ... and {hidden} more clipping events ({len(issues.clips)} in total)")


def _format_hz_range(low: float, high: float) -> str:
    """Format a frequency range for display."""

    def fmt(hz: float) -> str:
        if hz >= 1000:
            return f"{hz / 1000:.0f}k"
        return f"{hz:.0f}"

    return f"{fmt(low)}-{fmt(high)} Hz"


def render_json(result: DiffResult) -> str:
    """Render the result as JSON."""
    data = _result_to_dict(result)
    return json.dumps(data, indent=2)


def _result_to_dict(result: DiffResult) -> dict[str, Any]:
    """Convert a DiffResult to a JSON-serializable dict."""
    d = asdict(result)
    # Convert enum values to strings
    for seg in d.get("temporal", {}).get("segments", []):
        if "kind" in seg:
            seg["kind"] = seg["kind"].value if hasattr(seg["kind"], "value") else str(seg["kind"])
    return d


def render_html(result: DiffResult) -> str:
    """Render the result as a self-contained HTML report."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        return _render_html_fallback(result)

    # The template ships inside the package, so installed copies get the same report as a source checkout.
    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "templates")), autoescape=True
    )
    template = env.get_template("report.html.j2")
    return template.render(
        result=result,
        format_duration=format_duration,
        file_a=Path(result.metadata.file_a.path).name,
        file_b=Path(result.metadata.file_b.path).name,
        version=__version__,
        max_issues=MAX_LISTED_ISSUES,
    )


def _render_html_fallback(result: DiffResult) -> str:
    """Render a minimal HTML report without jinja2 templates."""
    meta = result.metadata
    file_a = Path(meta.file_a.path).name
    file_b = Path(meta.file_b.path).name

    json_data = render_json(result)

    def _css_class(delta: float) -> str:
        return "positive" if delta > 0 else "negative"

    spectral_rows = ""
    for b in result.spectral.bands:
        hz = _format_hz_range(b.low_hz, b.high_hz)
        cls = _css_class(b.delta_db)
        spectral_rows += (
            f'<tr><td>{b.name} ({hz})</td><td class="{cls}">{b.delta_db:+.1f} dB</td></tr>'
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>sounddifff: {file_a} vs {file_b}</title>\n"
        "<style>\n"
        "body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px;"
        " margin: 2rem auto; padding: 0 1rem; background: #1a1a2e; color: #e0e0e0; }\n"
        "h1 { color: #fff; font-size: 1.5rem; }\n"
        "h2 { color: #8be9fd; font-size: 1.1rem; margin-top: 2rem; }\n"
        "table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }\n"
        "td, th { padding: 0.4rem 0.8rem; text-align: left;"
        " border-bottom: 1px solid #333; }\n"
        ".positive { color: #ff5555; }\n"
        ".negative { color: #50fa7b; }\n"
        "pre { background: #16213e; padding: 1rem; border-radius: 4px;"
        " overflow-x: auto; font-size: 0.85rem; }\n"
        "</style>\n</head>\n<body>\n"
        f"<h1>sounddifff: {file_a} vs {file_b}</h1>\n\n"
        "<h2>Loudness</h2>\n<table>\n"
        f"<tr><td>LUFS</td><td>{result.loudness.file_a.lufs:.1f}</td>"
        f"<td>{result.loudness.file_b.lufs:.1f}</td>"
        f'<td class="{_css_class(result.loudness.lufs_delta)}">'
        f"{result.loudness.lufs_delta:+.1f} dB</td></tr>\n"
        f"<tr><td>Peak dBTP</td><td>{result.loudness.file_a.true_peak_dbtp:.1f}</td>"
        f"<td>{result.loudness.file_b.true_peak_dbtp:.1f}</td>"
        f'<td class="{_css_class(result.loudness.peak_delta)}">'
        f"{result.loudness.peak_delta:+.1f} dB</td></tr>\n"
        f"<tr><td>LRA</td><td>{result.loudness.file_a.loudness_range:.1f}</td>"
        f"<td>{result.loudness.file_b.loudness_range:.1f}</td>"
        f"<td>{result.loudness.lra_delta:+.1f} LU</td></tr>\n"
        "</table>\n\n"
        "<h2>Spectral</h2>\n<table>\n"
        f"{spectral_rows}\n"
        "</table>\n\n"
        f"<h2>Raw Data (JSON)</h2>\n<pre>{json_data}</pre>\n\n"
        "</body>\n</html>"
    )
