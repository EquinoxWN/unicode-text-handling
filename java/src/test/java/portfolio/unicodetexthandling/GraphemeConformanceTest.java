package portfolio.unicodetexthandling;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import portfolio.unicodetexthandling.Vectors.GraphemeCase;

/** GraphemeBreakTest.txt (Unicode 15.0.0) against BreakIterator and regex \X. */
class GraphemeConformanceTest {
    static final List<GraphemeCase> CASES = Vectors.grapheme(VectorsTest.DIR);
    static final Map<String, Integer> BASE = Vectors.baselines(VectorsTest.DIR.resolve("grapheme.txt"));
    static final Map<String, Function<String, List<String>>> APIS =
            Map.of("BreakIterator", Graphemes::breakIterator, "regex \\X", Graphemes::regex);

    @ParameterizedTest
    @ValueSource(strings = {"BreakIterator", "regex \\X"})
    void jdkSegmenterPassesEveryCase(String api) {
        List<String> expected = Vectors.expectedDeviations(
                        VectorsTest.DIR, "java", "grapheme", api, Vectors.runtimeUnicode())
                .stream().sorted().toList();
        assertEquals(expected, Conformance.graphemeFailures(CASES, APIS.get(api)).stream().sorted().toList());
    }

    @Test
    void naiveSplitsGetTheBaselineCountsRight() {
        int n = CASES.size();
        assertEquals(BASE.get("codepoint_exact"), n - Conformance.graphemeFailures(CASES, Graphemes::codePoints).size());
        assertEquals(BASE.get("utf16_exact"), n - Conformance.graphemeFailures(CASES, Graphemes::chars).size());
    }

    @Test
    void knownClusters() {
        assertEquals(List.of(), Graphemes.breakIterator(""));
        assertEquals(List.of("é", "x"), Graphemes.breakIterator("éx"));
        assertEquals(List.of("\r\n", "\n"), Graphemes.breakIterator("\r\n\n"));
        String flags = "🇯🇵";
        assertEquals(List.of(flags, "🇺"), Graphemes.breakIterator(flags + "🇺"));
        assertEquals(4, "👍🏽".length());
        assertEquals(1, Graphemes.regex("👍🏽").size());
    }

    @Test
    void invalidInputIsRejected() {
        assertThrows(NullPointerException.class, () -> Graphemes.breakIterator(null));
        assertThrows(IllegalArgumentException.class, () -> Graphemes.regex("a".repeat(Graphemes.MAX_LENGTH + 1)));
    }
}
