package portfolio.unicodetexthandling;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Loaders for the shared test vectors in spec/vectors (the same files Python and JavaScript read). */
public final class Vectors {
    /** Largest vector file accepted. */
    public static final long MAX_FILE_BYTES = 4L * 1024 * 1024;

    private Vectors() {}

    /** A vector file is missing, too large or malformed. */
    public static final class VectorException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        /** New error with a message. */
        public VectorException(String message) {
            super(message);
        }

        /** New error with a message and cause. */
        public VectorException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    /** One NormalizationTest line: c1..c5. */
    public record NormalizationCase(int line, String part, List<String> columns) {}

    /** One GraphemeBreakTest line: the expected clusters. */
    public record GraphemeCase(int line, String key, List<String> clusters) {
        /** The whole string being segmented. */
        public String text() {
            return String.join("", clusters);
        }
    }

    /** Garbled input, expected repair and the number of repair rounds. */
    public record MojibakeCase(int line, String text, String expected, int rounds, String note) {}

    /** A sample string with its expected counts. */
    public record EncodingSample(
            int line, String name, String text, int utf8Bytes, int utf16Units, int codePoints, int graphemes) {}

    /** A numbered data line. */
    private record Line(int number, String text) {}

    /** Default vector directory: system property uth.vectors, else ../spec/vectors. */
    public static Path defaultDir() {
        return Path.of(System.getProperty("uth.vectors", "../spec/vectors"));
    }

    /** Text from space-separated hex code points (empty field = empty string). */
    public static String unhex(String field, int line) {
        StringBuilder sb = new StringBuilder();
        for (String h : field.trim().split("\\s+")) {
            if (h.isEmpty()) {
                continue;
            }
            int cp;
            try {
                cp = Integer.parseInt(h, 16);
            } catch (NumberFormatException e) {
                throw new VectorException("line " + line + ": bad hex in '" + field + "'", e);
            }
            if (cp < 0 || cp > Character.MAX_CODE_POINT) {
                throw new VectorException("line " + line + ": code point out of range in '" + field + "'");
            }
            sb.appendCodePoint(cp);
        }
        return sb.toString();
    }

    /** "15.1.0" to {15, 1, 0}. */
    public static int[] versionOf(String text) {
        try {
            return Arrays.stream(text.split("\\.")).mapToInt(Integer::parseInt).toArray();
        } catch (NumberFormatException e) {
            throw new VectorException("bad version '" + text + "'", e);
        }
    }

    /** Numbered non-comment, non-blank lines of a vector file. */
    private static List<Line> lines(Path path) {
        try {
            if (!Files.isRegularFile(path)) {
                throw new VectorException("vector file not found: " + path);
            }
            if (Files.size(path) > MAX_FILE_BYTES) {
                throw new VectorException("vector file too large: " + path);
            }
            List<String> raw = Files.readAllLines(path, StandardCharsets.UTF_8);
            List<Line> out = new ArrayList<>();
            for (int i = 0; i < raw.size(); i++) {
                String ln = raw.get(i);
                if (!ln.isBlank() && !ln.startsWith("#")) {
                    out.add(new Line(i + 1, ln));
                }
            }
            return out;
        } catch (IOException e) {
            throw new UncheckedIOException("cannot read " + path, e);
        }
    }

    /** The '@baseline name value' directives of a vector file. */
    public static Map<String, Integer> baselines(Path path) {
        Map<String, Integer> out = new HashMap<>();
        for (Line l : lines(path)) {
            if (l.text().startsWith("@baseline")) {
                String[] p = l.text().split("\\s+");
                if (p.length != 3 || !p[2].chars().allMatch(Character::isDigit)) {
                    throw new VectorException(path.getFileName() + ":" + l.number() + ": bad baseline");
                }
                out.put(p[1], Integer.parseInt(p[2]));
            }
        }
        return out;
    }

    /** Cases from normalization.txt. */
    public static List<NormalizationCase> normalization(Path dir) {
        String part = "";
        List<NormalizationCase> out = new ArrayList<>();
        for (Line l : lines(dir.resolve("normalization.txt"))) {
            if (l.text().startsWith("@part")) {
                part = l.text().split("\\s+")[1];
                continue;
            }
            String[] f = l.text().split(";", -1);
            if (f.length != 5) {
                throw new VectorException("normalization.txt:" + l.number() + ": expected 5 fields");
            }
            List<String> cols = new ArrayList<>();
            for (String x : f) {
                cols.add(unhex(x, l.number()));
            }
            out.add(new NormalizationCase(l.number(), part, List.copyOf(cols)));
        }
        if (out.isEmpty()) {
            throw new VectorException("normalization.txt has no cases");
        }
        return out;
    }

    /** Cases from grapheme.txt. */
    public static List<GraphemeCase> grapheme(Path dir) {
        List<GraphemeCase> out = new ArrayList<>();
        for (Line l : lines(dir.resolve("grapheme.txt"))) {
            if (l.text().startsWith("@")) {
                continue;
            }
            List<String> clusters = new ArrayList<>();
            for (String c : l.text().split("\\|", -1)) {
                String s = unhex(c, l.number());
                if (s.isEmpty()) {
                    throw new VectorException("grapheme.txt:" + l.number() + ": empty cluster");
                }
                clusters.add(s);
            }
            out.add(new GraphemeCase(l.number(), l.text().replace('|', ' '), List.copyOf(clusters)));
        }
        if (out.isEmpty()) {
            throw new VectorException("grapheme.txt has no cases");
        }
        return out;
    }

    /** Strings from collation.txt, in DUCET order. */
    public static List<String> collation(Path dir) {
        List<String> out = new ArrayList<>();
        for (Line l : lines(dir.resolve("collation.txt"))) {
            if (!l.text().startsWith("@")) {
                out.add(unhex(l.text(), l.number()));
            }
        }
        if (out.size() < 2) {
            throw new VectorException("collation.txt needs at least two strings");
        }
        return out;
    }

    /** Cases from mojibake.tsv. */
    public static List<MojibakeCase> mojibake(Path dir) {
        List<MojibakeCase> out = new ArrayList<>();
        for (Line l : lines(dir.resolve("mojibake.tsv"))) {
            String[] f = l.text().split("\t", -1);
            if (f.length != 4 || f[2].isEmpty() || !f[2].chars().allMatch(Character::isDigit)) {
                throw new VectorException("mojibake.tsv:" + l.number() + ": expected input, expected, rounds, note");
            }
            out.add(new MojibakeCase(
                    l.number(), unhex(f[0], l.number()), unhex(f[1], l.number()), Integer.parseInt(f[2]), f[3]));
        }
        return out;
    }

    /** Samples from encoding.tsv. */
    public static List<EncodingSample> encoding(Path dir) {
        List<EncodingSample> out = new ArrayList<>();
        for (Line l : lines(dir.resolve("encoding.tsv"))) {
            String[] f = l.text().split("\t", -1);
            if (f.length != 6) {
                throw new VectorException("encoding.tsv:" + l.number() + ": expected name, hex, 4 counts");
            }
            int[] n = new int[4];
            for (int i = 0; i < 4; i++) {
                try {
                    n[i] = Integer.parseInt(f[i + 2]);
                } catch (NumberFormatException e) {
                    throw new VectorException("encoding.tsv:" + l.number() + ": bad count", e);
                }
            }
            out.add(new EncodingSample(l.number(), f[0], unhex(f[1], l.number()), n[0], n[1], n[2], n[3]));
        }
        return out;
    }

    /** Lexicographic comparison of version numbers. */
    static int compareVersions(int[] a, int[] b) {
        return Arrays.compare(a, b);
    }

    /** Case keys documented to differ for this API on a runtime with this Unicode version. */
    public static Set<String> expectedDeviations(Path dir, String language, String suite, String api, String unicode) {
        int[] runtime = versionOf(unicode);
        Set<String> out = new HashSet<>();
        for (Line l : lines(dir.resolve("known-deviations.tsv"))) {
            String[] f = l.text().split("\t", -1);
            if (f.length != 6) {
                throw new VectorException("known-deviations.tsv:" + l.number() + ": expected 6 fields");
            }
            if (f[0].equals(language) && f[1].equals(suite) && f[2].equals(api)
                    && compareVersions(runtime, versionOf(f[4])) >= 0) {
                out.add(f[3]);
            }
        }
        return out;
    }

    /** Unicode version implemented by this JDK's java.lang.Character, java.text and java.util.regex. */
    public static String runtimeUnicode() {
        int feature = Runtime.version().feature();
        if (feature <= 21) {
            return "15.0";
        }
        if (feature <= 23) {
            return "15.1";
        }
        if (feature <= 25) {
            return "16.0";
        }
        return "17.0";
    }
}
