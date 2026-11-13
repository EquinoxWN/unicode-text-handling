"""Download the pinned Unicode 15.0.0 data files into data/ucd/15.0.0, verifying each SHA-256.

usage: python spec/fetch_ucd.py [--dest DIR]
Files already present with the right checksum are kept; anything else is downloaded again.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import IO

UNICODE_VERSION = "15.0.0"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEST = ROOT / "data" / "ucd" / UNICODE_VERSION
BASE = f"https://www.unicode.org/Public/{UNICODE_VERSION}"
FILES: dict[str, tuple[str, str]] = {
    "NormalizationTest.txt": (
        f"{BASE}/ucd/NormalizationTest.txt",
        "fb9ac8cc154a80cad6caac9897af55a4e75176af6f4e2bb6edc2bf8b1d57f326",
    ),
    "GraphemeBreakTest.txt": (
        f"{BASE}/ucd/auxiliary/GraphemeBreakTest.txt",
        "0d2080d0def294a4b7660801cc03ddfe5866ff300c789c2cc1b50fd7802b2d97",
    ),
    "GraphemeBreakProperty.txt": (
        f"{BASE}/ucd/auxiliary/GraphemeBreakProperty.txt",
        "5a0f8748575432f8ff95e1dd5bfaa27bda1a844809e17d6939ee912bba6568a1",
    ),
    "emoji-data.txt": (
        f"{BASE}/ucd/emoji/emoji-data.txt",
        "29071dba22c72c27783a73016afb8ffaeb025866740791f9c2d0b55cc45a3470",
    ),
    "CollationTest.zip": (
        f"https://www.unicode.org/Public/UCA/{UNICODE_VERSION}/CollationTest.zip",
        "c30504af10d47cc55a5e1fde5506fb13c81073f2552460538b9e2a6e870e7c04",
    ),
}
TIMEOUT_S = 60
ATTEMPTS = 3
MAX_BYTES = 8 * 1024 * 1024

Opener = Callable[[str, float], IO[bytes]]


class FetchError(RuntimeError):
    """A file could not be downloaded or failed its checksum."""


def sha256(path: Path) -> str:
    """Hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open(url: str, timeout: float) -> IO[bytes]:
    """Open an https URL with a timeout."""
    if not url.startswith("https://"):
        raise FetchError(f"refusing non-https URL: {url}")
    agent = {"User-Agent": "unicode-text-handling-fetch"}
    request = urllib.request.Request(url, headers=agent)  # noqa: S310 (https checked above)
    response: IO[bytes] = urllib.request.urlopen(request, timeout=timeout)  # noqa: S310
    return response


def download(
    url: str,
    expected_sha: str,
    target: Path,
    opener: Opener = _open,
    attempts: int = ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Download url to target atomically, retrying with backoff; fail on checksum mismatch."""
    target.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        fd, tmp_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".part"
        )
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as out, opener(url, TIMEOUT_S) as resp:
                size = 0
                for chunk in iter(lambda: resp.read(1 << 16), b""):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise FetchError(f"{url}: larger than {MAX_BYTES} bytes")
                    out.write(chunk)
            got = sha256(tmp)
            if got != expected_sha:
                raise FetchError(f"{url}: sha256 {got}, expected {expected_sha}")
            os.replace(tmp, target)
            return
        except FetchError:
            tmp.unlink(missing_ok=True)
            raise
        except OSError as exc:  # network errors (URLError is an OSError) and disk errors
            tmp.unlink(missing_ok=True)
            last = exc
            if attempt < attempts:
                sleep(2.0 ** (attempt - 1))
    raise FetchError(f"{url}: failed after {attempts} attempts: {last}") from last


def fetch_all(dest: Path = DEFAULT_DEST, opener: Opener = _open) -> list[str]:
    """Make sure every pinned file is in dest; return the names that were downloaded."""
    fetched = []
    for name, (url, expected) in FILES.items():
        target = dest / name
        if target.is_file() and sha256(target) == expected:
            continue
        download(url, expected, target, opener)
        fetched.append(name)
    return fetched


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    args = parser.parse_args(argv)
    try:
        fetched = fetch_all(args.dest)
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        f"Unicode {UNICODE_VERSION} data in {args.dest}: {len(FILES)} files verified, "
        f"{len(fetched)} downloaded"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
