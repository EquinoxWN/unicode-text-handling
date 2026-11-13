"""Command line output and error handling."""

from pathlib import Path

import pytest

from unicode_text_handling.cli import main


def test_report(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report"]) == 0
    out = capsys.readouterr().out
    assert "python\tnormalization\tunicodedata.normalize NFC\t19074\t19074" in out
    assert "python\tgrapheme\tgraphemes() (this repo)\t602\t602" in out


def test_samples(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["samples"]) == 0
    assert "family-zwj\t25\t11\t7\t1\t7" in capsys.readouterr().out


def test_measure_and_repair(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["measure", "José"]) == 0
    assert main(["repair", "JosÃ©"]) == 0
    out = capsys.readouterr().out
    assert "José\t5\t4\t4\t4" in out
    assert "José\t(rounds undone: 1)" in out


def test_bad_text_exits_1(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["measure", "a\ud800"]) == 1
    assert "lone surrogate" in capsys.readouterr().err


def test_missing_vectors_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--vectors", str(tmp_path), "report"]) == 1
    assert "not found" in capsys.readouterr().err


def test_unknown_command_exits_2() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["frobnicate"])
    assert exc.value.code == 2
