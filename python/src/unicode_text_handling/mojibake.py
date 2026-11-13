"""Mojibake: UTF-8 bytes decoded as Windows-1252, and how to undo it."""

from __future__ import annotations

from dataclasses import dataclass

from .graphemes import MAX_LENGTH

MAX_ROUNDS = 3

# Windows-1252 bytes 0x80..0x9F (WHATWG Encoding Standard); undefined bytes map to the C1 control.
_HIGH = "€\u0081‚ƒ„…†‡ˆ‰Š‹Œ\u008dŽ\u008f\u0090‘’“”•–—˜™š›œ\u009džŸ"
DECODE = (
    tuple(chr(b) for b in range(0x80)) + tuple(_HIGH) + tuple(chr(b) for b in range(0xA0, 0x100))
)
ENCODE = {ch: b for b, ch in enumerate(DECODE)}


@dataclass(frozen=True)
class Repair:
    """Repaired text and how many mis-decodings were undone."""

    text: str
    rounds: int


def _check(text: object) -> str:
    """Validate the input type and size."""
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    if len(text) > MAX_LENGTH:
        raise ValueError(f"text longer than {MAX_LENGTH} code points")
    return text


def garble(text: str) -> str:
    """Encode as UTF-8 and decode as Windows-1252: what a mis-configured reader shows."""
    _check(text)
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"lone surrogate at index {exc.start}") from exc
    return "".join(DECODE[b] for b in data)


def unwind_once(text: str) -> str | None:
    """Undo one round of mojibake, or None if text is not Windows-1252-encodable valid UTF-8."""
    data = bytearray()
    for ch in text:
        b = ENCODE.get(ch)
        if b is None:
            return None
        data.append(b)
    try:
        return bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        return None


def repair(text: str, max_rounds: int = MAX_ROUNDS) -> Repair:
    """Undo up to max_rounds of UTF-8-read-as-Windows-1252, stopping when a round would not apply."""
    _check(text)
    if not 0 <= max_rounds <= 10:
        raise ValueError("max_rounds must be between 0 and 10")
    rounds = 0
    while rounds < max_rounds:
        fixed = unwind_once(text)
        if fixed is None or fixed == text:
            break
        text, rounds = fixed, rounds + 1
    return Repair(text, rounds)
