"""Tests for --fail-if rules (added by jaimefgdev, October 2026)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner, Result

from sounddifff.cli import main
from sounddifff.core import diff
from sounddifff.thresholds import Rule, check, parse_rules

if TYPE_CHECKING:
    from sounddifff.types import DiffResult

FIXTURES = Path(__file__).parent / "fixtures"


def _diff(a: str, b: str) -> DiffResult:
    return diff(FIXTURES / f"{a}.wav", FIXTURES / f"{b}.wav")


class TestParse:
    def test_numeric_and_flag_rules(self) -> None:
        assert parse_rules("lufs>1, peak>0.5,clipping") == [
            Rule("lufs", 1.0),
            Rule("peak", 0.5),
            Rule("clipping"),
        ]

    def test_correlation_uses_less_than(self) -> None:
        assert parse_rules("correlation<0.9") == [Rule("correlation", 0.9)]

    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("loudness>1", "unknown rule"),
            ("lufs", "needs a limit"),
            ("lufs<1", "needs a limit"),
            ("clipping>1", "takes no value"),
            ("lufs>abc", "invalid rule"),
            (" , ", "no rules"),
        ],
    )
    def test_invalid_rules(self, text: str, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            parse_rules(text)

    def test_rule_text_round_trips(self) -> None:
        assert [str(r) for r in parse_rules("lufs>1,correlation<0.9,silence")] == [
            "lufs>1",
            "correlation<0.9",
            "silence",
        ]


class TestCheck:
    def test_identical_files_pass_every_rule(self) -> None:
        rules = parse_rules(
            "lufs>0.1,peak>0.1,lra>0.1,band>0.1,duration>0.01,correlation<0.99,clipping,silence,format"
        )
        assert check(_diff("clean", "clean"), rules) == []

    def test_loudness_change(self) -> None:
        result = _diff("quiet", "loud")
        assert check(result, parse_rules("lufs>20")) == []
        failures = check(result, parse_rules("lufs>1"))
        assert len(failures) == 1 and failures[0].startswith("lufs>1: measured")

    def test_clipping_only_counts_the_comparison_file(self) -> None:
        assert check(_diff("clean", "clipped"), [Rule("clipping")])[0].startswith("clipping:")
        assert check(_diff("clipped", "clean"), [Rule("clipping")]) == []

    def test_new_silence(self) -> None:
        assert check(_diff("continuous", "with_silence"), [Rule("silence")])
        assert check(_diff("with_silence", "continuous"), [Rule("silence")]) == []

    def test_format_change(self) -> None:
        assert "channels" in check(_diff("sine_a", "mono"), [Rule("format")])[0]

    def test_correlation_drop(self) -> None:
        assert check(_diff("continuous", "with_silence"), parse_rules("correlation<0.95"))


class TestCLI:
    def _run(self, a: str, b: str, *extra: str) -> Result:
        return CliRunner().invoke(
            main, [str(FIXTURES / f"{a}.wav"), str(FIXTURES / f"{b}.wav"), *extra]
        )

    def test_passes_with_exit_code_0(self) -> None:
        assert self._run("sine_a", "sine_b", "--fail-if", "lufs>1,clipping").exit_code == 0

    def test_fails_with_exit_code_3_and_reports_why(self) -> None:
        result = self._run("clean", "clipped", "--fail-if", "lufs>1,clipping")
        assert result.exit_code == 3
        assert "FAIL lufs>1" in result.output and "FAIL clipping" in result.output

    def test_report_is_still_printed(self) -> None:
        result = self._run("clean", "clipped", "--fail-if", "clipping", "--format", "json")
        assert '"metadata"' in result.output

    def test_bad_rule_is_a_usage_error(self) -> None:
        result = self._run("clean", "clean", "--fail-if", "volume>1")
        assert result.exit_code == 2
        assert "unknown rule" in result.output
