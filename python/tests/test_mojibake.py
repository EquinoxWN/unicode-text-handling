"""Mojibake repair against the shared cases, plus bounds and invalid input."""

import pytest

from unicode_text_handling import vectors
from unicode_text_handling.mojibake import DECODE, ENCODE, garble, repair, unwind_once

CASES = vectors.mojibake()


@pytest.mark.parametrize("case", CASES, ids=[c.note for c in CASES])
def test_repair_vectors(case: vectors.MojibakeCase) -> None:
    fixed = repair(case.text)
    assert (fixed.text, fixed.rounds) == (case.expected, case.rounds)


def test_garble_reproduces_the_vectors() -> None:
    once = [c for c in CASES if c.note.endswith("garbled 1x")]
    assert len(once) == 12
    for case in once:
        assert garble(case.expected) == case.text


def test_table_covers_256_bytes_one_to_one() -> None:
    assert len(DECODE) == 256
    assert len(ENCODE) == 256
    assert DECODE[0x80] == "€"
    assert DECODE[0x81] == "\x81"
    assert DECODE[0x9F] == "Ÿ"
    assert DECODE[0xE9] == "é"


def test_round_limit_is_respected() -> None:
    text = garble(garble("José"))
    assert repair(text, max_rounds=1).text == garble("José")
    assert repair(text, max_rounds=0).rounds == 0


@pytest.mark.parametrize("rounds", [-1, 11])
def test_bad_round_limit_is_rejected(rounds: int) -> None:
    with pytest.raises(ValueError, match="max_rounds"):
        repair("x", max_rounds=rounds)


def test_unwind_once_refuses_non_1252_or_invalid_utf8() -> None:
    assert unwind_once("山") is None
    assert unwind_once("é") is None
    assert unwind_once("Ã©") == "é"


def test_invalid_input() -> None:
    with pytest.raises(TypeError):
        repair(42)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lone surrogate"):
        garble("\udc80")
