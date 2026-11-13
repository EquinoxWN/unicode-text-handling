"""Shared vector loaders: the files parse, and malformed input fails with a clear error."""

from pathlib import Path

import pytest

from unicode_text_handling import vectors
from unicode_text_handling.vectors import VectorError


def test_shared_files_load_with_expected_sizes() -> None:
    assert len(vectors.normalization()) == 19074
    assert len(vectors.grapheme()) == 602
    assert len(vectors.collation()) == 9004
    assert len(vectors.mojibake()) == 12 * 4 + 7
    assert len(vectors.encoding()) == 15


def test_normalization_parts_are_tracked() -> None:
    parts = {c.part for c in vectors.normalization()}
    assert parts == {"0", "1", "2", "3"}


def test_baselines_are_read() -> None:
    assert vectors.baselines(vectors.DEFAULT_DIR / "grapheme.txt") == {
        "codepoint_exact": 250,
        "utf16_exact": 220,
    }


@pytest.mark.parametrize(
    ("field", "expected"), [("", ""), ("0041", "A"), ("1F600 0041", "\U0001f600A")]
)
def test_unhex(field: str, expected: str) -> None:
    assert vectors.unhex(field) == expected


@pytest.mark.parametrize("field", ["XYZ", "110000", "-1"])
def test_unhex_rejects_bad_input(field: str) -> None:
    with pytest.raises(VectorError):
        vectors.unhex(field, 7)


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(VectorError, match="not found"):
        vectors.grapheme(tmp_path)


def test_empty_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "grapheme.txt").write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(VectorError, match="no cases"):
        vectors.grapheme(tmp_path)


def test_wrong_field_count_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "normalization.txt").write_text("0041;0041;0041\n", encoding="utf-8")
    with pytest.raises(VectorError, match="5 fields"):
        vectors.normalization(tmp_path)


def test_bad_mojibake_row_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "mojibake.tsv").write_text("0041\t0041\tx\tnote\n", encoding="utf-8")
    with pytest.raises(VectorError, match=r"mojibake.tsv:1"):
        vectors.mojibake(tmp_path)


def test_bad_encoding_row_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "encoding.tsv").write_text("x\t0041\t1\t1\t1\n", encoding="utf-8")
    with pytest.raises(VectorError, match=r"encoding.tsv:1"):
        vectors.encoding(tmp_path)


def test_bad_baseline_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "grapheme.txt"
    path.write_text("@baseline codepoint_exact many\n0041\n", encoding="utf-8")
    with pytest.raises(VectorError, match="bad baseline"):
        vectors.baselines(path)


def test_oversized_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "collation.txt").write_bytes(b"0041\n" * (vectors.MAX_FILE_BYTES // 5 + 1))
    with pytest.raises(VectorError, match="too large"):
        vectors.collation(tmp_path)


def test_deviations_apply_from_their_unicode_version() -> None:
    key = "2701 200D 2701"
    assert vectors.expected_deviations("js", "grapheme", "Intl.Segmenter", "17.0") == {key}
    assert vectors.expected_deviations("js", "grapheme", "Intl.Segmenter", "16.0") == set()
    assert vectors.expected_deviations("js", "encoding", "Intl.Segmenter", "15.1") == {"namaste"}
    assert vectors.expected_deviations("python", "grapheme", "graphemes", "99.0") == set()


def test_bad_version_is_rejected() -> None:
    with pytest.raises(VectorError):
        vectors.version_tuple("fifteen")
