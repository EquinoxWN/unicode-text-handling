"""Encoding experiment: byte, UTF-16, code point and grapheme counts of the shared samples."""

import pytest

from unicode_text_handling import vectors
from unicode_text_handling.graphemes import MAX_LENGTH
from unicode_text_handling.measure import Measurement, measure

SAMPLES = vectors.encoding()


@pytest.mark.parametrize("sample", SAMPLES, ids=[s.name for s in SAMPLES])
def test_sample_counts(sample: vectors.EncodingSample) -> None:
    expected = Measurement(
        sample.utf8_bytes, sample.utf16_units, sample.code_points, sample.graphemes
    )
    assert measure(sample.text) == expected


def test_len_is_code_points_not_characters() -> None:
    family = next(s for s in SAMPLES if s.name == "family-zwj")
    assert len(family.text) == 7
    assert measure(family.text).graphemes == 1


def test_lone_surrogate_is_rejected() -> None:
    with pytest.raises(ValueError, match="lone surrogate at index 1"):
        measure("a\ud800")


def test_non_str_is_rejected() -> None:
    with pytest.raises(TypeError):
        measure(None)  # type: ignore[arg-type]


def test_oversized_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="longer than"):
        measure("a" * (MAX_LENGTH + 1))
