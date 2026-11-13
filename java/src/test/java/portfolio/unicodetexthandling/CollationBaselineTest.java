package portfolio.unicodetexthandling;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.text.Collator;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.junit.jupiter.api.Test;

/** CollationTest_NON_IGNORABLE_SHORT sample: how far the JDK's orderings are from the UCA. */
class CollationBaselineTest {
    static final List<String> ORDER = Vectors.collation(VectorsTest.DIR);
    static final Map<String, Integer> BASE = Vectors.baselines(VectorsTest.DIR.resolve("collation.txt"));

    @Test
    void utf16OrderMatchesTheRecordedBaseline() {
        assertEquals(BASE.get("utf16_in_order"), Conformance.inOrderPairs(ORDER, String::compareTo));
    }

    @Test
    void codePointOrderMatchesTheRecordedBaseline() {
        assertEquals(BASE.get("codepoint_in_order"), Conformance.inOrderPairs(ORDER, Conformance::compareCodePoints));
    }

    @Test
    void codePointAndUtf16OrderDifferAboveTheBmp() {
        String supplementary = "😀"; // U+1F600
        String privateUse = "";
        assertTrue(supplementary.compareTo(privateUse) < 0);
        assertTrue(Conformance.compareCodePoints(supplementary, privateUse) > 0);
    }

    @Test
    void rootCollatorIsCloserToTheUcaThanBinaryOrder() {
        int collator = Conformance.inOrderPairs(ORDER, Collator.getInstance(Locale.ROOT));
        assertTrue(collator > BASE.get("utf16_in_order"), "Collator ROOT in order: " + collator);
        assertTrue(collator < ORDER.size() - 1, "the JDK root collator is not the DUCET");
    }

    @Test
    void inOrderPairsCountsEachAdjacentPair() {
        assertEquals(2, Conformance.inOrderPairs(List.of("a", "b", "c"), String::compareTo));
        assertEquals(0, Conformance.inOrderPairs(List.of("c", "b", "a"), String::compareTo));
        assertEquals(1, Conformance.inOrderPairs(List.of("a", "a"), String::compareTo));
        assertEquals(0, Conformance.inOrderPairs(List.of("a"), String::compareTo));
    }

    @Test
    void binarySortPutsCaseAndAccentsWhereReadersDoNotExpect() {
        List<String> words = new ArrayList<>(List.of("zebra", "Zoo", "éclair", "apple"));
        words.sort(String::compareTo);
        assertEquals(List.of("Zoo", "apple", "zebra", "éclair"), words);
        words.sort(Collator.getInstance(Locale.ROOT));
        assertEquals(List.of("apple", "éclair", "zebra", "Zoo"), words);
    }
}
