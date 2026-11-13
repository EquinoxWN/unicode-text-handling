// Command line: node src/cli.js [--vectors DIR] report | samples | measure TEXT... | repair TEXT...
import { pathToFileURL } from "node:url";
import { report } from "./conformance.js";
import { measure, repair } from "./text.js";
import * as vectors from "./vectors.js";

/** One table row for measure and samples. */
function measureRow(label, text) {
  const m = measure(text);
  return `${label}\t${m.utf8Bytes}\t${m.utf16Units}\t${m.codePoints}\t${m.graphemes}`;
}

/** Run one command; returns the exit code. */
export function run(argv, out = console.log, err = console.error) {
  let args = argv;
  let dir = vectors.DEFAULT_DIR;
  if (args[0] === "--vectors" && args.length >= 2) {
    dir = args[1];
    args = args.slice(2);
  }
  const [cmd, ...rest] = args;
  try {
    if (cmd === "report") {
      out("language\tsuite\tapi\tcases\tpassed");
      for (const r of report(dir)) out(`${r.language}\t${r.suite}\t${r.api}\t${r.cases}\t${r.passed}`);
    } else if (cmd === "samples") {
      out("sample\tutf8_bytes\tutf16_units\tcode_points\tgraphemes\t.length");
      for (const s of vectors.encoding(dir)) out(`${measureRow(s.name, s.text)}\t${s.text.length}`);
    } else if ((cmd === "measure" || cmd === "repair") && rest.length > 0) {
      if (cmd === "measure") {
        out("text\tutf8_bytes\tutf16_units\tcode_points\tgraphemes");
        for (const t of rest) out(measureRow(t, t));
      } else {
        for (const t of rest) {
          const r = repair(t);
          out(`${r.text}\t(rounds undone: ${r.rounds})`);
        }
      }
    } else {
      err("usage: cli.js [--vectors DIR] report | samples | measure TEXT... | repair TEXT...");
      return 2;
    }
  } catch (e) {
    if (e instanceof vectors.VectorError || e instanceof RangeError || e instanceof TypeError) {
      err(`error: ${e.message}`);
      return 1;
    }
    throw e;
  }
  return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = run(process.argv.slice(2));
}
