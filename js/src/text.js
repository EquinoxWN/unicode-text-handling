// Grapheme segmentation (Intl.Segmenter), the four 'lengths' of a string, and mojibake repair.

export const MAX_LENGTH = 2_000_000;
export const MAX_ROUNDS = 3;

const segmenter = new Intl.Segmenter("und", { granularity: "grapheme" });

// Windows-1252 bytes 0x80..0x9F (WHATWG Encoding Standard); undefined bytes map to the C1 control.
const HIGH =
  "€\u0081‚ƒ„…†‡ˆ‰Š‹Œ\u008dŽ\u008f" +
  "\u0090‘’“”•–—˜™š›œ\u009džŸ";
export const DECODE = Array.from({ length: 256 }, (_, b) =>
  b >= 0x80 && b < 0xa0 ? HIGH[b - 0x80] : String.fromCharCode(b),
);
const ENCODE = new Map(DECODE.map((ch, b) => [ch, b]));

/** Validate the input type and size. */
function check(text) {
  if (typeof text !== "string") throw new TypeError(`expected string, got ${typeof text}`);
  if (text.length > MAX_LENGTH) throw new RangeError(`text longer than ${MAX_LENGTH} UTF-16 units`);
  return text;
}

/** Validate and reject lone surrogates. */
function checkWellFormed(text) {
  check(text);
  if (!text.isWellFormed()) throw new RangeError("lone surrogate: not well-formed text");
  return text;
}

/** Clusters from Intl.Segmenter (ICU). */
export function graphemes(text) {
  check(text);
  return Array.from(segmenter.segment(text), (s) => s.segment);
}

/** Naive split: one code point per character ([...text]). */
export function codePoints(text) {
  return [...check(text)];
}

/** Naive split: one UTF-16 unit per character (text.length). */
export function utf16Units(text) {
  return check(text).split("");
}

/** UTF-8 bytes, UTF-16 units, code points and grapheme clusters of a string. */
export function measure(text) {
  checkWellFormed(text);
  return {
    utf8Bytes: Buffer.byteLength(text, "utf8"),
    utf16Units: text.length,
    codePoints: [...text].length,
    graphemes: graphemes(text).length,
  };
}

/** Encode as UTF-8 and decode as Windows-1252: what a mis-configured reader shows. */
export function garble(text) {
  checkWellFormed(text);
  return Array.from(Buffer.from(text, "utf8"), (b) => DECODE[b]).join("");
}

const strictUtf8 = new TextDecoder("utf-8", { fatal: true });

/** Undo one round, or null if text is not Windows-1252-encodable valid UTF-8. */
export function unwindOnce(text) {
  const bytes = new Uint8Array(text.length);
  for (let i = 0; i < text.length; i++) {
    const b = ENCODE.get(text[i]);
    if (b === undefined) return null;
    bytes[i] = b;
  }
  try {
    return strictUtf8.decode(bytes);
  } catch (err) {
    if (err instanceof TypeError) return null; // not UTF-8 underneath: this text is not mojibake
    throw err;
  }
}

/** Undo up to maxRounds of UTF-8-read-as-Windows-1252, stopping when a round would not apply. */
export function repair(text, maxRounds = MAX_ROUNDS) {
  check(text);
  if (!Number.isInteger(maxRounds) || maxRounds < 0 || maxRounds > 10) {
    throw new RangeError("maxRounds must be an integer between 0 and 10");
  }
  let rounds = 0;
  while (rounds < maxRounds) {
    const fixed = unwindOnce(text);
    if (fixed === null || fixed === text) break;
    text = fixed;
    rounds++;
  }
  return { text, rounds };
}
