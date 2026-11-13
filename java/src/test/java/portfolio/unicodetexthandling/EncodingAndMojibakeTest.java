package portfolio.unicodetexthandling;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import portfolio.unicodetexthandling.Vectors.EncodingSample;
import portfolio.unicodetexthandling.Vectors.MojibakeCase;

/** Encoding experiment counts, mojibake repair and the command line. */
class EncodingAndMojibakeTest {
    static Stream<EncodingSample> samples() {
        return Vectors.encoding(VectorsTest.DIR).stream();
    }

    static Stream<MojibakeCase> mojibake() {
        return Vectors.mojibake(VectorsTest.DIR).stream();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("samples")
    void sampleCounts(EncodingSample s) {
        Set<String> deviating = Vectors.expectedDeviations(
                VectorsTest.DIR, "java", "encoding", "BreakIterator", Vectors.runtimeUnicode());
        TextMeasure.Measurement m = TextMeasure.measure(s.text());
        assertEquals(s.utf8Bytes(), m.utf8Bytes());
        assertEquals(s.utf16Units(), m.utf16Units());
        assertEquals(s.utf16Units(), s.text().length());
        assertEquals(s.codePoints(), m.codePoints());
        if (deviating.contains(s.name())) {
            assertTrue(m.graphemes() != s.graphemes(), "documented deviation no longer happens: " + s.name());
        } else {
            assertEquals(s.graphemes(), m.graphemes());
        }
    }

    @Test
    void loneSurrogateIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> TextMeasure.measure("a\uD800"));
        assertThrows(IllegalArgumentException.class, () -> Mojibake.garble("\uDC80b"));
        assertThrows(NullPointerException.class, () -> TextMeasure.measure(null));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("mojibake")
    void repairVectors(MojibakeCase c) {
        assertEquals(new Mojibake.Repair(c.expected(), c.rounds()), Mojibake.repair(c.text()));
    }

    @Test
    void garbleReproducesTheVectors() {
        List<MojibakeCase> once = mojibake().filter(c -> c.note().endsWith("garbled 1x")).toList();
        assertEquals(12, once.size());
        once.forEach(c -> assertEquals(c.text(), Mojibake.garble(c.expected())));
    }

    @Test
    void windows1252Table() {
        assertEquals('€', Mojibake.decodeByte(0x80));
        assertEquals('\u0081', Mojibake.decodeByte(0x81));
        assertEquals('Ÿ', Mojibake.decodeByte(0x9F));
        assertEquals('é', Mojibake.decodeByte(0xE9));
    }

    @Test
    void roundLimitAndBadArguments() {
        String twice = Mojibake.garble(Mojibake.garble("José"));
        assertEquals(Mojibake.garble("José"), Mojibake.repair(twice, 1).text());
        assertEquals(0, Mojibake.repair(twice, 0).rounds());
        assertThrows(IllegalArgumentException.class, () -> Mojibake.repair("x", -1));
        assertThrows(IllegalArgumentException.class, () -> Mojibake.repair("x", 11));
        assertEquals(Optional.empty(), Mojibake.unwindOnce("山"));
        assertEquals(Optional.empty(), Mojibake.unwindOnce("é"));
        assertEquals(Optional.of("é"), Mojibake.unwindOnce("Ã©"));
    }

    /** Run the CLI and capture stdout, stderr and the exit code. */
    private static String[] cli(String... args) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        int code = App.run(args, new PrintStream(out, true, StandardCharsets.UTF_8),
                new PrintStream(err, true, StandardCharsets.UTF_8));
        return new String[] {String.valueOf(code), out.toString(StandardCharsets.UTF_8), err.toString(StandardCharsets.UTF_8)};
    }

    @Test
    void commandLine() {
        String[] samples = cli("samples");
        assertEquals("0", samples[0]);
        assertTrue(samples[1].contains("family-zwj\t25\t11\t7\t1\t11"));
        String[] repair = cli("repair", "JosÃ©");
        assertTrue(repair[1].contains("José\t(rounds undone: 1)"));
        String[] report = cli("report");
        assertTrue(report[1].contains("java\tnormalization\tNormalizer NFC\t19074\t19074"));
        assertEquals("1", cli("measure", "a\uD800")[0]);
        assertEquals("2", cli("frobnicate")[0]);
        assertEquals("2", cli()[0]);
        assertEquals("2", cli("measure")[0]);
        String[] missing = cli("--vectors", "does-not-exist", "samples");
        assertEquals("1", missing[0]);
        assertTrue(missing[2].contains("not found"));
    }
}
