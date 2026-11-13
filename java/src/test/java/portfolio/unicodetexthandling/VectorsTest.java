package portfolio.unicodetexthandling;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import portfolio.unicodetexthandling.Vectors.VectorException;

/** Shared vector loaders: the files parse, and malformed input fails with a clear error. */
class VectorsTest {
    static final Path DIR = Vectors.defaultDir();

    @TempDir
    Path tmp;

    @Test
    void sharedFilesLoadWithExpectedSizes() {
        assertEquals(19074, Vectors.normalization(DIR).size());
        assertEquals(602, Vectors.grapheme(DIR).size());
        assertEquals(9004, Vectors.collation(DIR).size());
        assertEquals(55, Vectors.mojibake(DIR).size());
        assertEquals(15, Vectors.encoding(DIR).size());
    }

    @Test
    void baselinesAreRead() {
        assertEquals(Map.of("codepoint_exact", 250, "utf16_exact", 220), Vectors.baselines(DIR.resolve("grapheme.txt")));
    }

    @Test
    void unhex() {
        assertEquals("", Vectors.unhex("", 1));
        assertEquals("A😀", Vectors.unhex("0041 1F600", 1));
        assertThrows(VectorException.class, () -> Vectors.unhex("XYZ", 1));
        assertThrows(VectorException.class, () -> Vectors.unhex("110000", 1));
    }

    @Test
    void missingFileIsReported() {
        VectorException e = assertThrows(VectorException.class, () -> Vectors.grapheme(tmp));
        assertTrue(e.getMessage().contains("not found"));
    }

    @Test
    void emptyAndMalformedFilesAreRejected() throws IOException {
        Files.writeString(tmp.resolve("grapheme.txt"), "# comment only\n", StandardCharsets.UTF_8);
        assertThrows(VectorException.class, () -> Vectors.grapheme(tmp));
        Files.writeString(tmp.resolve("normalization.txt"), "0041;0041;0041\n", StandardCharsets.UTF_8);
        assertThrows(VectorException.class, () -> Vectors.normalization(tmp));
        Files.writeString(tmp.resolve("mojibake.tsv"), "0041\t0041\tx\tnote\n", StandardCharsets.UTF_8);
        assertThrows(VectorException.class, () -> Vectors.mojibake(tmp));
        Files.writeString(tmp.resolve("encoding.tsv"), "x\t0041\t1\t1\t1\tz\n", StandardCharsets.UTF_8);
        assertThrows(VectorException.class, () -> Vectors.encoding(tmp));
        Files.writeString(tmp.resolve("collation.txt"), "0041\n", StandardCharsets.UTF_8);
        assertThrows(VectorException.class, () -> Vectors.collation(tmp));
    }

    @Test
    void oversizedFileIsRejected() throws IOException {
        Files.write(tmp.resolve("collation.txt"), new byte[(int) Vectors.MAX_FILE_BYTES + 1]);
        VectorException e = assertThrows(VectorException.class, () -> Vectors.collation(tmp));
        assertTrue(e.getMessage().contains("too large"));
    }

    @Test
    void deviationsApplyFromTheirUnicodeVersion() {
        assertEquals(Set.of("2701 200D 2701"), Vectors.expectedDeviations(DIR, "js", "grapheme", "Intl.Segmenter", "17.0"));
        assertEquals(Set.of(), Vectors.expectedDeviations(DIR, "js", "grapheme", "Intl.Segmenter", "16.0"));
        assertEquals(Set.of("namaste"), Vectors.expectedDeviations(DIR, "java", "encoding", "BreakIterator", "15.1"));
        assertEquals(Set.of(), Vectors.expectedDeviations(DIR, "java", "encoding", "BreakIterator", "15.0"));
        assertThrows(VectorException.class, () -> Vectors.versionOf("fifteen"));
    }

    @Test
    void runtimeUnicodeVersionIsKnown() {
        assertTrue(Vectors.compareVersions(Vectors.versionOf(Vectors.runtimeUnicode()), new int[] {15, 0}) >= 0);
    }
}
