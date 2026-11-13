"""Encoding experiment: the four different 'lengths' of one string."""

from __future__ import annotations

from dataclasses import dataclass

from .graphemes import MAX_LENGTH, graphemes


@dataclass(frozen=True)
class Measurement:
    """UTF-8 bytes, UTF-16 code units, code points and grapheme clusters of a string."""

    utf8_bytes: int
    utf16_units: int
    code_points: int
    graphemes: int


def measure(text: str) -> Measurement:
    """Measure text; lone surrogates are rejected because they cannot be encoded."""
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    if len(text) > MAX_LENGTH:
        raise ValueError(f"text longer than {MAX_LENGTH} code points")
    try:
        utf8 = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"lone surrogate at index {exc.start}: not well-formed text") from exc
    return Measurement(
        utf8_bytes=len(utf8),
        utf16_units=len(text.encode("utf-16-le")) // 2,
        code_points=len(text),
        graphemes=len(graphemes(text)),
    )
