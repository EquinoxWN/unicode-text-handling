# ADR 0003: Repair mojibake only by a strict, bounded round trip

- **Status:** Accepted

## Context

Mojibake from UTF-8 read as Windows-1252 ('JosÃ©') is common in exports, CSV files and old
databases, sometimes applied two or three times. Repair tools such as ftfy use heuristics (character
frequency, known bad sequences) to decide when to fix text. Heuristics repair more, but their
decisions are hard to reproduce identically in three languages and can change genuine text.

## Decision

One repair round encodes every character with the Windows-1252 table (WHATWG mapping, so all 256
bytes are reachable) and decodes the bytes as strict UTF-8. The round is accepted only if every
character was encodable, the bytes are valid UTF-8 and the result differs from the input. Rounds
repeat up to a limit (3 by default, 0 to 10 allowed).

## Consequences

- Same algorithm and same 55 shared cases in Java, Python and JavaScript.
- Text with any character outside Windows-1252 (for example '山田') or that is not valid UTF-8
  underneath (for example 'SÃO PAULO', '€100') is never touched.
- Only the Windows-1252 / Latin-1 confusion is handled; Shift_JIS, GBK or KOI8-R mojibake is not.
- A genuine string that is also valid UTF-8 underneath (the literal 'Ã©') would be changed. The
  README and RFC list this as a known limitation.
