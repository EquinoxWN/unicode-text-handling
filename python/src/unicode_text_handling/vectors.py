"""Loaders for the shared test vectors in spec/vectors (the same files Java and JavaScript read)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 4 * 1024 * 1024
DEFAULT_DIR = Path(__file__).resolve().parents[3] / "spec" / "vectors"


class VectorError(ValueError):
    """A vector file is missing, too large or malformed."""


@dataclass(frozen=True)
class NormalizationCase:
    """One NormalizationTest line: c1..c5 and the part it came from."""

    line: int
    part: str
    columns: tuple[str, str, str, str, str]


@dataclass(frozen=True)
class GraphemeCase:
    """One GraphemeBreakTest line: the expected clusters."""

    line: int
    key: str
    clusters: tuple[str, ...]

    @property
    def text(self) -> str:
        """The whole string being segmented."""
        return "".join(self.clusters)


@dataclass(frozen=True)
class MojibakeCase:
    """Garbled input, expected repair and the number of repair rounds."""

    line: int
    text: str
    expected: str
    rounds: int
    note: str


@dataclass(frozen=True)
class EncodingSample:
    """A sample string with its expected UTF-8, UTF-16, code point and grapheme counts."""

    line: int
    name: str
    text: str
    utf8_bytes: int
    utf16_units: int
    code_points: int
    graphemes: int


@dataclass(frozen=True)
class Deviation:
    """A documented case where a runtime's default API differs from the 15.0.0 vectors."""

    language: str
    suite: str
    api: str
    key: str
    min_unicode: tuple[int, ...]
    reason: str


def unhex(field: str, line: int = 0) -> str:
    """Text from space-separated hex code points (empty field = empty string)."""
    try:
        cps = [int(h, 16) for h in field.split()]
    except ValueError as exc:
        raise VectorError(f"line {line}: bad hex in {field!r}") from exc
    if any(not 0 <= cp <= 0x10FFFF for cp in cps):
        raise VectorError(f"line {line}: code point out of range in {field!r}")
    return "".join(chr(cp) for cp in cps)


def version_tuple(text: str) -> tuple[int, ...]:
    """'15.1.0' -> (15, 1, 0)."""
    try:
        return tuple(int(p) for p in text.split("."))
    except ValueError as exc:
        raise VectorError(f"bad version {text!r}") from exc


def _lines(path: Path) -> list[tuple[int, str]]:
    """Numbered non-comment, non-blank lines of a vector file."""
    if not path.is_file():
        raise VectorError(f"vector file not found: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise VectorError(f"vector file too large: {path}")
    text = path.read_text(encoding="utf-8")
    return [
        (n, ln.rstrip("\r"))
        for n, ln in enumerate(text.split("\n"), 1)
        if ln.strip() and not ln.startswith("#")
    ]


def baselines(path: Path) -> dict[str, int]:
    """The '@baseline name value' directives of a vector file."""
    out = {}
    for n, ln in _lines(path):
        if ln.startswith("@baseline"):
            parts = ln.split()
            if len(parts) != 3 or not parts[2].isdigit():
                raise VectorError(f"{path.name}:{n}: bad baseline {ln!r}")
            out[parts[1]] = int(parts[2])
    return out


def normalization(directory: Path = DEFAULT_DIR) -> list[NormalizationCase]:
    """Cases from normalization.txt."""
    part, out = "", []
    for n, ln in _lines(directory / "normalization.txt"):
        if ln.startswith("@part"):
            part = ln.split()[1]
            continue
        fields = ln.split(";")
        if len(fields) != 5:
            raise VectorError(f"normalization.txt:{n}: expected 5 fields")
        c = tuple(unhex(f, n) for f in fields)
        out.append(NormalizationCase(n, part, (c[0], c[1], c[2], c[3], c[4])))
    if not out:
        raise VectorError("normalization.txt has no cases")
    return out


def grapheme(directory: Path = DEFAULT_DIR) -> list[GraphemeCase]:
    """Cases from grapheme.txt."""
    out = []
    for n, ln in _lines(directory / "grapheme.txt"):
        if ln.startswith("@"):
            continue
        clusters = tuple(unhex(c, n) for c in ln.split("|"))
        if any(not c for c in clusters):
            raise VectorError(f"grapheme.txt:{n}: empty cluster")
        out.append(GraphemeCase(n, ln.replace("|", " "), clusters))
    if not out:
        raise VectorError("grapheme.txt has no cases")
    return out


def collation(directory: Path = DEFAULT_DIR) -> list[str]:
    """Strings from collation.txt, in DUCET order."""
    out = [unhex(ln, n) for n, ln in _lines(directory / "collation.txt") if not ln.startswith("@")]
    if len(out) < 2:
        raise VectorError("collation.txt needs at least two strings")
    return out


def mojibake(directory: Path = DEFAULT_DIR) -> list[MojibakeCase]:
    """Cases from mojibake.tsv."""
    out = []
    for n, ln in _lines(directory / "mojibake.tsv"):
        fields = ln.split("\t")
        if len(fields) != 4 or not fields[2].isdigit():
            raise VectorError(f"mojibake.tsv:{n}: expected input, expected, rounds, note")
        out.append(
            MojibakeCase(n, unhex(fields[0], n), unhex(fields[1], n), int(fields[2]), fields[3])
        )
    return out


def encoding(directory: Path = DEFAULT_DIR) -> list[EncodingSample]:
    """Samples from encoding.tsv."""
    out = []
    for n, ln in _lines(directory / "encoding.tsv"):
        f = ln.split("\t")
        if len(f) != 6 or not all(x.isdigit() for x in f[2:]):
            raise VectorError(f"encoding.tsv:{n}: expected name, hex, 4 counts")
        out.append(EncodingSample(n, f[0], unhex(f[1], n), *(int(x) for x in f[2:])))
    return out


def deviations(directory: Path = DEFAULT_DIR) -> list[Deviation]:
    """Rows of known-deviations.tsv."""
    out = []
    for n, ln in _lines(directory / "known-deviations.tsv"):
        f = ln.split("\t")
        if len(f) != 6:
            raise VectorError(f"known-deviations.tsv:{n}: expected 6 fields")
        out.append(Deviation(f[0], f[1], f[2], f[3], version_tuple(f[4]), f[5]))
    return out


def expected_deviations(
    language: str, suite: str, api: str, unicode_version: str, directory: Path = DEFAULT_DIR
) -> set[str]:
    """Case keys documented to differ for this API on a runtime with this Unicode version."""
    runtime = version_tuple(unicode_version)
    return {
        d.key
        for d in deviations(directory)
        if (d.language, d.suite, d.api) == (language, suite, api) and runtime >= d.min_unicode
    }
