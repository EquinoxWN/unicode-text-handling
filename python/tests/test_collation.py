"""CollationTest_NON_IGNORABLE_SHORT sample: how far plain code point order is from the UCA."""

from unicode_text_handling import vectors
from unicode_text_handling.conformance import in_order_pairs

ORDER = vectors.collation()
BASE = vectors.baselines(vectors.DEFAULT_DIR / "collation.txt")


def le(a: str, b: str) -> bool:
    """Code point order."""
    return a <= b


def test_code_point_order_matches_the_recorded_baseline() -> None:
    assert in_order_pairs(ORDER, le) == BASE["codepoint_in_order"]


def test_code_point_order_is_not_the_uca_order() -> None:
    assert BASE["codepoint_in_order"] < len(ORDER) - 1


def test_utf16_order_matches_the_recorded_baseline() -> None:
    def utf16(a: str, b: str) -> bool:
        return a.encode("utf-16-be") <= b.encode("utf-16-be")

    assert in_order_pairs(ORDER, utf16) == BASE["utf16_in_order"]


def test_in_order_pairs_counts_each_adjacent_pair() -> None:
    assert in_order_pairs(["a", "b", "c"], le) == 2
    assert in_order_pairs(["c", "b", "a"], le) == 0
    assert in_order_pairs(["a", "a"], le) == 1
    assert in_order_pairs(["a"], le) == 0


def test_python_sort_puts_case_and_accents_where_readers_do_not_expect() -> None:
    assert sorted(["zebra", "Zoo", "éclair", "apple"]) == ["Zoo", "apple", "zebra", "éclair"]
