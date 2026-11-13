"""Run the shared Unicode vectors against Python's APIs and report where each one disagrees."""

from __future__ import annotations

import itertools
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from . import vectors
from .graphemes import graphemes
from .vectors import GraphemeCase, NormalizationCase

Form = Literal["NFC", "NFD", "NFKC", "NFKD"]
FORMS: tuple[Form, ...] = ("NFC", "NFD", "NFKC", "NFKD")


@dataclass(frozen=True)
class Row:
    """One line of the conformance report."""

    language: str
    suite: str
    api: str
    cases: int
    passed: int

    def tsv(self) -> str:
        """Tab-separated form."""
        return f"{self.language}\t{self.suite}\t{self.api}\t{self.cases}\t{self.passed}"


def normalization_ok(case: NormalizationCase, form: Form, norm: Callable[[Form, str], str]) -> bool:
    """The NormalizationTest.txt invariants for one form."""
    c1, c2, c3, c4, c5 = case.columns

    def f(s: str) -> str:
        return norm(form, s)

    if form == "NFC":
        return c2 == f(c1) == f(c2) == f(c3) and c4 == f(c4) == f(c5)
    if form == "NFD":
        return c3 == f(c1) == f(c2) == f(c3) and c5 == f(c4) == f(c5)
    if form == "NFKC":
        return all(c4 == f(c) for c in case.columns)
    return all(c5 == f(c) for c in case.columns)


def normalization_failures(
    cases: Iterable[NormalizationCase],
    form: Form,
    norm: Callable[[Form, str], str] = unicodedata.normalize,
) -> list[int]:
    """Line numbers of cases that break the invariants for form."""
    return [c.line for c in cases if not normalization_ok(c, form, norm)]


def grapheme_failures(
    cases: Iterable[GraphemeCase], segment: Callable[[str], Sequence[str]]
) -> list[str]:
    """Keys of cases the segmenter splits differently from the vectors."""
    return [c.key for c in cases if tuple(segment(c.text)) != c.clusters]


def in_order_pairs(items: Sequence[str], before_or_equal: Callable[[str, str], bool]) -> int:
    """Adjacent pairs that the comparison keeps in order."""
    return sum(before_or_equal(a, b) for a, b in itertools.pairwise(items))


def code_points(text: str) -> list[str]:
    """Naive split: one code point per character."""
    return list(text)


def report(directory: Path = vectors.DEFAULT_DIR) -> list[Row]:
    """Every suite against every Python API."""
    rows = []
    norm = vectors.normalization(directory)
    for form in FORMS:
        bad = normalization_failures(norm, form)
        rows.append(
            Row(
                "python",
                "normalization",
                f"unicodedata.normalize {form}",
                len(norm),
                len(norm) - len(bad),
            )
        )
    gcases = vectors.grapheme(directory)
    for api, seg in (
        ("graphemes() (this repo)", graphemes),
        ("list(str) code points", code_points),
    ):
        rows.append(
            Row(
                "python",
                "grapheme",
                api,
                len(gcases),
                len(gcases) - len(grapheme_failures(gcases, seg)),
            )
        )
    coll = vectors.collation(directory)
    rows.append(
        Row(
            "python",
            "collation",
            "str < (code points)",
            len(coll) - 1,
            in_order_pairs(coll, lambda a, b: a <= b),
        )
    )
    return rows
