# ADR 0002: Generate one set of shared vectors, pinned to Unicode 15.0.0, with a deviation ledger

- **Status:** Accepted

## Context

The Unicode Consortium publishes conformance files for normalization, grapheme breaking and
collation. Three languages need to run them. The runtimes implement different Unicode versions on
this machine and in CI: Java 21 is at 15.0, Python 3.12 (CI) at 15.0 and 3.14 (local) at 16.0,
Node.js 24.19 at 17.0. Grapheme rules changed in 15.1 (rule GB9c for Indic conjuncts) and some
characters lost Extended_Pictographic in 17.0.

## Decision

- A Python generator turns the pinned 15.0.0 files into small line-based files under
  `spec/vectors`, committed and checked for drift by `make lint`. All three languages parse the same
  files with their standard libraries.
- The vectors stay at 15.0.0, the oldest version among the runtimes, so every runtime knows every
  character in them.
- Differences caused by a newer runtime are recorded in `spec/vectors/known-deviations.tsv` with the
  Unicode version they start at. Tests compute the expected failure set for the runtime they run on
  and require exactly that set: an undocumented failure fails, and so does a documented one that no
  longer happens.
- Python gets its own UAX #29 segmenter, generated from the same 15.0.0 property files, because its
  standard library has none.

## Consequences

- The three test suites are identical in content and run offline; only `make lint` and `make
  vectors` need network access (once, then `data/` is reused).
- Two deviations are in the ledger today, both for newer Unicode in Node.js 24 (one grapheme case,
  and the Devanagari encoding sample, which also applies to Java 22+).
- Moving to a newer Unicode version is a deliberate change: update the pinned URLs and checksums,
  regenerate, and review the ledger.
- The Python segmenter is code this repo has to maintain; the conformance file is what keeps it
  honest (602/602 cases).
