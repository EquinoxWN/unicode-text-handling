"""spec/fetch_ucd.py and spec/generate_vectors.py, without the network."""

import hashlib
import io
from pathlib import Path
from typing import IO

import fetch_ucd
import generate_vectors as gen
import pytest

BODY = b"hello unicode"
SHA = hashlib.sha256(BODY).hexdigest()


def opener_returning(body: bytes) -> fetch_ucd.Opener:
    """An opener that serves body and checks the timeout is passed."""

    def opener(url: str, timeout: float) -> IO[bytes]:
        assert timeout == fetch_ucd.TIMEOUT_S
        return io.BytesIO(body)

    return opener


def no_sleep(_seconds: float) -> None:
    """Skip backoff waits in tests."""


def test_download_writes_verified_file(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    fetch_ucd.download("https://x/f", SHA, target, opener_returning(BODY))
    assert target.read_bytes() == BODY
    assert [p.name for p in tmp_path.iterdir()] == ["f.txt"]


def test_checksum_mismatch_leaves_no_file(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    with pytest.raises(fetch_ucd.FetchError, match="sha256"):
        fetch_ucd.download("https://x/f", SHA, target, opener_returning(b"tampered"))
    assert list(tmp_path.iterdir()) == []


def test_network_errors_are_retried_then_reported(tmp_path: Path) -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def failing(url: str, timeout: float) -> IO[bytes]:
        calls.append(url)
        raise OSError("connection reset")

    with pytest.raises(fetch_ucd.FetchError, match="after 3 attempts"):
        fetch_ucd.download("https://x/f", SHA, tmp_path / "f", failing, sleep=sleeps.append)
    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]
    assert list(tmp_path.iterdir()) == []


def test_retry_succeeds_after_a_transient_error(tmp_path: Path) -> None:
    attempts: list[OSError | None] = [OSError("timeout"), None]

    def flaky(url: str, timeout: float) -> IO[bytes]:
        err = attempts.pop(0)
        if err:
            raise err
        return io.BytesIO(BODY)

    fetch_ucd.download("https://x/f", SHA, tmp_path / "f", flaky, sleep=no_sleep)
    assert (tmp_path / "f").read_bytes() == BODY


def test_oversized_download_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fetch_ucd, "MAX_BYTES", 4)
    with pytest.raises(fetch_ucd.FetchError, match="larger than"):
        fetch_ucd.download("https://x/f", SHA, tmp_path / "f", opener_returning(BODY))


def test_plain_http_is_refused() -> None:
    with pytest.raises(fetch_ucd.FetchError, match="non-https"):
        fetch_ucd._open("http://www.unicode.org/", 1)


def test_fetch_all_skips_verified_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "a.txt").write_bytes(BODY)
    monkeypatch.setattr(fetch_ucd, "FILES", {"a.txt": ("https://x/a", SHA)})

    def never(url: str, timeout: float) -> IO[bytes]:
        raise AssertionError("should not download")

    assert fetch_ucd.fetch_all(tmp_path, never) == []


def test_grapheme_line_parsing() -> None:
    src = "# c\n÷ 0020 × 0308 ÷ 0020 ÷\t# comment\n÷ 000D × 000A ÷\n"
    assert gen.grapheme_cases(src) == [["0020 0308", "0020"], ["000D 000A"]]


def test_normalization_rejects_short_lines() -> None:
    with pytest.raises(ValueError, match="bad NormalizationTest"):
        gen.normalization("0041;0041;\n")


def test_property_ranges_merge_and_detect_overlap() -> None:
    gbp = "0300..0301 ; Extend\n0302 ; Extend\n000D ; CR\n"
    emoji = "00A9 ; Extended_Pictographic\n00AE ; Emoji\n"
    assert gen.property_ranges(gbp, emoji) == [
        (0x0D, 0x0D, "CR"),
        (0xA9, 0xA9, "ExtPict"),
        (0x300, 0x302, "Extend"),
    ]
    with pytest.raises(ValueError, match="overlapping"):
        gen.property_ranges("0300 ; Extend\n", "0300 ; Extended_Pictographic\n")


def test_garble_uses_whatwg_fallback_for_undefined_bytes() -> None:
    assert gen.garble("Á") == "Ã\x81"
    assert gen.cp1252_byte("\x81") == 0x81
    assert gen.cp1252_byte("€") == 0x80
    assert gen.cp1252_byte("\x80") is None
