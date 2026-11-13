// Loaders for the shared test vectors in spec/vectors (the same files Java and Python read).
import fs from "node:fs";
import { fileURLToPath } from "node:url";

export const MAX_FILE_BYTES = 4 * 1024 * 1024;
export const DEFAULT_DIR = fileURLToPath(new URL("../../spec/vectors/", import.meta.url));

/** A vector file is missing, too large or malformed. */
export class VectorError extends Error {}

/** Text from space-separated hex code points (empty field = empty string). */
export function unhex(field, line = 0) {
  const parts = field.trim().split(/\s+/).filter(Boolean);
  return parts
    .map((h) => {
      if (!/^[0-9A-Fa-f]{1,6}$/.test(h)) throw new VectorError(`line ${line}: bad hex in '${field}'`);
      const cp = parseInt(h, 16);
      if (cp > 0x10ffff) throw new VectorError(`line ${line}: code point out of range in '${field}'`);
      return String.fromCodePoint(cp);
    })
    .join("");
}

/** "15.1.0" to [15, 1, 0]. */
export function versionOf(text) {
  const parts = String(text).split(".");
  if (!parts.every((p) => /^\d+$/.test(p))) throw new VectorError(`bad version '${text}'`);
  return parts.map(Number);
}

/** Negative, zero or positive, comparing versions part by part. */
export function compareVersions(a, b) {
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const d = (a[i] ?? 0) - (b[i] ?? 0);
    if (d !== 0) return d;
  }
  return 0;
}

/** Numbered non-comment, non-blank lines of a vector file. */
function lines(path) {
  let stat;
  try {
    stat = fs.statSync(path);
  } catch (err) {
    if (err.code === "ENOENT") throw new VectorError(`vector file not found: ${path}`);
    throw err;
  }
  if (stat.size > MAX_FILE_BYTES) throw new VectorError(`vector file too large: ${path}`);
  return fs
    .readFileSync(path, "utf8")
    .split("\n")
    .map((text, i) => ({ n: i + 1, text: text.replace(/\r$/, "") }))
    .filter(({ text }) => text.trim() !== "" && !text.startsWith("#"));
}

/** Join a directory and file name. */
function file(dir, name) {
  return dir.endsWith("/") || dir.endsWith("\\") ? dir + name : `${dir}/${name}`;
}

/** The '@baseline name value' directives of a vector file. */
export function baselines(dir, name) {
  const out = {};
  for (const { n, text } of lines(file(dir, name))) {
    if (!text.startsWith("@baseline")) continue;
    const p = text.split(/\s+/);
    if (p.length !== 3 || !/^\d+$/.test(p[2])) throw new VectorError(`${name}:${n}: bad baseline`);
    out[p[1]] = Number(p[2]);
  }
  return out;
}

/** Cases from normalization.txt: {line, part, columns}. */
export function normalization(dir = DEFAULT_DIR) {
  let part = "";
  const out = [];
  for (const { n, text } of lines(file(dir, "normalization.txt"))) {
    if (text.startsWith("@part")) {
      part = text.split(/\s+/)[1];
      continue;
    }
    const f = text.split(";");
    if (f.length !== 5) throw new VectorError(`normalization.txt:${n}: expected 5 fields`);
    out.push({ line: n, part, columns: f.map((x) => unhex(x, n)) });
  }
  if (out.length === 0) throw new VectorError("normalization.txt has no cases");
  return out;
}

/** Cases from grapheme.txt: {line, key, clusters}. */
export function grapheme(dir = DEFAULT_DIR) {
  const out = [];
  for (const { n, text } of lines(file(dir, "grapheme.txt"))) {
    if (text.startsWith("@")) continue;
    const clusters = text.split("|").map((c) => unhex(c, n));
    if (clusters.some((c) => c === "")) throw new VectorError(`grapheme.txt:${n}: empty cluster`);
    out.push({ line: n, key: text.replaceAll("|", " "), clusters });
  }
  if (out.length === 0) throw new VectorError("grapheme.txt has no cases");
  return out;
}

/** Strings from collation.txt, in DUCET order. */
export function collation(dir = DEFAULT_DIR) {
  const out = lines(file(dir, "collation.txt"))
    .filter(({ text }) => !text.startsWith("@"))
    .map(({ n, text }) => unhex(text, n));
  if (out.length < 2) throw new VectorError("collation.txt needs at least two strings");
  return out;
}

/** Cases from mojibake.tsv: {line, text, expected, rounds, note}. */
export function mojibake(dir = DEFAULT_DIR) {
  return lines(file(dir, "mojibake.tsv")).map(({ n, text }) => {
    const f = text.split("\t");
    if (f.length !== 4 || !/^\d+$/.test(f[2])) {
      throw new VectorError(`mojibake.tsv:${n}: expected input, expected, rounds, note`);
    }
    return { line: n, text: unhex(f[0], n), expected: unhex(f[1], n), rounds: Number(f[2]), note: f[3] };
  });
}

/** Samples from encoding.tsv. */
export function encoding(dir = DEFAULT_DIR) {
  return lines(file(dir, "encoding.tsv")).map(({ n, text }) => {
    const f = text.split("\t");
    if (f.length !== 6 || !f.slice(2).every((x) => /^\d+$/.test(x))) {
      throw new VectorError(`encoding.tsv:${n}: expected name, hex, 4 counts`);
    }
    const [utf8Bytes, utf16Units, codePoints, graphemes] = f.slice(2).map(Number);
    return { line: n, name: f[0], text: unhex(f[1], n), utf8Bytes, utf16Units, codePoints, graphemes };
  });
}

/** Case keys documented to differ for this API on a runtime with this Unicode version. */
export function expectedDeviations(language, suite, api, unicodeVersion, dir = DEFAULT_DIR) {
  const runtime = versionOf(unicodeVersion);
  const out = new Set();
  for (const { n, text } of lines(file(dir, "known-deviations.tsv"))) {
    const f = text.split("\t");
    if (f.length !== 6) throw new VectorError(`known-deviations.tsv:${n}: expected 6 fields`);
    if (f[0] === language && f[1] === suite && f[2] === api && compareVersions(runtime, versionOf(f[4])) >= 0) {
      out.add(f[3]);
    }
  }
  return out;
}
