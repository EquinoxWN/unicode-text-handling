package portfolio.unicodetexthandling;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.text.Normalizer;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import portfolio.unicodetexthandling.Vectors.NormalizationCase;

/** NormalizationTest.txt (Unicode 15.0.0) against java.text.Normalizer. */
class NormalizationConformanceTest {
    static final List<NormalizationCase> CASES = Vectors.normalization(VectorsTest.DIR);

    @ParameterizedTest
    @EnumSource(Normalizer.Form.class)
    void normalizerPassesEveryCase(Normalizer.Form form) {
        List<Integer> expected = Vectors.expectedDeviations(
                        VectorsTest.DIR, "java", "normalization", "Normalizer " + form, Vectors.runtimeUnicode())
                .stream().map(Integer::parseInt).sorted().toList();
        assertEquals(expected, Conformance.normalizationFailures(CASES, form));
    }

    @ParameterizedTest
    @EnumSource(Normalizer.Form.class)
    void harnessCatchesANormalizerThatDoesNothing(Normalizer.Form form) {
        assertTrue(Conformance.normalizationFailures(CASES, form, (f, s) -> s).size() > 1000);
    }

    @ParameterizedTest
    @EnumSource(Normalizer.Form.class)
    void harnessCatchesComposedAndDecomposedSwapped(Normalizer.Form form) {
        assertFalse(Conformance.normalizationFailures(CASES, form, (f, s) -> Normalizer.normalize(s, swap(f)))
                .isEmpty());
    }

    @ParameterizedTest
    @EnumSource(Normalizer.Form.class)
    void everyColumnIsChecked(Normalizer.Form form) {
        // A normalizer that is wrong only on column k (in a case where that string occurs once) must fail.
        for (int k = 0; k < 5; k++) {
            int col = k;
            NormalizationCase c = CASES.stream()
                    .filter(x -> Collections.frequency(x.columns(), x.columns().get(col)) == 1)
                    .findFirst()
                    .orElseThrow();
            String bad = c.columns().get(col);
            List<Integer> failures = Conformance.normalizationFailures(
                    List.of(c), form, (f, s) -> s.equals(bad) ? "�" : Normalizer.normalize(s, f));
            assertEquals(List.of(c.line()), failures, "column c" + (k + 1));
        }
    }

    /** NFC to NFD, NFKC to NFKD and back. */
    private static Normalizer.Form swap(Normalizer.Form f) {
        return switch (f) {
            case NFC -> Normalizer.Form.NFD;
            case NFD -> Normalizer.Form.NFC;
            case NFKC -> Normalizer.Form.NFKD;
            case NFKD -> Normalizer.Form.NFKC;
        };
    }
}
