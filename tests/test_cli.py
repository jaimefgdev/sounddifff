"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from sounddifff.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCLI:
    def test_basic_comparison(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(FIXTURES_DIR / "sine_a.wav"),
                str(FIXTURES_DIR / "sine_b.wav"),
            ],
        )
        assert result.exit_code == 0
        assert "sounddifff" in result.output

    def test_json_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(FIXTURES_DIR / "sine_a.wav"),
                str(FIXTURES_DIR / "sine_b.wav"),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert '"metadata"' in result.output

    def test_html_output_to_file(self, tmp_path: Path) -> None:
        output_file = tmp_path / "report.html"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(FIXTURES_DIR / "sine_a.wav"),
                str(FIXTURES_DIR / "sine_b.wav"),
                "--format",
                "html",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert "<html" in output_file.read_text()

    def test_file_not_found(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["nonexistent.wav", "also_nonexistent.wav"])
        assert result.exit_code != 0

    def test_version_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "sounddifff" in result.output

    def test_loudness_pair_shows_delta(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(FIXTURES_DIR / "quiet.wav"),
                str(FIXTURES_DIR / "loud.wav"),
            ],
        )
        assert result.exit_code == 0
        assert "LUFS" in result.output
