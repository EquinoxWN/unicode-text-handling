package portfolio.unicodetexthandling;

import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

/** Command line: report | samples | measure TEXT... | repair TEXT... [--vectors DIR first]. */
public final class App {
    private App() {}

    /** One table row for measure and samples. */
    static String measureRow(String label, String text) {
        TextMeasure.Measurement m = TextMeasure.measure(text);
        return label + "\t" + m.utf8Bytes() + "\t" + m.utf16Units() + "\t" + m.codePoints() + "\t" + m.graphemes();
    }

    /** Run one command; returns the exit code. */
    static int run(String[] argv, PrintStream out, PrintStream err) {
        List<String> args = Arrays.asList(argv);
        Path dir = Vectors.defaultDir();
        if (args.size() >= 2 && args.get(0).equals("--vectors")) {
            dir = Path.of(args.get(1));
            args = args.subList(2, args.size());
        }
        if (args.isEmpty()) {
            err.println("usage: App [--vectors DIR] report | samples | measure TEXT... | repair TEXT...");
            return 2;
        }
        List<String> rest = args.subList(1, args.size());
        try {
            switch (args.get(0)) {
                case "report" -> {
                    out.println("language\tsuite\tapi\tcases\tpassed");
                    Conformance.report(dir).forEach(r -> out.println(r.tsv()));
                }
                case "samples" -> {
                    out.println("sample\tutf8_bytes\tutf16_units\tcode_points\tgraphemes\tlength()");
                    for (Vectors.EncodingSample s : Vectors.encoding(dir)) {
                        out.println(measureRow(s.name(), s.text()) + "\t" + s.text().length());
                    }
                }
                case "measure" -> {
                    if (rest.isEmpty()) {
                        err.println("measure needs at least one TEXT");
                        return 2;
                    }
                    out.println("text\tutf8_bytes\tutf16_units\tcode_points\tgraphemes");
                    rest.forEach(t -> out.println(measureRow(t, t)));
                }
                case "repair" -> {
                    if (rest.isEmpty()) {
                        err.println("repair needs at least one TEXT");
                        return 2;
                    }
                    for (String t : rest) {
                        Mojibake.Repair r = Mojibake.repair(t);
                        out.println(r.text() + "\t(rounds undone: " + r.rounds() + ")");
                    }
                }
                default -> {
                    err.println("unknown command: " + args.get(0));
                    return 2;
                }
            }
        } catch (IllegalArgumentException | UncheckedIOException | Vectors.VectorException e) {
            err.println("error: " + e.getMessage());
            return 1;
        }
        return 0;
    }

    /** Entry point; prints UTF-8 whatever the console code page is. */
    public static void main(String[] args) {
        PrintStream out = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8);
        PrintStream err = new PrintStream(new FileOutputStream(FileDescriptor.err), true, StandardCharsets.UTF_8);
        int code = run(args, out, err);
        if (code != 0) {
            System.exit(code);
        }
    }
}
