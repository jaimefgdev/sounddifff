"""CLI entry point for sounddifff."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from sounddifff import __version__
from sounddifff.batch import compare_dirs, render_batch_json, render_batch_terminal
from sounddifff.compliance import PRESETS, check_file, render_check_json, render_check_terminal
from sounddifff.core import diff
from sounddifff.report import render
from sounddifff.thresholds import Rule, check, parse_rules
from sounddifff.types import OutputFormat


@click.command()
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json", "html"]),
    default="terminal",
    help="Output format.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(),
    default=None,
    help="Write output to a file (useful with --format html).",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show additional detail.",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="Disable colored terminal output.",
)
@click.option(
    "--fail-if",
    "fail_if",
    default=None,
    metavar="RULES",
    help=(
        "Exit with code 3 if any rule fails, e.g. 'lufs>1,peak>0.5,clipping'. "
        "Rules: lufs, peak, lra, band, duration (>N), correlation (<N), clipping, silence, format."
    ),
)
@click.version_option(version=__version__, prog_name="sounddifff")
def main(
    file_a: str,
    file_b: str,
    output_format: str,
    output_path: str | None,
    verbose: bool,
    no_color: bool,
    fail_if: str | None,
) -> None:
    """Compare two audio files (or two folders) and report what changed.

    sounddifff FILE_A FILE_B

    Compares FILE_A (reference) against FILE_B (comparison) and reports
    differences in loudness, spectral content, timing, and potential issues.
    With two folders, files are paired by relative path and compared one by one.

    To check a single file against a delivery target, use: sounddifff check FILE --preset spotify
    """
    try:
        rules = parse_rules(fail_if) if fail_if is not None else []
    except ValueError as e:
        raise click.BadParameter(str(e), param_hint="--fail-if") from e

    dir_a, dir_b = Path(file_a).is_dir(), Path(file_b).is_dir()
    if dir_a != dir_b:
        raise click.UsageError("compare two files or two folders, not a file with a folder")
    if dir_a:
        _compare_folders(file_a, file_b, output_format, output_path, rules)
        return

    try:
        result = diff(file_a, file_b)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    fmt = OutputFormat(output_format)
    output = render(result, fmt, output_path, no_color=no_color)

    if output_path and fmt == OutputFormat.HTML:
        click.echo(f"Report written to {output_path}")
    else:
        click.echo(output)

    failures = check(result, rules)
    for failure in failures:
        click.echo(f"FAIL {failure}", err=True)
    if failures:
        sys.exit(3)


def _compare_folders(
    dir_a: str, dir_b: str, output_format: str, output_path: str | None, rules: list[Rule]
) -> None:
    if output_format == "html":
        raise click.UsageError("folder comparison supports --format terminal or json")
    batch = compare_dirs(dir_a, dir_b, rules)
    output = render_batch_json(batch) if output_format == "json" else render_batch_terminal(batch)
    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
        click.echo(f"Report written to {output_path}")
    else:
        click.echo(output)
    if not batch.pairs:
        click.echo("Error: no audio files with the same relative path in both folders", err=True)
        sys.exit(1)
    if batch.failed:
        sys.exit(3)


@click.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--preset",
    type=click.Choice(sorted(PRESETS)),
    default="spotify",
    show_default=True,
    help="Delivery target.",
)
@click.option(
    "--lufs", type=float, default=None, help="Override the integrated loudness target (LUFS)."
)
@click.option("--tolerance", type=float, default=None, help="Override the allowed deviation (LU).")
@click.option(
    "--max-peak", type=float, default=None, help="Override the true-peak ceiling (dBTP)."
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format.",
)
def check_cmd(
    file: str,
    preset: str,
    lufs: float | None,
    tolerance: float | None,
    max_peak: float | None,
    output_format: str,
) -> None:
    """Check one file against a loudness delivery target.

    sounddifff check FILE --preset spotify

    Exits with code 3 if the file misses the target, so it works as a CI gate.
    """
    try:
        result = check_file(file, preset, lufs=lufs, tolerance=tolerance, max_true_peak=max_peak)
    except (ValueError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    click.echo(
        render_check_json(result) if output_format == "json" else render_check_terminal(result)
    )
    if not result.passed:
        sys.exit(3)


def entry() -> None:
    """Console entry point: ``sounddifff check ...`` or ``sounddifff A B``."""
    args = sys.argv[1:]
    if args and args[0] == "check":
        check_cmd.main(args[1:], prog_name="sounddifff check")
    else:
        main()
