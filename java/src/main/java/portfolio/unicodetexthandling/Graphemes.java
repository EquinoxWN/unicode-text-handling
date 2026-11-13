package portfolio.unicodetexthandling;

import java.text.BreakIterator;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Grapheme cluster segmentation with the JDK's own APIs, plus the naive splits for comparison. */
public final class Graphemes {
    /** Longest input accepted, in UTF-16 units. */
    public static final int MAX_LENGTH = 2_000_000;

    private static final Pattern CLUSTER = Pattern.compile("\\X");

    private Graphemes() {}

    /** Validate the input. */
    static String check(String text) {
        Objects.requireNonNull(text, "text");
        if (text.length() > MAX_LENGTH) {
            throw new IllegalArgumentException("text longer than " + MAX_LENGTH + " UTF-16 units");
        }
        return text;
    }

    /** Clusters from java.text.BreakIterator.getCharacterInstance(). */
    public static List<String> breakIterator(String text) {
        check(text);
        BreakIterator it = BreakIterator.getCharacterInstance();
        it.setText(text);
        List<String> out = new ArrayList<>();
        int start = it.first();
        for (int end = it.next(); end != BreakIterator.DONE; start = end, end = it.next()) {
            out.add(text.substring(start, end));
        }
        return out;
    }

    /** Clusters from the regex \X construct. */
    public static List<String> regex(String text) {
        check(text);
        List<String> out = new ArrayList<>();
        Matcher m = CLUSTER.matcher(text);
        while (m.find()) {
            out.add(m.group());
        }
        return out;
    }

    /** Naive split: one code point per character. */
    public static List<String> codePoints(String text) {
        check(text);
        return text.codePoints().mapToObj(Character::toString).toList();
    }

    /** Naive split: one UTF-16 unit (Java char) per character. */
    public static List<String> chars(String text) {
        check(text);
        return text.chars().mapToObj(c -> String.valueOf((char) c)).toList();
    }
}
