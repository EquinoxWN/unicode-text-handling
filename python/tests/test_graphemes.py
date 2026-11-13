"""GraphemeBreakTest.txt (Unicode 15.0.0) against this repo's UAX #29 segmenter."""

import pytest

from unicode_text_handling import vectors
from unicode_text_handling.conformance import code_points, grapheme_failures
from unicode_text_handling.graphemes import (
    MAX_LENGTH,
    UNICODE_VERSION,
    break_property,
    count_graphemes,
    graphemes,
)

CASES = vectors.grapheme()
BASE = vectors.baselines(vectors.DEFAULT_DIR / "grapheme.txt")


def test_table_matches_the_vector_version() -> None:
    assert UNICODE_VERSION == "15.0.0"


def test_segmenter_passes_every_case() -> None:
    assert grapheme_failures(CASES, graphemes) == []


def test_naive_code_point_split_gets_the_baseline_count_right() -> None:
    passed = len(CASES) - len(grapheme_failures(CASES, code_points))
    assert passed == BASE["codepoint_exact"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", []),
        ("ab", ["a", "b"]),
        ("éx", ["é", "x"]),
        ("\r\n\n", ["\r\n", "\n"]),
        ("\U0001f1ef\U0001f1f5\U0001f1fa", ["\U0001f1ef\U0001f1f5", "\U0001f1fa"]),
        ("\U0001f468‍\U0001f469‍\U0001f467", ["\U0001f468‍\U0001f469‍\U0001f467"]),
        ("a‍\U0001f469", ["a‍", "\U0001f469"]),
        ("각", ["각"]),
        ("؀a", ["؀a"]),
        ("कि", ["कि"]),
    ],
)
def test_known_clusters(text: str, expected: list[str]) -> None:
    assert graphemes(text) == expected


def test_property_lookup() -> None:
    assert break_property("a") == "Other"
    assert break_property("́") == "Extend"
    assert break_property("\r") == "CR"
    assert break_property("\U0001f600") == "ExtPict"
    assert break_property("\U0010ffff") == "Other"


def test_count_graphemes() -> None:
    assert count_graphemes("\U0001f44d\U0001f3fdok") == 3


def test_rejects_non_str() -> None:
    with pytest.raises(TypeError):
        graphemes(b"abc")  # type: ignore[arg-type]


def test_rejects_oversized_input() -> None:
    with pytest.raises(ValueError, match="longer than"):
        graphemes("a" * (MAX_LENGTH + 1))
