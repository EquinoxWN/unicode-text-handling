// Encoding experiment counts, mojibake repair, vector loaders and the command line.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import * as vectors from "../src/vectors.js";
import { DECODE, MAX_LENGTH, garble, graphemes, measure, repair, unwindOnce } from "../src/text.js";
import { run } from "../src/cli.js";

const UNICODE = process.versions.unicode;
const DEVIATING = vectors.expectedDeviations("js", "encoding", "Intl.Segmenter", UNICODE);

for (const s of vectors.encoding()) {
  test(`sample ${s.name}`, () => {
    const m = measure(s.text);
    assert.equal(m.utf8Bytes, s.utf8Bytes);
    assert.equal(m.utf16Units, s.utf16Units);
    assert.equal(m.codePoints, s.codePoints);
    if (DEVIATING.has(s.name)) assert.notEqual(m.graphemes, s.graphemes, "documented deviation no longer happens");
    else assert.equal(m.graphemes, s.graphemes);
  });
}

for (const c of vectors.mojibake()) {
  test(`repair: ${c.note}`, () => {
    assert.deepEqual(repair(c.text), { text: c.expected, rounds: c.rounds });
  });
}

test("garble reproduces the one-round vectors", () => {
  const once = vectors.mojibake().filter((c) => c.note.endsWith("garbled 1x"));
  assert.equal(once.length, 12);
  for (const c of once) assert.equal(garble(c.expected), c.text);
});

test("Windows-1252 table", () => {
  assert.equal(DECODE.length, 256);
  assert.equal(DECODE[0x80], "€");
  assert.equal(DECODE[0x81], "\x81");
  assert.equal(DECODE[0x9f], "Ÿ");
  assert.equal(DECODE[0xe9], "é");
});

test("round limit and bad arguments", () => {
  const twice = garble(garble("José"));
  assert.equal(repair(twice, 1).text, garble("José"));
  assert.equal(repair(twice, 0).rounds, 0);
  assert.throws(() => repair("x", -1), RangeError);
  assert.throws(() => repair("x", 11), RangeError);
  assert.throws(() => repair("x", 1.5), RangeError);
  assert.equal(unwindOnce("山"), null);
  assert.equal(unwindOnce("é"), null);
  assert.equal(unwindOnce("Ã©"), "é");
});

test("invalid input is rejected", () => {
  assert.throws(() => measure("a\uD800"), /lone surrogate/);
  assert.throws(() => garble("\uDC80"), /lone surrogate/);
  assert.throws(() => measure(null), TypeError);
  assert.throws(() => repair(42), TypeError);
  assert.throws(() => graphemes("a".repeat(MAX_LENGTH + 1)), RangeError);
});

test("graphemes on known strings", () => {
  assert.deepEqual(graphemes(""), []);
  assert.deepEqual(graphemes("éx"), ["é", "x"]);
  assert.deepEqual(graphemes("\r\n\n"), ["\r\n", "\n"]);
  assert.equal("👍🏽".length, 4);
  assert.equal(graphemes("👍🏽").length, 1);
});

test("vector loaders reject malformed files", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "uth-"));
  try {
    assert.throws(() => vectors.grapheme(dir), /not found/);
    fs.writeFileSync(path.join(dir, "grapheme.txt"), "# only a comment\n");
    assert.throws(() => vectors.grapheme(dir), /no cases/);
    fs.writeFileSync(path.join(dir, "normalization.txt"), "0041;0041;0041\n");
    assert.throws(() => vectors.normalization(dir), /5 fields/);
    fs.writeFileSync(path.join(dir, "mojibake.tsv"), "0041\t0041\tx\tnote\n");
    assert.throws(() => vectors.mojibake(dir), /mojibake\.tsv:1/);
    fs.writeFileSync(path.join(dir, "encoding.tsv"), "x\t0041\t1\t1\t1\n");
    assert.throws(() => vectors.encoding(dir), /encoding\.tsv:1/);
    fs.writeFileSync(path.join(dir, "collation.txt"), Buffer.alloc(vectors.MAX_FILE_BYTES + 1, 0x41));
    assert.throws(() => vectors.collation(dir), /too large/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("unhex and versions", () => {
  assert.equal(vectors.unhex(""), "");
  assert.equal(vectors.unhex("0041 1F600"), "A\u{1F600}");
  assert.throws(() => vectors.unhex("XYZ"), vectors.VectorError);
  assert.throws(() => vectors.unhex("110000"), vectors.VectorError);
  assert.throws(() => vectors.versionOf("fifteen"), vectors.VectorError);
  assert.deepEqual([...vectors.expectedDeviations("js", "grapheme", "Intl.Segmenter", "17.0")], ["2701 200D 2701"]);
  assert.equal(vectors.expectedDeviations("js", "grapheme", "Intl.Segmenter", "16.0").size, 0);
  assert.equal(vectors.compareVersions([17], [17, 0]), 0);
});

/** Run the CLI and capture its output. */
function cli(...args) {
  const out = [];
  const err = [];
  const code = run(args, (l) => out.push(l), (l) => err.push(l));
  return { code, out: out.join("\n"), err: err.join("\n") };
}

test("command line", () => {
  assert.match(cli("samples").out, /family-zwj\t25\t11\t7\t1\t11/);
  assert.match(cli("repair", "JosÃ©").out, /José\t\(rounds undone: 1\)/);
  assert.match(cli("report").out, /js\tnormalization\tString\.normalize NFC\t19074\t19074/);
  assert.equal(cli("measure", "a\uD800").code, 1);
  assert.equal(cli("frobnicate").code, 2);
  assert.equal(cli("measure").code, 2);
  const missing = cli("--vectors", "does-not-exist", "samples");
  assert.equal(missing.code, 1);
  assert.match(missing.err, /not found/);
});
