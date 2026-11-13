// Shared vectors (Unicode 15.0.0) against String.normalize, Intl.Segmenter and the sort orders.
import test from "node:test";
import assert from "node:assert/strict";
import * as vectors from "../src/vectors.js";
import {
  FORMS,
  compareCodePoints,
  compareUtf16,
  graphemeFailures,
  inOrderPairs,
  normalizationFailures,
} from "../src/conformance.js";
import { codePoints, graphemes, utf16Units } from "../src/text.js";

const UNICODE = process.versions.unicode;
const NORM = vectors.normalization();
const GRAPH = vectors.grapheme();
const ORDER = vectors.collation();
const GB = vectors.baselines(vectors.DEFAULT_DIR, "grapheme.txt");
const CB = vectors.baselines(vectors.DEFAULT_DIR, "collation.txt");
const SWAP = { NFC: "NFD", NFD: "NFC", NFKC: "NFKD", NFKD: "NFKC" };

for (const form of FORMS) {
  test(`String.normalize ${form} passes every case`, () => {
    const expected = [...vectors.expectedDeviations("js", "normalization", `String.normalize ${form}`, UNICODE)];
    assert.deepEqual(normalizationFailures(NORM, form), expected.map(Number).sort((a, b) => a - b));
  });

  test(`harness catches broken ${form} normalizers`, () => {
    assert.ok(normalizationFailures(NORM, form, (s) => s).length > 1000);
    assert.ok(normalizationFailures(NORM, form, (s, f) => s.normalize(SWAP[f])).length > 0);
  });

  test(`${form}: a normalizer wrong on any one column fails the case`, () => {
    for (let k = 0; k < 5; k++) {
      const c = NORM.find((x) => x.columns.filter((s) => s === x.columns[k]).length === 1);
      const bad = c.columns[k];
      const wrong = (s, f) => (s === bad ? "�" : s.normalize(f));
      assert.deepEqual(normalizationFailures([c], form, wrong), [c.line], `column c${k + 1}`);
    }
  });
}

test("unknown normalization form is rejected", () => {
  assert.throws(() => normalizationFailures(NORM.slice(0, 1), "NFX"), RangeError);
});

test("Intl.Segmenter passes every case except the documented deviations", () => {
  const expected = [...vectors.expectedDeviations("js", "grapheme", "Intl.Segmenter", UNICODE)].sort();
  assert.deepEqual(graphemeFailures(GRAPH, graphemes).sort(), expected);
});

test("naive splits get exactly the baseline counts right", () => {
  assert.equal(GRAPH.length - graphemeFailures(GRAPH, codePoints).length, GB.codepoint_exact);
  assert.equal(GRAPH.length - graphemeFailures(GRAPH, utf16Units).length, GB.utf16_exact);
});

test("graphemeFailures notices a missing or extra cluster", () => {
  const c = [{ key: "k", clusters: ["a", "b"] }];
  assert.deepEqual(graphemeFailures(c, () => ["a"]), ["k"]);
  assert.deepEqual(graphemeFailures(c, () => ["a", "b", ""]), ["k"]);
  assert.deepEqual(graphemeFailures(c, () => ["a", "b"]), []);
});

test("default sort and code point order match the recorded baselines", () => {
  assert.equal(inOrderPairs(ORDER, compareUtf16), CB.utf16_in_order);
  assert.equal(inOrderPairs(ORDER, compareCodePoints), CB.codepoint_in_order);
});

test("code point and UTF-16 order differ above the BMP", () => {
  assert.ok(compareUtf16("\u{1F600}", "") < 0);
  assert.ok(compareCodePoints("\u{1F600}", "") > 0);
  assert.ok(compareCodePoints("ab", "a") > 0);
  assert.equal(compareCodePoints("a", "a"), 0);
});

test("Intl.Collator is much closer to the UCA than binary order", () => {
  const icu = inOrderPairs(ORDER, new Intl.Collator("und").compare);
  assert.ok(icu > CB.utf16_in_order, `Intl.Collator in order: ${icu}`);
});

test("inOrderPairs counts each adjacent pair", () => {
  assert.equal(inOrderPairs(["a", "b", "c"], compareUtf16), 2);
  assert.equal(inOrderPairs(["c", "b", "a"], compareUtf16), 0);
  assert.equal(inOrderPairs(["a", "a"], compareUtf16), 1);
  assert.equal(inOrderPairs(["a"], compareUtf16), 0);
});

test("default sort puts case and accents where readers do not expect", () => {
  const words = ["zebra", "Zoo", "éclair", "apple"];
  assert.deepEqual([...words].sort(), ["Zoo", "apple", "zebra", "éclair"]);
  assert.deepEqual([...words].sort(new Intl.Collator("en").compare), ["apple", "éclair", "zebra", "Zoo"]);
});
