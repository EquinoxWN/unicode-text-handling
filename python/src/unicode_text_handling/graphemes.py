"""Extended grapheme clusters (UAX #29, Unicode 15.0.0): Python's standard library has no segmenter."""

from __future__ import annotations

from bisect import bisect_right

from ._grapheme_data import RANGES, UNICODE_VERSION

__all__ = ["UNICODE_VERSION", "break_property", "count_graphemes", "graphemes"]

MAX_LENGTH = 1_000_000
_STARTS = [r[0] for r in RANGES]
_CONTROLS = frozenset({"Control", "CR", "LF"})


def break_property(char: str) -> str:
    """Grapheme_Cluster_Break value of one character (ExtPict for Extended_Pictographic)."""
    cp = ord(char)
    i = bisect_right(_STARTS, cp) - 1
    if i >= 0 and RANGES[i][0] <= cp <= RANGES[i][1]:
        return RANGES[i][2]
    return "Other"


def _check(text: object) -> str:
    """Validate the input type and size."""
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    if len(text) > MAX_LENGTH:
        raise ValueError(f"text longer than {MAX_LENGTH} code points")
    return text


def _breaks(prev: str, cur: str, pict_before_zwj: bool, ri_run: int) -> bool:
    """Rules GB3 to GB999 for the boundary between prev and cur."""
    if prev == "CR" and cur == "LF":
        return False  # GB3
    if prev in _CONTROLS or cur in _CONTROLS:
        return True  # GB4, GB5
    if prev == "L" and cur in ("L", "V", "LV", "LVT"):
        return False  # GB6
    if prev in ("LV", "V") and cur in ("V", "T"):
        return False  # GB7
    if prev in ("LVT", "T") and cur == "T":
        return False  # GB8
    if cur in ("Extend", "ZWJ", "SpacingMark") or prev == "Prepend":
        return False  # GB9, GB9a, GB9b
    if prev == "ZWJ" and cur == "ExtPict" and pict_before_zwj:
        return False  # GB11
    if prev == cur == "Regional_Indicator":
        return ri_run % 2 == 0  # GB12, GB13
    return True  # GB999


def graphemes(text: str) -> list[str]:
    """Split text into user-perceived characters."""
    _check(text)
    if not text:
        return []
    out: list[str] = []
    start = 0
    prev = break_property(text[0])
    in_pict = prev == "ExtPict"  # ExtPict Extend* ends at prev
    pict_before_prev = False  # in_pict as it was one character before prev
    ri_run = 1 if prev == "Regional_Indicator" else 0
    for i in range(1, len(text)):
        cur = break_property(text[i])
        if _breaks(prev, cur, pict_before_prev, ri_run):
            out.append(text[start:i])
            start = i
        pict_before_prev = in_pict
        in_pict = cur == "ExtPict" or (cur == "Extend" and in_pict)
        ri_run = ri_run + 1 if cur == "Regional_Indicator" else 0
        prev = cur
    out.append(text[start:])
    return out


def count_graphemes(text: str) -> int:
    """Number of user-perceived characters."""
    return len(graphemes(text))
