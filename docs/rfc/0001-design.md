# RFC 0001: unicode-text-handling design

- **Status:** Accepted (M1 built)
- **Author:** EquinoxWN
- **Created:** 2026

## Problem

Names like 'José', '山田' or one emoji break search, sorting and length checks. The same string has
four different lengths (UTF-8 bytes, UTF-16 code units, code points, user-perceived characters), the
same visible text can be stored as different code point sequences, and text decoded with the wrong
encoding turns into mojibake ('JosÃ©'). Each language's standard library handles some of this and
gets some of it wrong, and teams rarely know which parts.

Who is affected: backend and front-end engineers who validate, store, truncate, search or sort
user-entered names and messages in Java, Python or JavaScript.

## Goals and critical-to-quality measures (Define)

| CTQ | Target for M1 | How it is measured |
|---|---|---|
| Normalization conformance of each language's built-in API | 19,074 / 19,074 NormalizationTest cases, all four forms | `make test`, `make report` |
| Grapheme segmentation conformance | 602 / 602 GraphemeBreakTest cases for the segmenter each language uses, except documented Unicode-version differences | same |
| Same vectors in all three languages | one generated file per suite in `spec/vectors`, read by all three | `generate_vectors.py --check` in `make lint` |
| Encoding counts | 15 samples with hand-checked byte, UTF-16, code point and grapheme counts, equal in all languages | `make test`, `make samples` |
| Mojibake repair | 55 shared cases (1 to 4 rounds of mis-decoding, plus text that must stay unchanged) pass in all languages | `make test` |
| Default-API gaps are visible | a report row per suite and API with cases and passes | `make report` |

Later goals (M2, M3): normalization and case folding for search and uniqueness, grapheme-safe
truncation, locale-aware collation with ICU, and a checklist for column sizes, regex and display width.

## Non-goals

- Running as a hosted service.
- Writing a UCA collation implementation in M1 (collation vectors are used to measure the default
  APIs only; ICU-based collation is M3).
- Supporting every Unicode version at once: the vectors are pinned to Unicode 15.0.0.

## Design

```
unicode.org (pinned URLs + SHA-256)
   └─ spec/fetch_ucd.py ──> data/ucd/15.0.0/ (git-ignored, re-downloadable)
          └─ spec/generate_vectors.py ──> spec/vectors/*.txt|tsv (committed)
                                     └─> python/src/unicode_text_handling/_grapheme_data.py
spec/vectors ──> java/ (JUnit)   python/ (pytest)   js/ (node:test)
```

- **Pinned data.** `fetch_ucd.py` downloads NormalizationTest, GraphemeBreakTest,
  GraphemeBreakProperty, emoji-data and CollationTest for Unicode 15.0.0 over https, with a 60 s
  timeout, three attempts with 1 s / 2 s backoff, an 8 MB size cap, SHA-256 verification and an
  atomic rename. A checksum mismatch is never retried.
- **Shared vectors.** `generate_vectors.py` reduces the files to simple line formats (hex code
  points, `;`, `|` and tab separators) that each language parses with its standard library. The
  collation sample is every 20th line of `CollationTest_NON_IGNORABLE_SHORT.txt` (9,004 strings, 30
  lone-surrogate lines dropped). Baseline counts for naive approaches are computed by the generator
  and stored in the files, so every language checks the same numbers. `--check` fails on drift.
- **Why 15.0.0.** It is the newest version every runtime in CI implements: Java 21 and Python 3.12
  are at Unicode 15.0, Node.js 24 is newer. Normalization of assigned characters is stable across
  versions; grapheme rules are not, so differences on newer runtimes are listed in
  `known-deviations.tsv` with the Unicode version they start at, and tests expect exactly those.
- **Per language.** Java uses `java.text.Normalizer`, `BreakIterator`, regex `\X` and
  `Collator`. JavaScript uses `String.prototype.normalize`, `Intl.Segmenter` and `Intl.Collator`.
  Python has `unicodedata` for normalization but no grapheme segmenter, so this repo implements
  UAX #29 rules GB3 to GB999 over a generated property table (see ADR 0002).
- **Encoding experiment.** `measure()` returns UTF-8 bytes, UTF-16 units, code points and grapheme
  clusters, and rejects lone surrogates rather than replacing them.
- **Mojibake repair.** Encode the text as Windows-1252 (WHATWG table: the five undefined bytes map to
  the C1 control of the same value), decode strictly as UTF-8, accept only if it decodes and changes
  the text, repeat at most 3 times (bounded, 0 to 10 allowed). Text that is not Windows-1252
  encodable or not valid UTF-8 underneath is returned unchanged.

## Alternatives considered

| Option | Why not |
|---|---|
| Read the Unicode files directly in each language's tests | Every language would need its own parser for four different file formats and network access at test time; one generator plus simple committed files keeps the three test suites identical and offline. |
| Commit the original Unicode files unchanged | About 6.5 MB, mostly comments and a 1.9 MB collation file of which a sample is enough to measure ordering; the reduced files are 1.1 MB and the generator proves they match the originals. |
| PyICU for Python graphemes and collation | No official Windows wheels and a native ICU dependency; for M1 the standard library plus a short rule implementation (about 80 lines) covers graphemes. ICU is planned for M3 collation. |
| Use the newest Unicode version (17.0) | Java 21 and Python 3.12 implement 15.0, so vectors for characters they do not know would fail for reasons unrelated to correctness. |
| Heuristic mojibake detection (character-frequency scoring, as in ftfy) | More coverage, but harder to explain and to test in three languages; the strict round trip only repairs text that is provably UTF-8 underneath. |

## Measurement plan

`make report` prints one row per language, suite and API with cases and passes; `make test`
asserts the conformance targets above and the exact baseline counts; CI prints the report as a
`::notice`. Results and the machine they were measured on are in `docs/results/m1.md`.

## Milestones

- **M1 (done):** shared vectors from the Unicode data files run against Java, Python and
  JavaScript; encoding experiments and mojibake repair.
- **M2:** NFC/NFD and case folding for search and uniqueness checks; grapheme-aware truncation.
- **M3:** locale-aware collation with ICU; checklist for column sizes, regex and CJK display width;
  published table of where each default API gets it wrong.

## Risks and open questions

- Runtimes newer than the vectors change grapheme results (seen: Node.js 24 with Unicode 17 on
  `2701 200D 2701` and on the Devanagari sample). The deviation ledger must be updated when CI moves
  to a newer runtime; tests fail until it is, by design.
- The mojibake repair can change genuine text that happens to be valid UTF-8 when read as
  Windows-1252 (for example the literal two characters 'Ã©'). This is rare in real text but possible.
- Collation is measured on a 1-in-20 sample, so pairs that are only adjacent in the full file are
  not compared.
