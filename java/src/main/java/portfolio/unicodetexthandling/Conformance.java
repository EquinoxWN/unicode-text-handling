package portfolio.unicodetexthandling;

import java.nio.file.Path;
import java.text.Collator;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.function.BiFunction;
import java.util.function.Function;
import portfolio.unicodetexthandling.Vectors.GraphemeCase;
import portfolio.unicodetexthandling.Vectors.NormalizationCase;

/** Run the shared Unicode vectors against Java's APIs and report where each one disagrees. */
public final class Conformance {
    private Conformance() {}

    /** One line of the conformance report. */
    public record Row(String language, String suite, String api, int cases, int passed) {
        /** Tab-separated form. */
        public String tsv() {
            return language + "\t" + suite + "\t" + api + "\t" + cases + "\t" + passed;
        }
    }

    /** The NormalizationTest.txt invariants for one form. */
    public static boolean normalizationOk(
            NormalizationCase c, Normalizer.Form form, BiFunction<Normalizer.Form, String, String> norm) {
        List<String> x = c.columns();
        Function<String, String> f = s -> norm.apply(form, s);
        return switch (form) {
            case NFC -> allEqual(x.get(1), f.apply(x.get(0)), f.apply(x.get(1)), f.apply(x.get(2)))
                    && allEqual(x.get(3), f.apply(x.get(3)), f.apply(x.get(4)));
            case NFD -> allEqual(x.get(2), f.apply(x.get(0)), f.apply(x.get(1)), f.apply(x.get(2)))
                    && allEqual(x.get(4), f.apply(x.get(3)), f.apply(x.get(4)));
            case NFKC -> x.stream().allMatch(s -> x.get(3).equals(f.apply(s)));
            case NFKD -> x.stream().allMatch(s -> x.get(4).equals(f.apply(s)));
        };
    }

    /** True when every value equals the first. */
    private static boolean allEqual(String first, String... rest) {
        for (String s : rest) {
            if (!first.equals(s)) {
                return false;
            }
        }
        return true;
    }

    /** Line numbers of cases that break the invariants for form. */
    public static List<Integer> normalizationFailures(
            List<NormalizationCase> cases, Normalizer.Form form, BiFunction<Normalizer.Form, String, String> norm) {
        List<Integer> out = new ArrayList<>();
        for (NormalizationCase c : cases) {
            if (!normalizationOk(c, form, norm)) {
                out.add(c.line());
            }
        }
        return out;
    }

    /** Failures with java.text.Normalizer. */
    public static List<Integer> normalizationFailures(List<NormalizationCase> cases, Normalizer.Form form) {
        return normalizationFailures(cases, form, (f, s) -> Normalizer.normalize(s, f));
    }

    /** Keys of cases the segmenter splits differently from the vectors. */
    public static List<String> graphemeFailures(List<GraphemeCase> cases, Function<String, List<String>> segment) {
        List<String> out = new ArrayList<>();
        for (GraphemeCase c : cases) {
            if (!segment.apply(c.text()).equals(c.clusters())) {
                out.add(c.key());
            }
        }
        return out;
    }

    /** Adjacent pairs that the comparator keeps in order. */
    public static <T> int inOrderPairs(List<T> items, Comparator<? super T> cmp) {
        int ok = 0;
        for (int i = 1; i < items.size(); i++) {
            if (cmp.compare(items.get(i - 1), items.get(i)) <= 0) {
                ok++;
            }
        }
        return ok;
    }

    /** Code point order (String.compareTo is UTF-16 order). */
    public static int compareCodePoints(String a, String b) {
        return java.util.Arrays.compare(a.codePoints().toArray(), b.codePoints().toArray());
    }

    /** Every suite against every Java API. */
    public static List<Row> report(Path dir) {
        List<Row> rows = new ArrayList<>();
        List<NormalizationCase> norm = Vectors.normalization(dir);
        for (Normalizer.Form form : Normalizer.Form.values()) {
            int bad = normalizationFailures(norm, form).size();
            rows.add(new Row("java", "normalization", "Normalizer " + form, norm.size(), norm.size() - bad));
        }
        List<GraphemeCase> g = Vectors.grapheme(dir);
        List<Row> seg = List.of(
                segRow(g, "BreakIterator", Graphemes::breakIterator),
                segRow(g, "regex \\X", Graphemes::regex),
                segRow(g, "codePoints()", Graphemes::codePoints),
                segRow(g, "chars (UTF-16)", Graphemes::chars));
        rows.addAll(seg);
        List<String> coll = Vectors.collation(dir);
        int pairs = coll.size() - 1;
        rows.add(new Row("java", "collation", "Collator ROOT", pairs, inOrderPairs(coll, Collator.getInstance(Locale.ROOT))));
        rows.add(new Row("java", "collation", "String.compareTo", pairs, inOrderPairs(coll, String::compareTo)));
        return rows;
    }

    /** One grapheme report row. */
    private static Row segRow(List<GraphemeCase> g, String api, Function<String, List<String>> f) {
        return new Row("java", "grapheme", api, g.size(), g.size() - graphemeFailures(g, f).size());
    }
}
