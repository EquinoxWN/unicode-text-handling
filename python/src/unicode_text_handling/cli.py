"""Command line: uth report | samples | measure TEXT... | repair TEXT..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import vectors
from .conformance import report
from .measure import measure
from .mojibake import repair


def _measure_row(label: str, text: str) -> str:
    """One table row for the measure and samples commands."""
    m = measure(text)
    return f"{label}\t{m.utf8_bytes}\t{m.utf16_units}\t{m.code_points}\t{m.graphemes}"


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run one command."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="uth", description="Unicode text handling experiments")
    parser.add_argument(
        "--vectors", type=Path, default=vectors.DEFAULT_DIR, help="spec/vectors dir"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report", help="run the shared vectors against Python's APIs")
    sub.add_parser("samples", help="lengths of the shared encoding samples")
    for name in ("measure", "repair"):
        sub.add_parser(name).add_argument("text", nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "report":
            print("language\tsuite\tapi\tcases\tpassed")
            for row in report(args.vectors):
                print(row.tsv())
        elif args.cmd == "samples":
            print("sample\tutf8_bytes\tutf16_units\tcode_points\tgraphemes\tlen()")
            for s in vectors.encoding(args.vectors):
                print(f"{_measure_row(s.name, s.text)}\t{len(s.text)}")
        elif args.cmd == "measure":
            print("text\tutf8_bytes\tutf16_units\tcode_points\tgraphemes")
            for text in args.text:
                print(_measure_row(text, text))
        else:
            for text in args.text:
                fixed = repair(text)
                print(f"{fixed.text}\t(rounds undone: {fixed.rounds})")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
