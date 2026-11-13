// Run the shared Unicode vectors against JavaScript's APIs and report where each one disagrees.
import * as vectors from "./vectors.js";
import { codePoints, graphemes, utf16Units } from "./text.js";

export const FORMS = ["NFC", "NFD", "NFKC", "NFKD"];

/** The NormalizationTest.txt invariants for one form. */
export function normalizationOk({ columns }, form, norm) {
  const [c1, c2, c3, c4, c5] = columns;
  const f = (s) => norm(s, form);
  const eq = (first, ...rest) => rest.every((s) => s === first);
  if (form === "NFC") return eq(c2, f(c1), f(c2), f(c3)) && eq(c4, f(c4), f(c5));
  if (form === "NFD") return eq(c3, f(c1), f(c2), f(c3)) && eq(c5, f(c4), f(c5));
  if (form === "NFKC") return columns.every((c) => c4 === f(c));
  if (form === "NFKD") return columns.every((c) => c5 === f(c));
  throw new RangeError(`unknown form ${form}`);
}

/** Line numbers of cases that break the invariants for form. */
export function normalizationFailures(cases, form, norm = (s, f) => s.normalize(f)) {
  return cases.filter((c) => !normalizationOk(c, form, norm)).map((c) => c.line);
}

/** Keys of cases the segmenter splits differently from the vectors. */
export function graphemeFailures(cases, segment) {
  return cases
    .filter((c) => {
      const got = segment(c.clusters.join(""));
      return got.length !== c.clusters.length || got.some((s, i) => s !== c.clusters[i]);
    })
    .map((c) => c.key);
}

/** Adjacent pairs that the comparator keeps in order. */
export function inOrderPairs(items, compare) {
  let ok = 0;
  for (let i = 1; i < items.length; i++) if (compare(items[i - 1], items[i]) <= 0) ok++;
  return ok;
}

/** UTF-16 code unit order, as the default Array.prototype.sort uses. */
export function compareUtf16(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Code point order. */
export function compareCodePoints(a, b) {
  const x = [...a];
  const y = [...b];
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const d = x[i].codePointAt(0) - y[i].codePointAt(0);
    if (d !== 0) return d;
  }
  return x.length - y.length;
}

/** Every suite against every JavaScript API. */
export function report(dir = vectors.DEFAULT_DIR) {
  const rows = [];
  const row = (suite, api, cases, passed) => rows.push({ language: "js", suite, api, cases, passed });
  const norm = vectors.normalization(dir);
  for (const form of FORMS) {
    row("normalization", `String.normalize ${form}`, norm.length, norm.length - normalizationFailures(norm, form).length);
  }
  const g = vectors.grapheme(dir);
  for (const [api, seg] of [
    ["Intl.Segmenter", graphemes],
    ["[...str] code points", codePoints],
    ["str.length (UTF-16)", utf16Units],
  ]) {
    row("grapheme", api, g.length, g.length - graphemeFailures(g, seg).length);
  }
  const coll = vectors.collation(dir);
  const und = new Intl.Collator("und");
  row("collation", "Intl.Collator und", coll.length - 1, inOrderPairs(coll, und.compare));
  row("collation", "sort() default (UTF-16)", coll.length - 1, inOrderPairs(coll, compareUtf16));
  return rows;
}
