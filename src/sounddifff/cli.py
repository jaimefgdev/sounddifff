"""CLI entry point for sounddifff."""

from __future__ import annotations

import sys

import click

from sounddifff import __version__
from sounddifff.core import diff
from sounddifff.report import render
from sounddifff.thresholds import check, parse_rules
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
    """Compare two audio files and report what changed.

    sounddifff FILE_A FILE_B

    Compares FILE_A (reference) against FILE_B (comparison) and reports
    differences in loudness, spectral content, timing, and potential issues.
    """
    try:
        rules = parse_rules(fail_if) if fail_if is not None else []
    except ValueError as e:
        raise click.BadParameter(str(e), param_hint="--fail-if") from e

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
