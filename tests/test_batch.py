"""Tests for folder comparison (added by jaimefgdev, October 2026)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from click.testing import CliRunner

from sounddifff.batch import compare_dirs
from sounddifff.cli import main
from sounddifff.thresholds import parse_rules

FIXTURES = Path(__file__).parent / "fixtures"


def _folders(tmp_path: Path) -> tuple[Path, Path]:
    a, b = tmp_path / "a", tmp_path / "b"
    (a / "sub").mkdir(parents=True)
    (b / "sub").mkdir(parents=True)
    shutil.copy(FIXTURES / "clean.wav", a / "same.wav")
    shutil.copy(FIXTURES / "clean.wav", b / "same.wav")
    shutil.copy(FIXTURES / "quiet.wav", a / "sub" / "voice.wav")
    shutil.copy(FIXTURES / "loud.wav", b / "sub" / "voice.wav")
    shutil.copy(FIXTURES / "mono.wav", a / "removed.wav")
    shutil.copy(FIXTURES / "mono.wav", b / "added.wav")
    (a / "notes.txt").write_text("not audio")
    return a, b


def test_pairs_by_relative_path(tmp_path: Path) -> None:
    a, b = _folders(tmp_path)
    batch = compare_dirs(a, b, parse_rules("lufs>1"))
    assert [p.name for p in batch.pairs] == ["same.wav", "sub/voice.wav"]
    assert [p.status for p in batch.pairs] == ["ok", "fail"]
    assert batch.only_in_a == ["removed.wav"] and batch.only_in_b == ["added.wav"]
    assert batch.failed


def test_without_rules_everything_is_ok(tmp_path: Path) -> None:
    a, b = _folders(tmp_path)
    assert not compare_dirs(a, b).failed


def test_cli_exit_codes_and_json(tmp_path: Path) -> None:
    a, b = _folders(tmp_path)
    runner = CliRunner()
    assert runner.invoke(main, [str(a), str(b)]).exit_code == 0
    result = runner.invoke(main, [str(a), str(b), "--fail-if", "lufs>1", "--format", "json"])
    assert result.exit_code == 3
    data = json.loads(result.output)
    assert {p["file"]: p["status"] for p in data["pairs"]} == {
        "same.wav": "ok",
        "sub/voice.wav": "fail",
    }


def test_file_with_folder_is_a_usage_error(tmp_path: Path) -> None:
    a, _ = _folders(tmp_path)
    result = CliRunner().invoke(main, [str(a), str(FIXTURES / "clean.wav")])
    assert result.exit_code == 2


def test_html_not_supported_for_folders(tmp_path: Path) -> None:
    a, b = _folders(tmp_path)
    assert CliRunner().invoke(main, [str(a), str(b), "--format", "html"]).exit_code == 2
